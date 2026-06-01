# AACP Lab v3 — Multi-Workflow Department Lab

Real agents. Real CSV data. 5 workflows. 6 domains. Formatted Excel output.
All coordination via AACP v1.1 packets.

## Workflows

| Workflow | Domain | Hops | Data file |
|---|---|---|---|
| Payroll | HR + FIN | 5 | employees, budgets, payroll_rules |
| Month-End Close | FIN | 6 | budgets |
| Sales Qualification | SALES | 5 per lead | leads |
| CS Resolution | CS | 5 per ticket | tickets |
| JML Onboarding | HR + IT | 6 per hire | new_hires |

## Setup

```bash
pip3 install anthropic openai openpyxl
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
```

## Run

```bash
# All workflows, cheapest model first
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
  lab_v3_MODEL_TIMESTAMP.json   full results
  lab_v3_PERIOD_TIMESTAMP.xlsx  6-sheet Excel report
  comparison_TIMESTAMP.json     multi-model comparison
  audit.jsonl                   every AACP packet logged
```

## Cost estimate per full run

| Model | Estimated cost |
|---|---|
| gpt-4.1-mini | ~$0.015 |
| gpt-4.1 | ~$0.075 |
| claude-sonnet-4-5 | ~$0.120 |
| gpt-4o | ~$0.150 |
