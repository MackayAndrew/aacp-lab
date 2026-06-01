"""AACP Lab v3 - Finance Month-End Close Workflow. 6 hops."""
import time
from .base_workflow import WorkflowResult, validate_packet, print_send, print_receive


def run(finance_agent, audit_agent, period="2026-03", prev_period="2026-02", model="gpt-4.1-mini"):
    res = WorkflowResult("month_end_close", period, model)

    def hop(from_a, agent, packet, data=None, preview_fn=None):
        v = validate_packet(packet)
        print_send(from_a, agent.name, packet, v)
        r = agent.receive(packet, data)
        preview = preview_fn(r["result"]) if preview_fn and r["result"] else ""
        print_receive(agent.name, r, preview)
        res.add_hop(from_a, agent.name, packet, v, r)
        time.sleep(0.3)
        return r

    r1 = hop("ORCHESTRATOR", finance_agent,
             f"FETCH|FIN|return:ORCHESTRATOR|p:1|aacp:1.1|res:trial_balance|period:{period}|fmt:json",
             {"period": period},
             lambda x: f"GL entries: {x.get('gl_entries','?')} Balanced: {x.get('balanced','?')}")
    if r1["error"]: return res.to_dict()

    r2 = hop("ORCHESTRATOR", finance_agent,
             f"PROC|FIN|return:ORCHESTRATOR|p:1|aacp:1.1|res:bank_reconciliation|period:{period}|rules:recon_v1|validate:gl_match",
             {"trial_balance": r1["result"], "period": period},
             lambda x: f"Reconciled: {x.get('reconciled','?')} Unmatched: {x.get('unmatched_items',0)} items")
    if r2["error"]: return res.to_dict()

    r3 = hop("ORCHESTRATOR", finance_agent,
             f"CALC|FIN|return:ORCHESTRATOR|p:1|aacp:1.1|res:accruals|period:{period}|rules:accrual_policy_v2|validate:period_cutoff",
             {"trial_balance": r1["result"], "period": period},
             lambda x: f"Posted {x.get('accruals_posted',0)} accruals £{x.get('total_value_gbp',0):,}")

    r4 = hop("ORCHESTRATOR", finance_agent,
             f"CALC|FIN|return:ORCHESTRATOR|p:2|aacp:1.1|res:variance_analysis|period:{period}|src_prev:gl://close/{prev_period}|highlight:MATERIAL_VARIANCE",
             {"period": period, "prev_period": prev_period, "accruals": r3.get("result")},
             lambda x: f"Material variances: {x.get('material_variances',0)}")

    r5 = hop("ORCHESTRATOR", finance_agent,
             f"REPORT|FIN|return:ORCHESTRATOR|p:2|aacp:1.1|period:{period}|fmt:pdf,xlsx|tmpl:mgmt_accounts_v1|highlight:REVIEW_REQ",
             {"variance_analysis": r4.get("result"), "reconciliation": r2.get("result"), "period": period},
             lambda x: x.get("executive_summary","")[:70])

    hop("ORCHESTRATOR", audit_agent,
        f"LOG|FIN|return:AUDIT-AGENT|p:2|aacp:1.1|res:close_certification|period:{period}|actor:ORCHESTRATOR|status:certified",
        {"period": period, "workflow": "month_end_close"},
        lambda x: "Close certification logged")

    res.output = {
        "trial_balance":    r1.get("result"),
        "reconciliation":   r2.get("result"),
        "accruals":         r3.get("result"),
        "variance_analysis": r4.get("result"),
        "management_accounts": r5.get("result"),
    }
    return res.to_dict()
