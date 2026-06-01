"""
AACP Lab v3 - Multi-Workflow Department Lab
Runs 5 workflow types across HR, Finance, Sales, CS, IT domains.
All coordination via AACP v1.1 packets.

Usage:
  python3 run.py                          # all workflows, gpt-4.1-mini
  python3 run.py --workflow payroll
  python3 run.py --workflow sales
  python3 run.py --workflow cs
  python3 run.py --workflow jml
  python3 run.py --workflow month-end
  python3 run.py --model gpt-4.1
  python3 run.py --compare                # all models, cheapest first

Requirements:
  pip3 install anthropic openai openpyxl
  export ANTHROPIC_API_KEY=...
  export OPENAI_API_KEY=...
"""

import sys, os, json, time, argparse
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.base_agent   import MODEL_REGISTRY
from agents.hr_agent     import HRAgent
from agents.finance_agent import FinanceAgent
from agents.sales_agent  import SalesAgent
from agents.cs_agent     import CSAgent
from agents.it_agent     import ITAgent
from agents.audit_agent  import AuditAgent

from workflows import payroll, sales_qualification, cs_resolution, jml_onboarding, month_end
from report_writer import write_report

MODEL_ORDER = ["gpt-4.1-mini", "gpt-4.1", "claude-sonnet-4-5", "gpt-4o"]
PERIOD      = "2026-03"
PREV_PERIOD = "2026-02"


def check_keys(model):
    provider = MODEL_REGISTRY.get(model, {}).get("provider", "openai")
    if provider == "anthropic" and not os.environ.get("ANTHROPIC_API_KEY"):
        print(f"ERROR: ANTHROPIC_API_KEY not set"); return False
    if provider == "openai"    and not os.environ.get("OPENAI_API_KEY"):
        print(f"ERROR: OPENAI_API_KEY not set"); return False
    return True


def run_all_workflows(model: str, period: str = PERIOD) -> dict:
    if not check_keys(model): return {}

    print(f"\n{'='*65}")
    print(f"  AACP LAB v3 — ALL WORKFLOWS")
    print(f"  Model: {model} | Period: {period}")
    print(f"{'='*65}")

    Path("output").mkdir(exist_ok=True)
    Path("output/audit.jsonl").unlink(missing_ok=True)

    hr      = HRAgent(model)
    finance = FinanceAgent(model)
    sales   = SalesAgent(model)
    cs      = CSAgent(model)
    it      = ITAgent(model)
    audit   = AuditAgent()

    results = {}
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # Run all 5 workflows
    print(f"\n{'─'*65}")
    print(f"  WORKFLOW 1/5 — Payroll")
    print(f"{'─'*65}")
    results["payroll"] = payroll.run(hr, finance, audit, period, model)

    print(f"\n{'─'*65}")
    print(f"  WORKFLOW 2/5 — Month-End Close")
    print(f"{'─'*65}")
    results["month_end"] = month_end.run(finance, audit, period, PREV_PERIOD, model)

    print(f"\n{'─'*65}")
    print(f"  WORKFLOW 3/5 — Sales Qualification")
    print(f"{'─'*65}")
    results["sales"] = sales_qualification.run(sales, audit, period, model)

    print(f"\n{'─'*65}")
    print(f"  WORKFLOW 4/5 — CS Resolution")
    print(f"{'─'*65}")
    results["cs"] = cs_resolution.run(cs, audit, period, model)

    print(f"\n{'─'*65}")
    print(f"  WORKFLOW 5/5 — JML Onboarding")
    print(f"{'─'*65}")
    results["jml"] = jml_onboarding.run(hr, it, audit, period, model)

    # Totals
    total_cost    = sum(r.get("totals",{}).get("cost_usd",0)    for r in results.values())
    total_tokens  = sum(r.get("totals",{}).get("tokens_in",0)   for r in results.values())
    total_latency = sum(r.get("totals",{}).get("latency_ms",0)  for r in results.values())
    total_hops    = sum(r.get("totals",{}).get("hops",0)        for r in results.values())

    summary = {
        "run_id":    f"lab_v3_{model.replace('/','_')}_{ts}",
        "model":     model,
        "period":    period,
        "completed": datetime.now(timezone.utc).isoformat(),
        "workflows": results,
        "totals": {
            "workflows":    len(results),
            "hops":         total_hops,
            "tokens_in":    total_tokens,
            "cost_usd":     round(total_cost, 4),
            "latency_ms":   round(total_latency, 0),
        },
    }

    # Save JSON
    json_path = f"output/lab_v3_{model.replace('/','_')}_{ts}.json"
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Write Excel
    xlsx_path = write_report(results, model, period, ts)

    print(f"\n{'='*65}")
    print(f"  SUMMARY — {model}")
    print(f"{'='*65}")
    print(f"  Workflows:    {len(results)}")
    print(f"  Total hops:   {total_hops}")
    print(f"  Total tokens: {total_tokens:,}")
    print(f"  Total cost:   ${total_cost:.4f}")
    print(f"  Total time:   {total_latency/1000:.1f}s")
    print(f"  JSON:         {json_path}")
    if xlsx_path:
        print(f"  Excel:        {xlsx_path}")

    return summary


