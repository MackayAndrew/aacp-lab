"""AACP Lab v3 - JML Onboarding Workflow. 6 hops per new hire."""
import csv
import time
from .base_workflow import WorkflowResult, validate_packet, print_send, print_receive


def run(hr_agent, it_agent, audit_agent, period="2026-03", model="gpt-4.1-mini"):
    res       = WorkflowResult("jml_onboarding", period, model)
    new_hires = list(csv.DictReader(open(f"data/new_hires_{period}.csv")))
    results   = []
    print(f"\n  Onboarding {len(new_hires)} new hires...")

    for hire in new_hires:
        emp_id   = hire["employee_id"]
        username = hire["username"]
        print(f"\n  --- New hire {emp_id}: {hire['name']} ({hire['role']}) ---")

        def hop(from_a, agent, packet, data=None, preview_fn=None):
            v = validate_packet(packet)
            print_send(from_a, agent.name, packet, v)
            r = agent.receive(packet, data)
            preview = preview_fn(r["result"]) if preview_fn and r["result"] else ""
            print_receive(agent.name, r, preview)
            res.add_hop(from_a, agent.name, packet, v, r)
            time.sleep(0.2)
            return r

        r1 = hop("ORCHESTRATOR", hr_agent,
                 f"FETCH|HR|return:ORCHESTRATOR|p:1|aacp:1.1|res:employee_record|filter:id={emp_id}|fmt:json",
                 {"employee": hire},
                 lambda x: f"{x.get('employee',{}).get('name','?')} - {x.get('employee',{}).get('role','?')}")
        if r1["error"]: continue

        licences = hire.get("licences", "M365,Slack").split(",")
        systems  = hire.get("systems",  "email,vpn").split(",")

        r2 = hop("ORCHESTRATOR", it_agent,
                 f"BUILD|IT|return:ORCHESTRATOR|p:1|aacp:1.1|res:ad_account|filter:usr={username}|fields:email,dept,grp,pwd_reset",
                 {"employee": hire, "username": username},
                 lambda x: f"Account created: {x.get('email','?')}")
        if r2["error"]: continue

        r3 = hop("ORCHESTRATOR", it_agent,
                 f"PROC|IT|return:ORCHESTRATOR|p:1|aacp:1.1|res:licence_assignment|filter:usr={username}|req:{','.join(licences)}",
                 {"username": username, "licences": licences},
                 lambda x: f"Licences: {x.get('licences_assigned',[])}")

        r4 = hop("ORCHESTRATOR", it_agent,
                 f"BUILD|IT|return:ORCHESTRATOR|p:1|aacp:1.1|res:access_profile|filter:usr={username}|req:{','.join(systems)}",
                 {"username": username, "systems": systems},
                 lambda x: f"Systems: {x.get('systems_granted',[])}")

        r5 = hop("ORCHESTRATOR", it_agent,
                 f"SEND|HR|return:ORCHESTRATOR|p:2|aacp:1.1|to:{username}|subj:welcome_{username}_onboarding|flag_msg:onboarding_complete",
                 {"username": username, "employee": hire, "account": r2.get("result")},
                 lambda x: f"Welcome email sent to {username}")

        hop("ORCHESTRATOR", audit_agent,
            f"LOG|IT|return:AUDIT-AGENT|p:2|aacp:1.1|actor:ORCHESTRATOR|status:provisioned|filter:usr={username}",
            {"username": username, "emp_id": emp_id, "workflow": "jml_onboarding"},
            lambda x: "Provisioning logged")

        results.append({
            "employee_id": emp_id,
            "name":        hire["name"],
            "username":    username,
            "dept":        hire["dept"],
            "role":        hire["role"],
            "email":       r2["result"].get("email") if r2.get("result") else None,
            "licences":    r3["result"].get("licences_assigned") if r3.get("result") else None,
            "systems":     r4["result"].get("systems_granted") if r4.get("result") else None,
            "welcome_sent": r5["result"].get("sent") if r5.get("result") else None,
        })

    res.output = {
        "hires_processed": len(new_hires),
        "results": results,
        "provisioned": sum(1 for r in results if r.get("welcome_sent")),
    }
    return res.to_dict()
