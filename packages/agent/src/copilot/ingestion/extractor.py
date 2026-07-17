"""LLM entity/relationship extraction for uploaded documents."""

import logging
import os
import time
from collections.abc import Callable

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from copilot.config.settings import settings
from copilot.ingestion.schema import ALLOWED_NODES, ALLOWED_RELATIONSHIPS, EXTRACTION_PROMPT

logger = logging.getLogger(__name__)

# gpt-oss-120b has its own Groq daily-token budget, separate from the
# llama-3.3-70b the agent runs on — uploads don't eat the agent's quota
BYOD_PROVIDER = os.environ.get("BYOD_LLM_PROVIDER", "groq")
BYOD_MODEL = os.environ.get(
    "BYOD_LLM_MODEL",
    "openai/gpt-oss-120b" if BYOD_PROVIDER == "groq" else "qwen2.5:7b",
)

RETRY_ATTEMPTS = 3


def get_extraction_llm():
    if BYOD_PROVIDER == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(model=BYOD_MODEL, temperature=0.0, base_url=settings.ollama_base_url)
    from langchain_groq import ChatGroq

    return ChatGroq(model=BYOD_MODEL, temperature=0.0, api_key=settings.groq_api_key_str)


def build_transformer():
    from langchain_experimental.graph_transformers import LLMGraphTransformer

    prompt = ChatPromptTemplate.from_messages([("user", EXTRACTION_PROMPT)]).partial(
        node_labels=", ".join(ALLOWED_NODES),
        rel_types=", ".join(ALLOWED_RELATIONSHIPS),
    )
    return LLMGraphTransformer(
        llm=get_extraction_llm(),
        allowed_nodes=ALLOWED_NODES,
        allowed_relationships=ALLOWED_RELATIONSHIPS,
        prompt=prompt,
        strict_mode=False,
    )


def extract_graph_documents(
    chunks: list[Document],
    on_progress: Callable[[int, int], None] | None = None,
) -> tuple[list, int]:
    """Extract graph documents chunk by chunk.

    Returns (graph_documents, skipped_count). Groq function-calling
    occasionally emits malformed JSON (tool_use_failed); each chunk is
    retried, then skipped so one flaky chunk doesn't fail the upload.
    """
    transformer = build_transformer()
    graph_documents = []
    skipped = 0

    for i, chunk in enumerate(chunks, 1):
        result = None
        for attempt in range(RETRY_ATTEMPTS):
            try:
                result = transformer.convert_to_graph_documents([chunk])
                break
            except Exception as e:
                logger.warning(
                    "extraction chunk %d attempt %d failed: %s", i, attempt + 1, str(e)[:200]
                )
                time.sleep(3 * (attempt + 1))
        if result is None:
            skipped += 1
        else:
            graph_documents.extend(result)
        if on_progress:
            on_progress(i, len(chunks))

    return graph_documents, skipped
