"""
Rebuild the demo knowledge graph + vector index from the shareholder letters.

Replays the ingestion originally done in notebooks/graph_ingestion_schemaorg.ipynb
and notebooks/vector_ingestion.ipynb as a single reproducible script, so the
corpus can be rebuilt from scratch (e.g. after the Aura free instance is
deleted for inactivity).

Usage:
    python scripts/ingest_corpus.py                 # graph + vectors
    python scripts/ingest_corpus.py --graph-only
    python scripts/ingest_corpus.py --vectors-only
    python scripts/ingest_corpus.py --clear         # wipe DB first

Requires: NEO4J_URI, NEO4J_PASSWORD, GROQ_API_KEY in .env, and a local
Ollama server with the nomic-embed-text model pulled (for embeddings).
"""

import argparse
import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

from copilot.ingestion.schema import (  # noqa: E402
    ALLOWED_NODES,
    ALLOWED_RELATIONSHIPS,
    EXTRACTION_PROMPT,
)
from langchain_community.document_loaders import DirectoryLoader, TextLoader  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
from langchain_neo4j import Neo4jGraph  # noqa: E402
from langchain_text_splitters import RecursiveCharacterTextSplitter  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("ingest")

DATA_DIR = REPO_ROOT / "data"

CONSTRAINTS = [
    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE"
    for label in [
        "Organization",
        "Person",
        "Product",
        "MonetaryAmount",
        "Strategy",
        "Risk",
        "Technology",
        "Metric",
        "Event",
        "Initiative",
    ]
]

INDEXES = [
    "CREATE INDEX IF NOT EXISTS FOR (n:Organization) ON (n.name)",
    "CREATE INDEX IF NOT EXISTS FOR (n:Person) ON (n.name)",
    "CREATE INDEX IF NOT EXISTS FOR (n:Product) ON (n.name)",
    "CREATE INDEX IF NOT EXISTS FOR (n:MonetaryAmount) ON (n.period)",
]


def connect() -> Neo4jGraph:
    graph = Neo4jGraph(
        url=os.environ["NEO4J_URI"],
        username=os.environ.get("NEO4J_USERNAME", "neo4j"),
        password=os.environ["NEO4J_PASSWORD"],
        database=os.environ.get("NEO4J_DATABASE") or "neo4j",
    )
    logger.info("Connected to Neo4j at %s", os.environ["NEO4J_URI"])
    return graph


def load_documents():
    loader = DirectoryLoader(
        str(DATA_DIR), glob="*.txt", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"}
    )
    raw_docs = loader.load()
    if not raw_docs:
        raise SystemExit(f"No .txt documents found in {DATA_DIR}")
    logger.info("Loaded %d documents from %s", len(raw_docs), DATA_DIR)
    return raw_docs


def ingest_graph(graph: Neo4jGraph, raw_docs, batch_size: int, sleep_s: float, start: int = 1):
    from langchain_experimental.graph_transformers import LLMGraphTransformer
    from langchain_groq import ChatGroq

    for cypher in CONSTRAINTS + INDEXES:
        try:
            graph.query(cypher)
        except Exception as e:
            logger.warning("schema statement failed: %s", e)
    logger.info("Schema constraints/indexes ensured")

    llm = ChatGroq(
        api_key=os.environ["GROQ_API_KEY"],
        model=os.environ.get("INGEST_LLM_MODEL", "llama-3.3-70b-versatile"),
        temperature=0,
    )

    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    documents = splitter.split_documents(raw_docs)
    logger.info("Split into %d extraction chunks", len(documents))

    prompt = ChatPromptTemplate.from_messages([("user", EXTRACTION_PROMPT)]).partial(
        node_labels=", ".join(ALLOWED_NODES),
        rel_types=", ".join(ALLOWED_RELATIONSHIPS),
    )
    transformer = LLMGraphTransformer(
        llm=llm,
        allowed_nodes=ALLOWED_NODES,
        allowed_relationships=ALLOWED_RELATIONSHIPS,
        prompt=prompt,
        strict_mode=False,
    )

    total_nodes = total_rels = skipped = 0
    for i, doc in enumerate(documents, 1):
        if i < start:
            continue
        graph_docs = None
        # Groq function-calling occasionally emits malformed JSON
        # (tool_use_failed); retry, then skip so one flaky chunk
        # doesn't kill the whole run
        for attempt in range(3):
            try:
                graph_docs = transformer.convert_to_graph_documents([doc])
                break
            except Exception as e:
                logger.warning("chunk %d attempt %d failed: %s", i, attempt + 1, str(e)[:200])
                time.sleep(5 * (attempt + 1))
        if graph_docs is None:
            skipped += 1
            continue
        graph.add_graph_documents(graph_docs)
        total_nodes += sum(len(d.nodes) for d in graph_docs)
        total_rels += sum(len(d.relationships) for d in graph_docs)
        if i % batch_size == 0 or i == len(documents):
            logger.info(
                "graph chunk %d/%d (totals: %d nodes, %d rels, %d skipped)",
                i,
                len(documents),
                total_nodes,
                total_rels,
                skipped,
            )
        if i < len(documents) and sleep_s:
            time.sleep(sleep_s)

    cleanup_off_schema(graph)
    graph.refresh_schema()
    logger.info("Graph ingestion complete: %d nodes, %d relationships", total_nodes, total_rels)


