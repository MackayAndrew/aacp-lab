"""AACP Lab v3 — Audit Agent. Deterministic. No LLM. $0.00."""
import json
from datetime import datetime, timezone
from pathlib import Path
from .base_agent import write_audit

class AuditAgent:
    name   = "AUDIT-AGENT"
    domain = "LOG"

    def receive(self, packet: str, data: dict = None) -> dict:
        ts = datetime.now(timezone.utc).isoformat()
        record = {
            "ts": ts, "agent": self.name,
            "packet": packet, "model": "deterministic",
            "cost_usd": 0.0, "tokens_in": 0, "tokens_out": 0,
            "status": "logged", "data": data or {},
        }
        write_audit(record)
        Path("output/payroll_audit.jsonl").parent.mkdir(exist_ok=True)
        with open("output/payroll_audit.jsonl", "a") as f:
            f.write(json.dumps(record) + "\n")
        return {
            "result": {"logged": True, "ts": ts},
            "tokens_in": 0, "tokens_out": 0,
            "latency_ms": 1, "cost_usd": 0.0, "error": None,
        }
