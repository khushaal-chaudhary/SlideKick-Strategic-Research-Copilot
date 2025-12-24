"""
Strategic Research Copilot - Knowledge Graph Schema

This module defines a standardized schema based on schema.org with
financial extensions. Using a standardized schema provides:

1. Interoperability - Data can be shared/merged with other systems
2. LLM Extraction - Schema.org is in LLM training data, making extraction easier
3. Documentation - Well-defined types with clear semantics
4. Portfolio Value - Demonstrates understanding of ontology design

Schema.org Types Used:
- Organization (Corporation) - Companies like Microsoft
- Person - CEOs, executives
- Product - Products and services
- MonetaryAmount - Financial metrics (from FIBO extension)
- CreativeWork (Report) - Shareholder letters, reports
- Event - Announcements, launches
- Thing - Generic fallback

Custom Extensions (prefixed with 'x:'):
- x:Strategy - Strategic initiatives
- x:Risk - Business risks
- x:Technology - Technologies mentioned
- x:Metric - Business metrics beyond monetary

References:
- https://schema.org/Organization
- https://schema.org/MonetaryAmount  
- https://www.w3.org/community/fibo/ (FIBO schema.org extension)
"""

from enum import Enum
from typing import Any


# =============================================================================
# Node Types (Schema.org Aligned)
# =============================================================================

class NodeType(str, Enum):
    """
    Knowledge graph node types aligned with schema.org.
    
    Uses schema.org types where available, with custom extensions
    prefixed with 'x:' for domain-specific concepts.
    """
    
    # --- Schema.org Core Types ---
    ORGANIZATION = "Organization"      # schema.org/Organization (corporations, companies)
    PERSON = "Person"                  # schema.org/Person (executives, founders)
    PRODUCT = "Product"                # schema.org/Product (products, services)
    EVENT = "Event"                    # schema.org/Event (announcements, launches)
    PLACE = "Place"                    # schema.org/Place (locations, regions)
    CREATIVE_WORK = "CreativeWork"     # schema.org/CreativeWork (reports, documents)
    
    # --- Schema.org Financial Types (from FIBO extension) ---
    MONETARY_AMOUNT = "MonetaryAmount"          # schema.org/MonetaryAmount
    FINANCIAL_PRODUCT = "FinancialProduct"      # schema.org/FinancialProduct
    
    # --- Custom Extensions (Domain-Specific) ---
    STRATEGY = "x:Strategy"            # Strategic initiatives, plans
    RISK = "x:Risk"                    # Business risks, threats
    TECHNOLOGY = "x:Technology"        # Technologies, platforms
    METRIC = "x:Metric"                # Non-monetary metrics (users, growth %)
    INITIATIVE = "x:Initiative"        # Programs, campaigns
    SECTOR = "x:Sector"                # Industry sectors, markets
    
    # --- Fallback ---
    THING = "Thing"                    # schema.org/Thing (generic)


# =============================================================================
# Relationship Types (Schema.org Aligned)
# =============================================================================

class RelationType(str, Enum):
    """
    Knowledge graph relationship types.
    
    Uses schema.org properties where available, with domain-specific
    extensions for strategic analysis.
    """
    
    # --- Schema.org Properties ---
    MEMBER_OF = "memberOf"             # Person → Organization
    FOUNDER = "founder"                # Organization → Person
    CEO = "ceo"                        # Organization → Person (custom but clear)
    PARENT_ORGANIZATION = "parentOrganization"  # Organization → Organization
    SUB_ORGANIZATION = "subOrganization"        # Organization → Organization
    OWNS = "owns"                      # Organization → Organization/Product
    PRODUCES = "produces"              # Organization → Product
    SPONSOR = "sponsor"                # Organization → Event
    LOCATION = "location"              # Thing → Place
    ABOUT = "about"                    # CreativeWork → Thing
    MENTIONS = "mentions"              # CreativeWork → Thing
    
    # --- Financial Relationships ---
    HAS_REVENUE = "hasRevenue"         # Organization → MonetaryAmount
    HAS_INVESTMENT = "hasInvestment"   # Organization → MonetaryAmount
    FUNDS = "funds"                    # Organization → Initiative
    
    # --- Strategic Relationships ---
    LAUNCHED = "launched"              # Organization → Product/Initiative
    ANNOUNCED = "announced"            # Organization → Event/Strategy
    FOCUSES_ON = "focusesOn"           # Organization → Strategy/Technology
    COMPETES_WITH = "competesWith"     # Organization → Organization
    PARTNERS_WITH = "partnersWith"     # Organization → Organization
    ACQUIRED = "acquired"              # Organization → Organization
    
    # --- Risk/Metric Relationships ---
    FACES_RISK = "facesRisk"           # Organization → Risk
    MITIGATES = "mitigates"            # Strategy → Risk
    MEASURED_BY = "measuredBy"         # Strategy/Product → Metric
    INCREASED = "increased"            # Thing → Metric (with temporal context)
    DECREASED = "decreased"            # Thing → Metric (with temporal context)
    
    # --- Technology Relationships ---
    USES = "uses"                      # Organization/Product → Technology
    BUILT_ON = "builtOn"               # Product → Technology
    ENABLES = "enables"                # Technology → Strategy/Product
    
    # --- Generic ---
    RELATED_TO = "relatedTo"           # Thing → Thing (fallback)


