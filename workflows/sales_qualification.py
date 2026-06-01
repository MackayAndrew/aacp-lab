"""AACP Lab v3 - Sales Qualification Workflow. 5 hops per lead."""
import csv
import time
from .base_workflow import WorkflowResult, validate_packet, print_send, print_receive


def run(sales_agent, audit_agent, period="2026-03", model="gpt-4.1-mini"):
    res   = WorkflowResult("sales_qualification", period, model)
    leads = list(csv.DictReader(open(f"data/leads_{period}.csv")))
    results = []
    print(f"\n  Processing {len(leads)} leads...")

    for lead in leads:
        lead_id = lead["id"]
        print(f"\n  --- Lead {lead_id}: {lead['company']} ---")

        def hop(from_a, agent, packet, data=None, preview_fn=None):
            v = validate_packet(packet)
            print_send(from_a, agent.name, packet, v)
            r = agent.receive(packet, data)
            preview = preview_fn(r["result"]) if preview_fn and r["result"] else ""
            print_receive(agent.name, r, preview)
            res.add_hop(from_a, agent.name, packet, v, r)
            time.sleep(0.2)
            return r

        r1 = hop("ORCHESTRATOR", sales_agent,
                 f"FETCH|SALES|return:ORCHESTRATOR|p:1|aacp:1.1|res:lead_profile|filter:id={lead_id}|fmt:json",
                 {"lead": lead}, lambda x: str(x.get("lead", {}).get("company", "")))
        if r1["error"]: continue

        r2 = hop("ORCHESTRATOR", sales_agent,
                 f"CALC|SALES|return:ORCHESTRATOR|p:1|aacp:1.1|res:lead_score|filter:id={lead_id}|rules:bant",
                 {"lead": r1["result"], "lead_id": lead_id},
                 lambda x: f"Score {x.get('total_score',0)}/100 - {'QUALIFIED' if x.get('qualified') else 'NOT QUALIFIED'}")
        if r2["error"]: continue

        r3 = hop("ORCHESTRATOR", sales_agent,
                 f"PROC|SALES|return:ORCHESTRATOR|p:2|aacp:1.1|res:lead_routing|filter:id={lead_id}|validate:score>=60",
                 {"score_result": r2["result"], "lead_id": lead_id},
                 lambda x: f"Stage: {x.get('stage','?')} Rep: {x.get('routed_to','?')}")

        hop("ORCHESTRATOR", audit_agent,
            f"LOG|SALES|return:AUDIT-AGENT|p:3|aacp:1.1|actor:ORCHESTRATOR|status:processed",
            {"lead_id": lead_id, "workflow": "sales_qualification"},
            lambda x: "Logged")

        hop("ORCHESTRATOR", sales_agent,
            f"SEND|SALES|return:ORCHESTRATOR|p:1|aacp:1.1|subj:qualified_lead_{lead_id}|highlight:ACTION_REQUIRED",
            {"lead_id": lead_id, "routing": r3.get("result")},
            lambda x: f"Notified {x.get('to','rep')}")

        results.append({
            "lead_id":   lead_id,
            "company":   lead["company"],
            "score":     r2["result"].get("total_score") if r2["result"] else None,
            "qualified": r2["result"].get("qualified") if r2["result"] else None,
            "stage":     r3["result"].get("stage") if r3.get("result") else None,
            "rep":       r3["result"].get("routed_to") if r3.get("result") else None,
        })

    res.output = {
        "leads_processed": len(leads),
        "results": results,
        "qualified": sum(1 for r in results if r.get("qualified")),
    }
    return res.to_dict()
