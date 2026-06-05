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
| gpt-4.1-mini | $0.0190 | 40,585 | 160s | ✓ 5/5 |
| gpt-4.1 | $0.0984 | 41,005 | 124s | ✓ 5/5 |
| claude-sonnet-4-5 | $0.2237 | 53,127 | 423s | ✓ 5/5 |
| gpt-4o | $0.2408 | 40,459 | 101s | ✓ 5/5 |

Total hops per model: 76. All packets validated against AACP v1.1 schema.
Audit agent deterministic at $0.00 on every run.

## Model selection guide (evidence-based)

| Workflow | Recommended | Reason |
|---|---|---|
| JML Onboarding | gpt-4.1-mini | Deterministic tasks. $0.0033 for 3 hires |
| Sales Qualification | gpt-4.1 | Best scoring judgment on borderline leads |
| CS Resolution | gpt-4.1 | Best goodwill decisions by LTV |
| Month-End Close | gpt-4.1 | Caught 3 material variances — gpt-4o caught 1 |
| Payroll | gpt-4.1 | Reliable anomaly detection across runs |

**gpt-4.1 is the best all-round model for structured enterprise workflows.**
Full 5-workflow department day: $0.0984 (~10p).

## Workflows

| Workflow | Domain | Hops | Real-world basis |
|---|---|---|---|
| Payroll | HR + FIN | 5 | HMRC PAYE |
| Month-End Close | FIN | 6 | NetSuite Autonomous Close 2026 |
| Sales Qualification | SALES | 5 per lead | Salesforce Agentforce 2026 |
| CS Resolution | CS | 5 per ticket | Zendesk Resolution Platform 2026 |
| JML Onboarding | HR + IT | 6 per hire | ConductorOne, Lumos, CloudEagle |

## Setup

```bash
pip install anthropic openai openpyxl aacp
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
```

## Run

```bash
python3 run.py                    # all workflows, gpt-4.1-mini
python3 run.py --workflow payroll
python3 run.py --model gpt-4.1
python3 run.py --compare          # all 4 models
```

## Links

- Protocol: https://aacp.dev
- Python SDK: https://github.com/MackayAndrew/aacp
- TypeScript SDK: https://github.com/MackayAndrew/aacp-ts
- LangChain integration: https://github.com/MackayAndrew/aacp-langchain
- CrewAI integration: https://github.com/MackayAndrew/aacp-crewai
- IETF Draft: https://datatracker.ietf.org/doc/draft-mackay-aacp/