# =============================================================================
# Schema Definitions with Properties
# =============================================================================

SCHEMA_DEFINITIONS = {
    NodeType.ORGANIZATION: {
        "schema_url": "https://schema.org/Organization",
        "description": "An organization such as a corporation, company, or institution",
        "properties": {
            "name": "Official name",
            "legalName": "Legal registered name",
            "ticker": "Stock ticker symbol",
            "description": "Brief description",
            "foundingDate": "When founded (ISO date)",
            "numberOfEmployees": "Employee count",
            "url": "Official website",
        },
        "examples": ["Microsoft", "OpenAI", "Anthropic"],
    },
    
    NodeType.PERSON: {
        "schema_url": "https://schema.org/Person",
        "description": "A person, such as an executive or founder",
        "properties": {
            "name": "Full name",
            "jobTitle": "Current title/role",
            "worksFor": "Organization they work for",
        },
        "examples": ["Satya Nadella", "Sam Altman"],
    },
    
    NodeType.PRODUCT: {
        "schema_url": "https://schema.org/Product",
        "description": "A product or service",
        "properties": {
            "name": "Product name",
            "description": "What it does",
            "category": "Product category",
            "datePublished": "Launch date",
        },
        "examples": ["Azure", "Microsoft 365", "Copilot", "Xbox"],
    },
    
    NodeType.MONETARY_AMOUNT: {
        "schema_url": "https://schema.org/MonetaryAmount",
        "description": "A monetary value with currency",
        "properties": {
            "value": "Numeric value",
            "currency": "Currency code (USD, EUR)",
            "name": "What this amount represents",
            "period": "Time period (Q3 2024, FY2024)",
        },
        "examples": ["$211 billion revenue", "$35 billion investment"],
    },
    
    NodeType.STRATEGY: {
        "schema_url": None,  # Custom extension
        "description": "A strategic initiative or business strategy",
        "properties": {
            "name": "Strategy name",
            "description": "What the strategy aims to achieve",
            "status": "Current status (active, planned, completed)",
            "priority": "Priority level",
        },
        "examples": ["AI-First Strategy", "Cloud Expansion", "Sustainability Initiative"],
    },
    
    NodeType.RISK: {
        "schema_url": None,  # Custom extension
        "description": "A business risk or threat",
        "properties": {
            "name": "Risk name",
            "description": "Nature of the risk",
            "severity": "Risk severity (high, medium, low)",
            "category": "Risk category (regulatory, competitive, operational)",
        },
        "examples": ["Cybersecurity Threats", "Regulatory Compliance", "Market Competition"],
    },
    
    NodeType.TECHNOLOGY: {
        "schema_url": None,  # Custom extension
        "description": "A technology, platform, or technical capability",
        "properties": {
            "name": "Technology name",
            "description": "What it is",
            "category": "Category (AI, Cloud, Security, etc.)",
        },
        "examples": ["GPT-4", "Azure AI", "Kubernetes", "Quantum Computing"],
    },
    
    NodeType.METRIC: {
        "schema_url": None,  # Custom extension
        "description": "A non-monetary business metric",
        "properties": {
            "name": "Metric name",
            "value": "Metric value",
            "unit": "Unit of measurement",
            "period": "Time period",
            "changePercent": "Percentage change",
        },
        "examples": ["300 million Teams users", "40% YoY growth", "500+ enterprise customers"],
    },
    
    NodeType.EVENT: {
        "schema_url": "https://schema.org/Event",
        "description": "An announcement, launch, or business event",
        "properties": {
            "name": "Event name",
            "description": "What happened",
            "startDate": "When it occurred",
            "eventType": "Type (announcement, launch, acquisition)",
        },
        "examples": ["Copilot Launch", "Activision Acquisition", "Build 2024"],
    },
}


# =============================================================================
# LLM Extraction Prompt Template
# =============================================================================

