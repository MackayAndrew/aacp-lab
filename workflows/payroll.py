"""AACP Lab v3 — Payroll Workflow (5 hops)"""
import csv, json, time
from pathlib import Path
from .base_workflow import WorkflowResult, validate_packet, print_send, print_receive


def run(hr_agent, finance_agent, audit_agent, period="2026-03", model="gpt-4.1-mini"):
    res = WorkflowResult("payroll", period, model)
    emp_data = list(csv.DictReader(open(f"data/employees_{period}.csv")))
    bud_data = list(csv.DictReader(open(f"data/budgets_{period}.csv")))
    rules    = json.load(open("data/payroll_rules.json"))

    def hop(from_a, agent, packet, data=None, preview_fn=None):
        v = validate_packet(packet)
        print_send(from_a, agent.name, packet, v)
        r = agent.receive(packet, data)
        preview = preview_fn(r["result"]) if preview_fn and r["result"] else ""
        print_receive(agent.name, r, preview)
        res.add_hop(from_a, agent.name, packet, v, r)
        time.sleep(0.3)
        return r

    p1 = f"FETCH|HR|return:ORCHESTRATOR|p:1|aacp:1.1|res:emp_salary|period:{period}|filter:status=active|fmt:json"
    r1 = hop("ORCHESTRATOR", hr_agent, p1,
              {"employees": emp_data, "period": period},
              lambda x: f"{x.get('total_employees',0)} employees, gross £{x.get('total_gross',0):,}")
    if r1["error"]: return res.to_dict()

    p2 = f"FETCH|FIN|return:ORCHESTRATOR|p:1|aacp:1.1|res:budget_cc|period:{period}|fmt:json"
    r2 = hop("ORCHESTRATOR", finance_agent, p2,
              {"budgets": bud_data, "period": period},
              lambda x: f"{x.get('flagged_count',0)} CCs pre-flagged")
    if r2["error"]: return res.to_dict()

    p3 = "MERGE|HR|return:ORCHESTRATOR|p:1|aacp:1.1|rules:payroll_v2|validate:budget_cc"
    r3 = hop("ORCHESTRATOR", hr_agent, p3,
              {"employees": r1["result"], "budgets": r2["result"], "payroll_rules": rules},
              lambda x: f"£{x.get('totals',{}).get('gross',0):,} gross | {len(x.get('anomalies',[]))} anomalies")
    if r3["error"]: return res.to_dict()

    p4 = "REPORT|HR|return:ORCHESTRATOR|p:2|aacp:1.1|fmt:pdf,xlsx|highlight:REVIEW_REQ"
    r4 = hop("ORCHESTRATOR", hr_agent, p4,
              {"payroll_summary": r3["result"], "period": period, "rules": rules},
              lambda x: x.get("executive_summary","")[:70])

    p5 = f"LOG|HR|return:AUDIT-AGENT|p:2|aacp:1.1|actor:ORCHESTRATOR|status:review_required"
    kf = r4["result"].get("key_figures", {}) if r4["result"] else {}
    hop("ORCHESTRATOR", audit_agent, p5, {
        "period": period, "workflow": "payroll",
        "employee_count": kf.get("employee_count"),
        "total_gross_gbp": kf.get("total_gross_gbp"),
        "anomaly_count": kf.get("anomaly_count", 0),
    }, lambda x: "Audit record written")

    res.output = {
        "employees": r1["result"],
        "budgets":   r2["result"],
        "payroll":   r3["result"],
        "report":    r4["result"],
    }
    return res.to_dict()
