# Knowledge Graph Schema Design

## Overview

This document describes the schema design for the Strategic Research Copilot knowledge graph. The schema is **aligned with schema.org** with custom extensions for strategic analysis.

## Why Schema.org?

| Consideration | Our Choice |
|--------------|------------|
| **Interoperability** | ✅ schema.org is the web standard |
| **LLM Extraction** | ✅ LLMs trained on schema.org data |
| **Complexity** | ✅ Simpler than FIBO (~20 types vs 2,457) |
| **Financial Support** | ✅ FIBO terms already in schema.org |
| **Portfolio Value** | ✅ Demonstrates industry awareness |

### Alternatives Considered

1. **FIBO (Financial Industry Business Ontology)**
   - ✅ Industry standard for finance
   - ❌ 2,457 classes - overkill for shareholder letters
   - ❌ Hard to prompt LLMs to extract
   - Decision: Use FIBO concepts already merged into schema.org

2. **Custom Schema**
   - ✅ Perfectly tailored
   - ❌ Not interoperable
   - ❌ Harder to explain in interviews
   - Decision: Extend schema.org instead

## Schema Overview

```
                    schema.org/Thing
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   Organization       Person            Product
   (Corporation)    (Executive)        (Service)
        │                                   │
        ├── x:Strategy                      │
        ├── x:Risk                          │
        └── x:Technology ───────────────────┘
                │
          MonetaryAmount
          (from FIBO ext)
```

## Node Types

### Schema.org Core Types

| Type | Schema URL | Description | Example |
|------|-----------|-------------|---------|
| `Organization` | schema.org/Organization | Companies, corporations | Microsoft, OpenAI |
| `Person` | schema.org/Person | Individuals | Satya Nadella |
| `Product` | schema.org/Product | Products/services | Azure, Copilot |
| `Event` | schema.org/Event | Announcements, launches | Build 2024 |
| `Place` | schema.org/Place | Locations | Seattle, China |
| `CreativeWork` | schema.org/CreativeWork | Documents, reports | FY2024 Annual Report |

### Schema.org Financial Types (FIBO Extension)

| Type | Schema URL | Description | Example |
|------|-----------|-------------|---------|
| `MonetaryAmount` | schema.org/MonetaryAmount | Money values | $211B revenue |
| `FinancialProduct` | schema.org/FinancialProduct | Financial instruments | Azure Credits |

### Custom Extensions (x: prefix)

| Type | Description | Example |
|------|-------------|---------|
| `x:Strategy` | Strategic initiatives | "AI-First Strategy" |
| `x:Risk` | Business risks | "Cybersecurity Threats" |
| `x:Technology` | Technical capabilities | "GPT-4", "Kubernetes" |
| `x:Metric` | Non-monetary metrics | "300M users", "40% growth" |
| `x:Initiative` | Programs, campaigns | "AI for Good" |
| `x:Sector` | Industry sectors | "Cloud Computing" |

## Relationship Types

### Schema.org Properties

```
Person ──[ceo]──────────────> Organization
Person ──[founder]──────────> Organization
Person ──[memberOf]─────────> Organization

Organization ──[parentOrganization]──> Organization
Organization ──[subOrganization]─────> Organization
Organization ──[produces]────────────> Product
Organization ──[owns]────────────────> Organization

CreativeWork ──[about]───────> Thing
CreativeWork ──[mentions]────> Thing
```

### Strategic Relationships

```
Organization ──[focusesOn]────> Strategy | Technology
Organization ──[launched]─────> Product | Initiative
Organization ──[announced]────> Event | Strategy
Organization ──[competesWith]─> Organization
Organization ──[partnersWith]─> Organization
Organization ──[acquired]─────> Organization
```

### Financial Relationships

```
Organization ──[hasRevenue]─────> MonetaryAmount
Organization ──[hasInvestment]──> MonetaryAmount
Organization ──[funds]──────────> Initiative
```

### Risk Relationships

```
Organization ──[facesRisk]────> Risk
Strategy ─────[mitigates]─────> Risk
```

### Metric Relationships

```
Product ──[measuredBy]──> Metric
Thing ────[increased]───> Metric
Thing ────[decreased]───> Metric
```

## Example: Microsoft Shareholder Letter Extraction

### Input Text
```
Microsoft CEO Satya Nadella announced that Azure revenue grew 29% to $25.9 billion 
in Q3 2024. The company's AI-first strategy is driving growth, with Copilot now 
integrated into Microsoft 365. Microsoft faces cybersecurity risks but is 
investing $35 billion in security infrastructure.
```

### Extracted Graph

