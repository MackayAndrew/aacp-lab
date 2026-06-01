# AACP Lab v3 — Multi-Workflow Department Lab

Real agents. Real CSV data. 5 workflows. 6 domains.
All coordination via AACP v1.1 packets. Formatted Excel output.

## What it proves

AACP v1.1 packets are correctly interpreted by all four major
LLM models across five different business workflow types without
model-specific prompt tuning.

## Validated comparison — Q1 FY2026

| Model | Cost | Tokens in | Latency | All workflows pass |
|---|---|---|---|---|
| gpt-4.1-mini | $0.0190 | 40,585 | 160s | ✓ |
| gpt-4.1 | $0.0984 | 41,005 | 124s | ✓ |
| claude-sonnet-4-5 | $0.2237 | 53,127 | 423s | ✓ |
| gpt-4o | $0.2408 | 40,459 | 101s | ✓ |

Total hops per model: 76. All packets validated against AACP v1.1 schema.
Audit agent deterministic at $0.00 on every run.

## Model selection guide (evidence-based)

| Workflow | Recommended | Reason |
|---|---|---|
| JML Onboarding | gpt-4.1-mini | Deterministic tasks, any model works. $0.0033 for 3 hires |
| Sales Qualification | gpt-4.1 | Best scoring judgment on borderline leads |
| CS Resolution | gpt-4.1 | Best goodwill decisions by LTV, conservative where appropriate |
| Month-End Close | gpt-4.1 | Caught 3 material variances — gpt-4o only caught 1 |
| Payroll | gpt-4.1 | Reliable anomaly detection across runs |

**gpt-4.1 is the best all-round model for structured enterprise workflows.**
Full 5-workflow department day costs $0.0984 (~10p). 

## Workflows

| Workflow | Domain | Hops | Data file | Real-world basis |
|---|---|---|---|---|
| Payroll | HR + FIN | 5 | employees, budgets, payroll_rules | HMRC PAYE |
| Month-End Close | FIN | 6 | budgets | NetSuite Autonomous Close |
| Sales Qualification | SALES | 5 per lead | leads | Salesforce Agentforce |
| CS Resolution | CS | 5 per ticket | tickets | Zendesk Resolution Platform |
| JML Onboarding | HR + IT | 6 per hire | new_hires | ConductorOne, Lumos |

## Setup

```bash
pip3 install anthropic openai openpyxl
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
```

## Run

```bash
# All workflows, cheapest model first (recommended)
python3 run.py

# Single workflow
python3 run.py --workflow payroll
python3 run.py --workflow sales
python3 run.py --workflow cs
python3 run.py --workflow jml
python3 run.py --workflow month-end

# Specific model
python3 run.py --model gpt-4.1

# Full 4-model comparison
python3 run.py --compare
```

## Output

```
output/
  lab_v3_MODEL_TIMESTAMP.json     full structured results per model
  lab_v3_PERIOD_TIMESTAMP.xlsx    6-sheet Excel report
    Sheet 1: Summary              all workflows, costs, success
    Sheet 2: Payroll              employee pay, anomalies, CC status
    Sheet 3: Sales Pipeline       lead scores, qualification, routing
    Sheet 4: CS Resolution        ticket outcomes, goodwill decisions
    Sheet 5: JML Onboarding       new hire provisioning status
    Sheet 6: Month-End Close      reconciliation, variances, accounts
  comparison_TIMESTAMP.json       multi-model comparison table
  audit.jsonl                     every AACP packet, every agent call
```

## Structure

```
agents/
  base_agent.py     multi-provider API, cost tracking, audit logging
  hr_agent.py       HR + payroll domain
  finance_agent.py  FIN domain — budgets, GL, reconciliation
  sales_agent.py    SALES domain — lead qualification
  cs_agent.py       CS domain — complaint resolution
  it_agent.py       IT domain — JML provisioning
  audit_agent.py    deterministic, no LLM, $0.00

workflows/
  base_workflow.py  shared utilities, packet validation, printing
  payroll.py        5-hop payroll run
  month_end.py      6-hop month-end close
  sales_qualification.py  5-hop per lead
  cs_resolution.py  5-hop per ticket
  jml_onboarding.py 6-hop per new hire

data/
  employees_2026-03.csv    8 employees, Q1 FY2026
  budgets_2026-03.csv      4 cost centres
  payroll_rules.json       PAYE rate, thresholds, pay date
  leads_2026-03.csv        5 sales leads, BANT data
  tickets_2026-03.csv      5 CS tickets, LTV and sentiment
  new_hires_2026-03.csv    3 new hires, roles and systems
```

## Links

- Protocol spec: https://aacp.dev
- Python SDK: https://github.com/MackayAndrew/aacp — pip install aacp
- TypeScript SDK: https://github.com/MackayAndrew/aacp-ts — npm install aacp-ts
- IETF Draft: https://datatracker.ietf.org/doc/draft-mackay-aacp/
- VS Code Extension: https://marketplace.visualstudio.com/items?itemName=dispatch-aacp.dispatch-aacp
