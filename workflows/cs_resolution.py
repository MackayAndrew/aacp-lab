"""AACP Lab v3 - Customer Service Resolution Workflow. 5 hops per ticket."""
import csv
import time
from .base_workflow import WorkflowResult, validate_packet, print_send, print_receive


def run(cs_agent, audit_agent, period="2026-03", model="gpt-4.1-mini"):
    res     = WorkflowResult("cs_resolution", period, model)
    tickets = list(csv.DictReader(open(f"data/tickets_{period}.csv")))
    results = []
    print(f"\n  Processing {len(tickets)} tickets...")

    for ticket in tickets:
        ticket_id   = ticket["id"]
        customer_id = ticket["customer_id"]
        print(f"\n  --- Ticket {ticket_id}: {ticket['subject'][:50]} ---")

        def hop(from_a, agent, packet, data=None, preview_fn=None):
            v = validate_packet(packet)
            print_send(from_a, agent.name, packet, v)
            r = agent.receive(packet, data)
            preview = preview_fn(r["result"]) if preview_fn and r["result"] else ""
            print_receive(agent.name, r, preview)
            res.add_hop(from_a, agent.name, packet, v, r)
            time.sleep(0.2)
            return r

        r1 = hop("ORCHESTRATOR", cs_agent,
                 f"FETCH|CS|return:ORCHESTRATOR|p:1|aacp:1.1|res:customer_profile|filter:id={customer_id}|fields:history,ltv,loyalty,open_tickets,sentiment|fmt:json",
                 {"ticket": ticket, "customer_id": customer_id},
                 lambda x: f"LTV £{x.get('ltv_gbp',0):,} loyalty {x.get('loyalty_years',0)}y")
        if r1["error"]: continue

        r2 = hop("ORCHESTRATOR", cs_agent,
                 f"PROC|CS|return:ORCHESTRATOR|p:1|aacp:1.1|res:ticket_triage|filter:id={ticket_id}|req:categorise,sentiment_score,priority_score",
                 {"ticket": ticket, "customer_profile": r1["result"]},
                 lambda x: f"Category: {x.get('category','?')} Escalate: {x.get('escalate',False)}")
        if r2["error"]: continue
        if not r2["result"]: continue

        ltv       = int(ticket.get("ltv_gbp", 0) or 0)
        sentiment = ticket.get("sentiment", "negative")
        goodwill  = ltv > 5000
        r3 = hop("ORCHESTRATOR", cs_agent,
                 f"RESOLVE|CS|return:ORCHESTRATOR|p:1|aacp:1.1|res:complaint|filter:id={ticket_id}|sentiment:{sentiment}|tone:empathetic|ltv:{ltv}|ccy:GBP|req:resolve{'%2cgoodwill_consider' if goodwill else ''}",
                 {"ticket": ticket, "triage": r2["result"], "customer": r1["result"]},
                 lambda x: f"Strategy: {x.get('resolution_strategy','?')[:50]}")

        r4 = hop("ORCHESTRATOR", cs_agent,
                 f"SEND|CS|return:ORCHESTRATOR|p:1|aacp:1.1|to:{customer_id}|subj:resolution_{ticket_id}|tone:empathetic|flag_msg:resolution_sent",
                 {"ticket_id": ticket_id, "resolution": r3.get("result")},
                 lambda x: "Response sent")

        hop("ORCHESTRATOR", audit_agent,
            f"LOG|CS|return:AUDIT-AGENT|p:3|aacp:1.1|actor:ORCHESTRATOR|status:resolved",
            {"ticket_id": ticket_id, "customer_id": customer_id, "workflow": "cs_resolution"},
            lambda x: "Logged")

        results.append({
            "ticket_id":         ticket_id,
            "customer_id":       customer_id,
            "subject":           ticket["subject"],
            "ltv_gbp":           ltv,
            "category":          r2["result"].get("category") if r2["result"] else None,
            "resolution_strategy": r3["result"].get("resolution_strategy") if r3.get("result") else None,
            "goodwill_offer":    r3["result"].get("goodwill_offer") if r3.get("result") else None,
            "goodwill_amount":   r3["result"].get("goodwill_amount_gbp") if r3.get("result") else None,
            "escalate":          r2["result"].get("escalate") if r2["result"] else None,
            "sent":              r4["result"].get("sent") if r4.get("result") else None,
        })

    res.output = {
        "tickets_processed": len(tickets),
        "results": results,
        "resolved": sum(1 for r in results if r.get("sent")),
        "goodwill_offered": sum(1 for r in results if r.get("goodwill_offer")),
    }
    return res.to_dict()