```json
{
  "nodes": [
    {"id": "microsoft", "type": "Organization", "properties": {"name": "Microsoft"}},
    {"id": "satya_nadella", "type": "Person", "properties": {"name": "Satya Nadella", "jobTitle": "CEO"}},
    {"id": "azure", "type": "Product", "properties": {"name": "Azure", "category": "Cloud"}},
    {"id": "azure_revenue_q3_2024", "type": "MonetaryAmount", "properties": {"value": 25.9, "currency": "USD", "unit": "billion", "period": "Q3 2024"}},
    {"id": "azure_growth", "type": "x:Metric", "properties": {"value": 29, "unit": "percent", "period": "Q3 2024"}},
    {"id": "ai_first_strategy", "type": "x:Strategy", "properties": {"name": "AI-First Strategy"}},
    {"id": "copilot", "type": "Product", "properties": {"name": "Copilot"}},
    {"id": "microsoft_365", "type": "Product", "properties": {"name": "Microsoft 365"}},
    {"id": "cybersecurity_risk", "type": "x:Risk", "properties": {"name": "Cybersecurity Risks"}},
    {"id": "security_investment", "type": "MonetaryAmount", "properties": {"value": 35, "currency": "USD", "unit": "billion"}}
  ],
  "relationships": [
    {"source": "satya_nadella", "target": "microsoft", "type": "ceo"},
    {"source": "microsoft", "target": "azure", "type": "produces"},
    {"source": "azure", "target": "azure_revenue_q3_2024", "type": "hasRevenue"},
    {"source": "azure", "target": "azure_growth", "type": "increased"},
    {"source": "microsoft", "target": "ai_first_strategy", "type": "focusesOn"},
    {"source": "microsoft", "target": "copilot", "type": "launched"},
    {"source": "copilot", "target": "microsoft_365", "type": "partOf"},
    {"source": "microsoft", "target": "cybersecurity_risk", "type": "facesRisk"},
    {"source": "microsoft", "target": "security_investment", "type": "hasInvestment"}
  ]
}
```

### Visualization

```
                    ┌─────────────┐
                    │  Microsoft  │
                    │(Organization)│
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
           │               │               │
      [ceo]│        [produces]      [focusesOn]
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌─────────┐    ┌────────────┐
    │  Satya   │    │  Azure  │    │ AI-First   │
    │ Nadella  │    │(Product)│    │ Strategy   │
    │ (Person) │    └────┬────┘    └────────────┘
    └──────────┘         │
                   [hasRevenue]
                         │
                         ▼
                  ┌────────────┐
                  │ $25.9B Q3  │
                  │(Monetary   │
                  │ Amount)    │
                  └────────────┘
```

## Migration from Current Schema

If you already have data in the old schema, use this mapping:

| Old Type | New Type |
|----------|----------|
| Company | Organization |
| Person | Person |
| Product | Product |
| Strategy | x:Strategy |
| FinancialMetric | MonetaryAmount or x:Metric |
| Risk | x:Risk |
| Technology | x:Technology |

| Old Relationship | New Relationship |
|-----------------|------------------|
| LAUNCHED | launched |
| INCREASED | increased |
| DECREASED | decreased |
| ANNOUNCED | announced |
| FOCUSES_ON | focusesOn |
| COMPETES_WITH | competesWith |
| MENTIONS | mentions |

## Neo4j Implementation

### Create Constraints

```cypher
// Unique constraints
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Organization) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Product) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:MonetaryAmount) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Strategy) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Risk) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Technology) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Metric) REQUIRE n.id IS UNIQUE;

// Indexes for common queries
CREATE INDEX IF NOT EXISTS FOR (n:Organization) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:Person) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:Product) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:MonetaryAmount) ON (n.period);
```

### Example Queries

```cypher
// Find all products by Microsoft
MATCH (org:Organization {name: "Microsoft"})-[:produces]->(p:Product)
RETURN p.name, p.description

// Find revenue over time
MATCH (org:Organization {name: "Microsoft"})-[:hasRevenue]->(m:MonetaryAmount)
RETURN m.period, m.value, m.currency
ORDER BY m.period

// Find strategies and their risks
MATCH (org:Organization)-[:focusesOn]->(s:Strategy)
OPTIONAL MATCH (s)-[:mitigates]->(r:Risk)
RETURN s.name, collect(r.name) as mitigatedRisks
```

## Portfolio Talking Points

When discussing this in interviews:

1. **"I aligned the schema with schema.org for interoperability"**
   - Shows awareness of industry standards
   - Demonstrates thinking beyond just "making it work"

2. **"I evaluated FIBO but found schema.org sufficient"**
   - Shows you know about FIBO (financial industry standard)
   - Demonstrates pragmatic decision-making (not over-engineering)

3. **"The schema enables LLM extraction"**
   - Schema.org terms are in LLM training data
   - Makes entity extraction more reliable

4. **"Custom extensions follow naming conventions"**
   - x: prefix for domain-specific types
   - Consistent with how schema.org extensions work

## References

- [Schema.org](https://schema.org/)
- [Schema.org Organization](https://schema.org/Organization)
- [Schema.org MonetaryAmount](https://schema.org/MonetaryAmount)
- [FIBO](https://spec.edmcouncil.org/fibo/)
- [W3C FIBO Community Group](https://www.w3.org/community/fibo/)
- [FIBO schema.org extension](https://www.w3.org/community/fibo/)
