"""
AACP Lab v3 — Base Workflow
Shared utilities for all workflow modules.
"""

import json, time
from datetime import datetime, timezone


VALID_TASKS = {"FETCH","PROC","FLAG","RESOLVE","LOG","SEND",
               "BUILD","MERGE","CALC","REPORT","ACK","SYNC"}
VALID_DOMS  = {"HR","FIN","SALES","LEGAL","IT","CS","MKT"}


def validate_packet(packet: str) -> dict:
    fields = [f.strip() for f in packet.strip().split("|")]
    errors, warnings = [], []
    if len(fields) < 3:
        return {"valid": False, "errors": ["Too few fields"], "warnings": []}
    if fields[0] not in VALID_TASKS: errors.append(f"Unknown TASK: {fields[0]}")
    if fields[1] not in VALID_DOMS:  errors.append(f"Unknown DOM: {fields[1]}")
    keys = {f.split(":",1)[0].lower(): f.split(":",1)[1]
            for f in fields[2:] if ":" in f}
    if "return" not in keys: errors.append("Missing return:")
    if "aacp"   not in keys: warnings.append("Missing aacp: version")
    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def print_send(from_a, to_agent, packet, validation):
    valid_str = "VALID" if validation["valid"] else "INVALID"
    print(f"\n  ┌─ [{from_a}] → [{to_agent}]")
    print(f"  │  {packet}")
    print(f"  │  Schema: {valid_str}", end="")
    if validation.get("warnings"):
        print(f" ⚠ {validation['warnings'][0]}", end="")
    print()


def print_receive(agent, r, preview=""):
    status = "✓" if r["error"] is None else "✗"
    if r["error"]:
        print(f"  └─ [{agent}] {status} ERROR: {r['error'][:80]}")
    else:
        cost_str = f"${r['cost_usd']:.4f}" if r["cost_usd"] > 0 else "$0.0000"
        print(f"  └─ [{agent}] {status} "
              f"{r['tokens_in']}in/{r['tokens_out']}out "
              f"{r['latency_ms']:.0f}ms {cost_str}")
        if preview:
            print(f"     ↳ {preview[:80]}")


class WorkflowResult:
    def __init__(self, workflow: str, period: str, model: str):
        self.workflow   = workflow
        self.period     = period
        self.model      = model
        self.hops       = []
        self.tokens_in  = 0
        self.tokens_out = 0
        self.cost_usd   = 0.0
        self.latency_ms = 0.0
        self.success    = True
        self.output     = {}
        self.started    = datetime.now(timezone.utc).isoformat()

    def add_hop(self, from_a, to_agent, packet, validation, r):
        self.hops.append({
            "from": from_a, "to": to_agent,
            "packet": packet, "validation": validation,
            "tokens_in": r["tokens_in"], "tokens_out": r["tokens_out"],
            "cost_usd": r["cost_usd"], "latency_ms": r["latency_ms"],
            "error": r["error"],
        })
        self.tokens_in  += r["tokens_in"]
        self.tokens_out += r["tokens_out"]
        self.cost_usd   += r["cost_usd"]
        self.latency_ms += r["latency_ms"]
        if r["error"]:
            self.success = False

    def to_dict(self) -> dict:
        return {
            "workflow":   self.workflow,
            "period":     self.period,
            "model":      self.model,
            "started":    self.started,
            "completed":  datetime.now(timezone.utc).isoformat(),
            "success":    self.success,
            "hops":       self.hops,
            "totals": {
                "hops":       len(self.hops),
                "tokens_in":  self.tokens_in,
                "tokens_out": self.tokens_out,
                "cost_usd":   round(self.cost_usd, 4),
                "latency_ms": round(self.latency_ms, 0),
            },
            "output": self.output,
        }
