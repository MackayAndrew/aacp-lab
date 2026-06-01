"""
AACP Lab v3 — Base Agent
Multi-provider support. Anthropic and OpenAI.
Cost tracking and audit logging built in.
"""

import os, re, json, time
from datetime import datetime, timezone
from pathlib import Path

MODEL_REGISTRY = {
    "gpt-4.1-mini":      {"provider": "openai",    "cost_per_1m": 0.40},
    "gpt-4.1":           {"provider": "openai",    "cost_per_1m": 2.00},
    "claude-sonnet-4-5": {"provider": "anthropic", "cost_per_1m": 3.00},
    "gpt-4o":            {"provider": "openai",    "cost_per_1m": 5.00},
}

AUDIT_LOG = Path("output/audit.jsonl")

def write_audit(entry: dict):
    AUDIT_LOG.parent.mkdir(exist_ok=True)
    with open(AUDIT_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


class BaseAgent:
    name:          str = "BASE-AGENT"
    domain:        str = "UNKNOWN"
    system_prompt: str = ""

    def __init__(self, model: str = "gpt-4.1-mini"):
        cfg = MODEL_REGISTRY.get(model, {"provider": "openai", "cost_per_1m": 0.40})
        self.model    = model
        self.provider = cfg["provider"]
        self.cpm      = cfg["cost_per_1m"]
        self._anth    = None
        self._oai     = None

    def _client(self):
        if self.provider == "anthropic":
            if not self._anth:
                import anthropic
                self._anth = anthropic.Anthropic(
                    api_key=os.environ.get("ANTHROPIC_API_KEY"))
            return self._anth
        else:
            if not self._oai:
                from openai import OpenAI
                self._oai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            return self._oai

    def receive(self, packet: str, data: dict = None) -> dict:
        parts = [f"Coordination packet:\n{packet}"]
        if data:
            parts.append(f"\nData:\n{json.dumps(data, indent=2)}")
        parts.append("\nRespond with valid JSON only. No markdown fences.")
        user_msg = "\n".join(parts)

        start = time.time()
        tokens_in = tokens_out = 0
        raw = ""

        try:
            client = self._client()
            if self.provider == "anthropic":
                r = client.messages.create(
                    model=self.model, max_tokens=2000,
                    system=self.system_prompt,
                    messages=[{"role": "user", "content": user_msg}],
                )
                raw        = r.content[0].text.strip()
                tokens_in  = r.usage.input_tokens
                tokens_out = r.usage.output_tokens
            else:
                r = client.chat.completions.create(
                    model=self.model, max_tokens=2000,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user",   "content": user_msg},
                    ],
                )
                raw        = r.choices[0].message.content.strip()
                tokens_in  = r.usage.prompt_tokens
                tokens_out = r.usage.completion_tokens

            latency_ms = (time.time() - start) * 1000
            raw = re.sub(r'^```(?:json)?\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)
            result   = json.loads(raw.strip())
            cost_usd = (tokens_in + tokens_out) / 1_000_000 * self.cpm

            write_audit({
                "ts": datetime.now(timezone.utc).isoformat(),
                "agent": self.name, "model": self.model,
                "packet": packet, "tokens_in": tokens_in,
                "tokens_out": tokens_out, "cost_usd": round(cost_usd, 6),
                "latency_ms": round(latency_ms, 0), "status": "ok",
            })

            return {
                "result": result, "tokens_in": tokens_in,
                "tokens_out": tokens_out, "latency_ms": round(latency_ms, 0),
                "cost_usd": round(cost_usd, 6), "error": None,
            }

        except json.JSONDecodeError as e:
            latency_ms = (time.time() - start) * 1000
            write_audit({"ts": datetime.now(timezone.utc).isoformat(),
                "agent": self.name, "model": self.model,
                "packet": packet, "status": "json_error", "error": str(e)})
            return {
                "result": None, "tokens_in": tokens_in, "tokens_out": tokens_out,
                "latency_ms": round(latency_ms, 0), "cost_usd": 0.0,
                "error": f"JSON parse error: {e}\nRaw: {raw[:300]}",
            }
        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            write_audit({"ts": datetime.now(timezone.utc).isoformat(),
                "agent": self.name, "model": self.model,
                "packet": packet, "status": "error", "error": str(e)})
            return {
                "result": None, "tokens_in": 0, "tokens_out": 0,
                "latency_ms": round(latency_ms, 0), "cost_usd": 0.0,
                "error": str(e),
            }
