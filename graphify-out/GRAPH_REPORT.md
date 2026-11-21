# Graph Report - INWESTWATCH  (2026-11-21)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 12 nodes · 9 edges · 4 communities (1 shown, 3 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 382 input · 38 output

## Graph Freshness
- Built from commit: `2b073229`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- InvestWatch Platform Architecture
- Development Documentation and Skills
- Investment Competition Regulations
- InvestWatch Challenge Description

## God Nodes (most connected - your core abstractions)
1. `InvestWatch System` - 7 edges
2. `InvestWatch Competition Regulations` - 2 edges
3. `Analytical / AI Modules` - 1 edges
4. `Web Dashboard` - 1 edges
5. `Module 1: External Ecosystem Monitoring` - 1 edges
6. `Module 2: Compliance and Risk Verification` - 1 edges
7. `Module 3: Unauthorized Services Identification` - 1 edges
8. `Backend & Scraping Engine` - 1 edges
9. `graphify skill` - 1 edges
10. `Urząd Komisji Nadzoru Finansowego (UKNF)` - 1 edges

## Surprising Connections (you probably didn't know these)
- `InvestWatch Competition Regulations` --references--> `InvestWatch System`  [EXTRACTED]
  DocsTaskINWESTWATCH/UKNF - Regulamin Zadania Konkursowego.pdf → DocsTaskINWESTWATCH/Opis Wyzwania HackNation UKNF 19.11.pdf

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **InvestWatch Analytical Modules** — investwatch_module_1, investwatch_module_2, investwatch_module_3 [EXTRACTED 1.00]
- **InvestWatch MVP Architecture** — investwatch_scraping_engine, investwatch_ai_modules, investwatch_dashboard [EXTRACTED 1.00]

## Communities (4 total, 3 thin omitted)

### Community 0 - "InvestWatch Platform Architecture"
Cohesion: 0.29
Nodes (7): Analytical / AI Modules, Web Dashboard, Module 1: External Ecosystem Monitoring, Module 2: Compliance and Risk Verification, Module 3: Unauthorized Services Identification, Backend & Scraping Engine, InvestWatch System

## Knowledge Gaps
- **9 isolated node(s):** `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring`, `Module 2: Compliance and Risk Verification`, `Module 3: Unauthorized Services Identification` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 10 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `InvestWatch System` connect `InvestWatch Platform Architecture` to `Investment Competition Regulations`?**
  _High betweenness centrality (0.491) - this node is a cross-community bridge._
- **What connects `Analytical / AI Modules`, `Web Dashboard`, `Module 1: External Ecosystem Monitoring` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Why does `InvestWatch Competition Regulations` connect `Investment Competition Regulations` to `InvestWatch Platform Architecture`?**
  _High betweenness centrality (0.127) - this node is a cross-community bridge._