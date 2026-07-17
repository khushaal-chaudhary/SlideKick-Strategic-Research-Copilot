"""
Schema.org-aligned extraction schema shared by the demo-corpus rebuild
script (scripts/ingest_corpus.py) and the BYOD ingestion pipeline.
"""

ALLOWED_NODES = [
    "Organization",
    "Person",
    "Product",
    "Event",
    "MonetaryAmount",
    "Strategy",
    "Risk",
    "Technology",
    "Metric",
    "Initiative",
    "Concept",
    "Program",
]

ALLOWED_RELATIONSHIPS = [
    "CEO",
    "FOUNDER",
    "PRODUCES",
    "ACQUIRED",
    "PARTNERS_WITH",
    "COMPETES_WITH",
    "HAS_REVENUE",
    "HAS_INVESTMENT",
    "COSTS",
    "FOCUSES_ON",
    "LAUNCHED",
    "ANNOUNCED",
    "USES",
    "FACES_RISK",
    "MITIGATES",
    "MEASURED_BY",
    "INCREASED",
    "DECREASED",
    "RELATED_TO",
    "MENTIONS",
    "PROTECTS",
    "SUPPORTS",
    "INVESTS_IN",
]

EXTRACTION_PROMPT = """
You are an expert knowledge graph builder extracting structured data from business documents.

Extract entities and relationships using this SCHEMA.ORG-ALIGNED schema:

## Node Types:
- **Organization**: Companies, corporations (Microsoft, OpenAI, Activision)
- **Person**: Executives, founders, key people (Satya Nadella, Brad Smith)
- **Product**: Products, services, platforms (Azure, Microsoft 365, Copilot, Xbox)
- **MonetaryAmount**: Financial values with currency ($211 billion revenue, $35B investment)
- **Strategy**: Strategic initiatives (AI-first strategy, Cloud expansion)
- **Risk**: Business risks and challenges (Cybersecurity threats, Regulatory compliance)
- **Technology**: Technologies, platforms (GPT-4, Machine Learning, Cloud Computing)
- **Metric**: Non-monetary metrics (300 million users, 29% growth, 32,000 nonprofits)
- **Event**: Announcements, launches, conferences (Build 2024, Ignite)
- **Initiative**: Programs, campaigns (AI for Good, Digital Skills)

## Relationship Types:
{rel_types}

## Guidelines:
1. Use the MOST SPECIFIC node type (Organization over generic)
2. For MonetaryAmount, extract the value, currency, and what it represents
3. For Metric, include the value, unit, and time period if mentioned
4. Create relationships ONLY when explicitly stated or strongly implied
5. Use consistent naming (e.g., "Microsoft" not "MSFT" or "microsoft")

## Examples:
- "Microsoft revenue was $211 billion" -> Organization(Microsoft) -[HAS_REVENUE]-> MonetaryAmount($211B)
- "Satya Nadella, CEO of Microsoft" -> Person(Satya Nadella) -[CEO]-> Organization(Microsoft)
- "Azure grew 29%" -> Product(Azure) -[INCREASED]-> Metric(29% growth)
- "investing in AI" -> Organization -[FOCUSES_ON]-> Technology(AI)

Node Labels: {node_labels}

Text to extract from:
{input}
"""