def cleanup_off_schema(graph: Neo4jGraph):
    """Remove the small amount of off-schema output the LLM emits despite the allowed lists."""
    # LLMGraphTransformer title-cases multi-word labels (MonetaryAmount -> Monetaryamount)
    graph.query("MATCH (n:Monetaryamount) SET n:MonetaryAmount REMOVE n:Monetaryamount")

    # namespace IS NULL guards keep BYOD workspace data untouched
    rel_rows = graph.query("MATCH ()-[r]->() RETURN DISTINCT type(r) AS t")
    for row in rel_rows:
        if row["t"] not in ALLOWED_RELATIONSHIPS:
            graph.query(
                f"MATCH (a)-[r:`{row['t']}`]->() WHERE a.namespace IS NULL DELETE r"
            )
            logger.info("Removed off-schema relationship type: %s", row["t"])

    keep = set(ALLOWED_NODES) | {"DocumentChunk", "UserChunk"}
    label_rows = graph.query("MATCH (n) UNWIND labels(n) AS l RETURN DISTINCT l")
    for row in label_rows:
        if row["l"] not in keep:
            graph.query(
                f"MATCH (n:`{row['l']}`) WHERE n.namespace IS NULL DETACH DELETE n"
            )
            logger.info("Removed off-schema node label: %s", row["l"])


def ingest_vectors(graph: Neo4jGraph, raw_docs, batch_size: int):
    from langchain_ollama import OllamaEmbeddings

    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    dims = len(embeddings.embed_query("dimension probe"))
    logger.info("Ollama embeddings ready (%d dimensions)", dims)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=100, separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = splitter.split_documents(raw_docs)
    logger.info("Split into %d vector chunks", len(chunks))

    graph.query(
        f"""
        CREATE VECTOR INDEX document_embeddings IF NOT EXISTS
        FOR (c:DocumentChunk)
        ON c.embedding
        OPTIONS {{
            indexConfig: {{
                `vector.dimensions`: {dims},
                `vector.similarity_function`: 'cosine'
            }}
        }}
        """
    )

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        vectors = embeddings.embed_documents([c.page_content for c in batch])
        for j, (chunk, vector) in enumerate(zip(batch, vectors)):
            source = Path(chunk.metadata.get("source", "unknown")).name
            graph.query(
                """
                MERGE (c:DocumentChunk {id: $chunk_id})
                SET c.text = $text, c.source = $source, c.embedding = $embedding
                """,
                params={
                    "chunk_id": f"chunk_{i + j}",
                    "text": chunk.page_content,
                    "source": source,
                    "embedding": vector,
                },
            )
        logger.info("vector batch %d-%d/%d done", i + 1, min(i + batch_size, len(chunks)), len(chunks))

    logger.info("Vector ingestion complete: %d chunks", len(chunks))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph-only", action="store_true")
    parser.add_argument("--vectors-only", action="store_true")
    parser.add_argument("--clear", action="store_true", help="Delete all nodes first")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--sleep", type=float, default=10.0, help="Seconds between extraction batches")
    parser.add_argument("--start", type=int, default=1, help="Resume graph extraction at this chunk (1-based)")
    args = parser.parse_args()

    graph = connect()

    if args.clear:
        confirm = input("This deletes ALL nodes in the database. Type 'yes' to continue: ")
        if confirm.strip().lower() != "yes":
            raise SystemExit("Aborted")
        graph.query("MATCH (n) DETACH DELETE n")
        logger.info("Database cleared")

    raw_docs = load_documents()

    if not args.vectors_only:
        ingest_graph(graph, raw_docs, args.batch_size, args.sleep, args.start)
    if not args.graph_only:
        ingest_vectors(graph, raw_docs, args.batch_size)

    counts = graph.query("MATCH (n) RETURN count(n) AS nodes")
    rels = graph.query("MATCH ()-[r]->() RETURN count(r) AS rels")
    logger.info("Final DB state: %s nodes, %s relationships", counts[0]["nodes"], rels[0]["rels"])


if __name__ == "__main__":
    main()