def get_extraction_prompt() -> str:
    """
    Generate a prompt for LLM-based entity/relationship extraction.
    
    This prompt is designed to:
    1. Use schema.org terminology that LLMs understand well
    2. Provide clear examples
    3. Ensure consistent output format
    """
    
    node_types = "\n".join([
        f"  - {t.value}: {SCHEMA_DEFINITIONS.get(t, {}).get('description', 'No description')}"
        for t in NodeType
    ])
    
    rel_types = ", ".join([r.value for r in RelationType])
    
    return f"""You are extracting structured knowledge from text using schema.org-aligned types.

## Node Types (use these exactly):
{node_types}

## Relationship Types:
{rel_types}

## Output Format (JSON):
{{
    "nodes": [
        {{
            "id": "unique_identifier",
            "type": "Organization|Person|Product|...",
            "properties": {{
                "name": "Display name",
                "description": "Brief description",
                ...other relevant properties...
            }}
        }}
    ],
    "relationships": [
        {{
            "source": "source_node_id",
            "target": "target_node_id",
            "type": "launched|focusesOn|...",
            "properties": {{
                ...optional properties like date, context...
            }}
        }}
    ]
}}

## Guidelines:
1. Use the most specific type available (Organization over Thing)
2. Include properties that are explicitly mentioned in the text
3. Create relationships only when clearly stated or strongly implied
4. Use consistent IDs (lowercase, underscores: "microsoft", "satya_nadella")
5. For MonetaryAmount, always include value and currency
6. For Metrics, include the unit and time period if available

## Example Extraction:

Text: "Microsoft CEO Satya Nadella announced that Azure revenue grew 29% to $25.9 billion in Q3 2024."

Output:
{{
    "nodes": [
        {{"id": "microsoft", "type": "Organization", "properties": {{"name": "Microsoft"}}}},
        {{"id": "satya_nadella", "type": "Person", "properties": {{"name": "Satya Nadella", "jobTitle": "CEO"}}}},
        {{"id": "azure", "type": "Product", "properties": {{"name": "Azure", "category": "Cloud"}}}},
        {{"id": "azure_revenue_q3_2024", "type": "MonetaryAmount", "properties": {{"name": "Azure Revenue", "value": 25.9, "currency": "USD", "unit": "billion", "period": "Q3 2024"}}}},
        {{"id": "azure_growth_q3_2024", "type": "x:Metric", "properties": {{"name": "Azure Growth", "value": 29, "unit": "percent", "period": "Q3 2024"}}}}
    ],
    "relationships": [
        {{"source": "satya_nadella", "target": "microsoft", "type": "ceo"}},
        {{"source": "microsoft", "target": "azure", "type": "produces"}},
        {{"source": "azure", "target": "azure_revenue_q3_2024", "type": "hasRevenue"}},
        {{"source": "azure", "target": "azure_growth_q3_2024", "type": "increased"}}
    ]
}}

Now extract from the following text:
"""


# =============================================================================
# Cypher Schema for Neo4j
# =============================================================================

def get_neo4j_schema() -> str:
    """
    Generate Cypher statements to create schema constraints in Neo4j.
    
    This ensures:
    1. Unique node IDs
    2. Proper indexing for fast queries
    """
    
    constraints = []
    
    for node_type in NodeType:
        type_name = node_type.value.replace("x:", "")  # Remove extension prefix for Neo4j
        constraints.append(
            f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{type_name}) REQUIRE n.id IS UNIQUE;"
        )
    
    # Add indexes for common query patterns
    indexes = [
        "CREATE INDEX IF NOT EXISTS FOR (n:Organization) ON (n.name);",
        "CREATE INDEX IF NOT EXISTS FOR (n:Person) ON (n.name);",
        "CREATE INDEX IF NOT EXISTS FOR (n:Product) ON (n.name);",
        "CREATE INDEX IF NOT EXISTS FOR (n:MonetaryAmount) ON (n.period);",
    ]
    
    return "\n".join(constraints + indexes)


# =============================================================================
# Mapping Your Current Schema to Schema.org
# =============================================================================

MIGRATION_MAP = {
    # Your current types → Schema.org aligned types
    "Company": NodeType.ORGANIZATION,
    "Person": NodeType.PERSON,
    "Product": NodeType.PRODUCT,
    "Strategy": NodeType.STRATEGY,
    "FinancialMetric": NodeType.MONETARY_AMOUNT,  # or x:Metric for non-monetary
    "Risk": NodeType.RISK,
    "Technology": NodeType.TECHNOLOGY,
    
    # Your current relationships → Schema.org aligned
    "LAUNCHED": RelationType.LAUNCHED,
    "INCREASED": RelationType.INCREASED,
    "DECREASED": RelationType.DECREASED,
    "ANNOUNCED": RelationType.ANNOUNCED,
    "FOCUSES_ON": RelationType.FOCUSES_ON,
    "COMPETES_WITH": RelationType.COMPETES_WITH,
    "MENTIONS": RelationType.MENTIONS,
}


def migrate_node_type(old_type: str) -> NodeType:
    """Convert old schema type to new schema.org-aligned type."""
    return MIGRATION_MAP.get(old_type, NodeType.THING)


def migrate_relationship_type(old_type: str) -> RelationType:
    """Convert old relationship type to new schema.org-aligned type."""
    return MIGRATION_MAP.get(old_type, RelationType.RELATED_TO)