def run_single_workflow(workflow: str, model: str, period: str = PERIOD):
    if not check_keys(model): return

    Path("output").mkdir(exist_ok=True)
    hr      = HRAgent(model)
    finance = FinanceAgent(model)
    sales   = SalesAgent(model)
    cs      = CSAgent(model)
    it      = ITAgent(model)
    audit   = AuditAgent()

    wf_map = {
        "payroll":   lambda: payroll.run(hr, finance, audit, period, model),
        "month-end": lambda: month_end.run(finance, audit, period, PREV_PERIOD, model),
        "sales":     lambda: sales_qualification.run(sales, audit, period, model),
        "cs":        lambda: cs_resolution.run(cs, audit, period, model),
        "jml":       lambda: jml_onboarding.run(hr, it, audit, period, model),
    }

    if workflow not in wf_map:
        print(f"Unknown workflow: {workflow}. Choose from: {', '.join(wf_map.keys())}")
        return

    print(f"\n{'='*65}")
    print(f"  AACP LAB v3 — {workflow.upper()}")
    print(f"  Model: {model} | Period: {period}")
    print(f"{'='*65}")

    result = wf_map[workflow]()
    t = result.get("totals", {})
    print(f"\n  Hops: {t.get('hops',0)} | "
          f"Tokens: {t.get('tokens_in',0):,} | "
          f"Cost: ${t.get('cost_usd',0):.4f} | "
          f"Time: {t.get('latency_ms',0)/1000:.1f}s")


def run_comparison(period: str = PERIOD):
    print(f"\n{'='*65}")
    print(f"  AACP LAB v3 — MULTI-MODEL COMPARISON")
    print(f"  Running cheapest model first")
    print(f"{'='*65}")

    summaries = []
    for model in MODEL_ORDER:
        provider = MODEL_REGISTRY.get(model, {}).get("provider", "openai")
        has_key  = (
            (provider == "openai"    and os.environ.get("OPENAI_API_KEY")) or
            (provider == "anthropic" and os.environ.get("ANTHROPIC_API_KEY"))
        )
        if not has_key:
            print(f"\n  Skipping {model} — API key not set")
            continue

        s = run_all_workflows(model, period)
        if s:
            summaries.append(s)
        time.sleep(2)

    if not summaries:
        return

    print(f"\n{'='*65}")
    print(f"  COMPARISON — {period}")
    print(f"{'='*65}")
    print(f"  {'Model':<22} {'Cost':>10} {'Tokens':>10} {'Time':>8}")
    print(f"  {'─'*52}")
    for s in summaries:
        t = s["totals"]
        print(f"  {s['model']:<22} ${t['cost_usd']:>9.4f} "
              f"{t['tokens_in']:>10,} {t['latency_ms']/1000:>6.1f}s")

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    comp_path = f"output/comparison_{ts}.json"
    with open(comp_path, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "period": period,
            "models": [s["model"] for s in summaries],
            "results": [{
                "model":      s["model"],
                "cost_usd":   s["totals"]["cost_usd"],
                "tokens_in":  s["totals"]["tokens_in"],
                "latency_ms": s["totals"]["latency_ms"],
            } for s in summaries],
        }, f, indent=2)
    print(f"\n  Saved: {comp_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AACP Lab v3")
    parser.add_argument("--model",    default="gpt-4.1-mini",
        choices=MODEL_ORDER)
    parser.add_argument("--workflow", default=None,
        choices=["payroll", "month-end", "sales", "cs", "jml"])
    parser.add_argument("--period",   default=PERIOD)
    parser.add_argument("--compare",  action="store_true")
    args = parser.parse_args()

    if args.compare:
        run_comparison(period=args.period)
    elif args.workflow:
        run_single_workflow(args.workflow, args.model, args.period)
    else:
        run_all_workflows(args.model, args.period)
