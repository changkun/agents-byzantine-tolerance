"""Experiment 04 — Ambiguous-Spec Detection via Partial Agreement Maps.

Each cell shows N agents an unambiguous- or ambiguous-version spec text plus
a fixed decision checklist; agents must commit to a value for every decision.
The runner computes per-decision disagreement (entropy for categorical,
coefficient of variation for numeric) and pairs those scores against the
author-labelled ambiguity set to ask: does disagreement predict ambiguity?

CLI:
  python experiments/04_ambiguous_spec.py --smoke
  python experiments/04_ambiguous_spec.py --ns 5 --trials 3
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import re
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results"

sys.path.insert(0, str(REPO_ROOT))
from agents_byzantine_tolerance.agent import (  # noqa: E402
    Agent,
    AgentError,
    DEFAULT_CONFIGS,
)


SYSTEM_PROMPT = """\
You are committing to concrete design decisions for a software component.
You will receive:
  1. A specification text.
  2. A decision checklist with N slots. Each slot is either categorical
     (with allowed options listed) or numeric (free integer).

For every slot you MUST pick exactly one value, even if the spec is silent
on it. If the spec under-specifies a slot, use your best judgment — do
NOT return placeholders, ranges, or "depends on context".

Output rules (strict):
- Reply with a single JSON object on the FINAL line of your response.
- Keys are decision slot keys. Values are: a single option string (categorical)
  or a single integer (numeric).
- The JSON object must be the entire final line. No prose on that line.
"""

USER_TEMPLATE = """\
SPEC:
{spec}

DECISIONS (you must commit to exactly one value per key):
{checklist}

Reply with a JSON object on the final line, keys = decision keys, values =
your chosen option (lowercase, exact-match for categorical) or integer.
"""


_JSON_LINE = re.compile(r"\{.*\}")


def parse_decisions(text: str, decisions: list[dict]) -> dict | None:
    if not text:
        return None
    for line in reversed([ln for ln in text.splitlines() if ln.strip()][-5:]):
        m = _JSON_LINE.search(line)
        if not m:
            continue
        try:
            obj = json.loads(m.group(0))
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        out: dict = {}
        for d in decisions:
            v = obj.get(d["key"])
            if v is None:
                out[d["key"]] = None
                continue
            if d["kind"] == "categorical":
                s = str(v).strip().lower()
                # Accept exact matches OR (rough) substring of any option
                opts = [str(o).lower() for o in d["options"]]
                if s in opts:
                    out[d["key"]] = s
                else:
                    matches = [o for o in opts if o in s or s in o]
                    out[d["key"]] = matches[0] if len(matches) == 1 else None
            elif d["kind"] == "numeric":
                if isinstance(v, (int, float)) and v == int(v):
                    out[d["key"]] = int(v)
                elif isinstance(v, str):
                    try:
                        out[d["key"]] = int(v.strip())
                    except ValueError:
                        out[d["key"]] = None
                else:
                    out[d["key"]] = None
        return out
    return None


def _checklist_text(decisions: list[dict]) -> str:
    lines = []
    for d in decisions:
        if d["kind"] == "categorical":
            opts = ", ".join(str(o) for o in d["options"])
            lines.append(
                f"- {d['key']}: {d['prompt']} (categorical; options: {opts})"
            )
        else:
            lines.append(f"- {d['key']}: {d['prompt']} (numeric integer)")
    return "\n".join(lines)


def disagreement_score(values: list, kind: str) -> float | None:
    """Entropy for categorical, coefficient-of-variation for numeric.

    Both normalised to [0,1] for plotting; entropy uses ln(k) where k is
    the number of distinct values in this slot's options. CV is clipped at 1.
    """
    valid = [v for v in values if v is not None]
    if len(valid) < 2:
        return None
    if kind == "categorical":
        counts = Counter(valid)
        total = sum(counts.values())
        probs = [c / total for c in counts.values()]
        ent = -sum(p * math.log(p) for p in probs if p > 0)
        # Normalise by ln(N) so entropy is in [0,1] regardless of N.
        max_ent = math.log(min(len(valid), 4))  # 4 typical options
        return ent / max_ent if max_ent > 0 else 0.0
    if kind == "numeric":
        mean = statistics.mean(valid)
        if mean == 0:
            return 1.0 if len(set(valid)) > 1 else 0.0
        std = statistics.stdev(valid) if len(valid) > 1 else 0.0
        return min(1.0, abs(std / mean))
    return None


def build_agents(n: int, composition: str) -> list[Agent]:
    if composition == "homogeneous-claude":
        return [Agent(f"claude-{i}", DEFAULT_CONFIGS["claude-haiku"]) for i in range(n)]
    if composition == "homogeneous-codex":
        return [Agent(f"codex-{i}", DEFAULT_CONFIGS["codex-default"]) for i in range(n)]
    if composition == "heterogeneous":
        cs = [DEFAULT_CONFIGS["claude-haiku"], DEFAULT_CONFIGS["codex-default"]]
        return [Agent(f"agent-{i}-{cs[i % 2].kind.value}", cs[i % 2]) for i in range(n)]
    raise ValueError(composition)


async def run_cell(
    pair: dict,
    variant: str,
    n: int,
    composition: str,
    trial: int,
    sem: asyncio.Semaphore,
    timeout_s: float,
) -> dict:
    decisions = pair["decisions"]
    spec_text = pair["variants"][variant]["text"]
    ambiguity_set = pair["variants"][variant]["ambiguity_set"]
    agents = build_agents(n, composition)
    user = USER_TEMPLATE.format(spec=spec_text, checklist=_checklist_text(decisions))

    async def one(agent: Agent) -> dict:
        async with sem:
            try:
                resp = await agent.query(
                    user, system=SYSTEM_PROMPT, timeout=timeout_s
                )
                answers = parse_decisions(resp.final_message, decisions)
                return {
                    "agent_id": agent.agent_id,
                    "kind": agent.config.kind.value,
                    "model": agent.config.model,
                    "raw_tail": resp.final_message[-1500:],
                    "answers": answers,
                    "rc": resp.returncode,
                    "error": None,
                }
            except AgentError as e:
                return {
                    "agent_id": agent.agent_id,
                    "kind": agent.config.kind.value,
                    "model": agent.config.model,
                    "raw_tail": "",
                    "answers": None,
                    "rc": -1,
                    "error": str(e),
                }

    t0 = time.time()
    agent_results = await asyncio.gather(*(one(a) for a in agents))
    dt = time.time() - t0

    per_decision: dict = {}
    for d in decisions:
        vals = [
            (r["answers"] or {}).get(d["key"]) if r["answers"] else None
            for r in agent_results
        ]
        per_decision[d["key"]] = {
            "kind": d["kind"],
            "values": vals,
            "score": disagreement_score(vals, d["kind"]),
            "in_ambiguity_set": d["key"] in ambiguity_set,
        }

    return {
        "pair_id": pair["id"],
        "domain": pair["domain"],
        "variant": variant,
        "n": n,
        "composition": composition,
        "trial": trial,
        "duration_s": round(dt, 2),
        "agents": agent_results,
        "per_decision": per_decision,
        "ambiguity_set": ambiguity_set,
    }


def already_done(path: Path) -> set[tuple]:
    if not path.exists():
        return set()
    done = set()
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        done.add((rec["pair_id"], rec["variant"], rec["n"], rec["composition"], rec["trial"]))
    return done


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--specs", default=str(REPO_ROOT / "experiments" / "specs.yaml"))
    ap.add_argument("--output", default=None)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--timeout", type=float, default=180)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--ns", help="default 3,5,7")
    ap.add_argument("--compositions", help="default homogeneous-claude,heterogeneous")
    ap.add_argument("--trials", type=int, default=3)
    args = ap.parse_args()

    bank = yaml.safe_load(Path(args.specs).read_text())
    pairs = bank["pairs"]
    if args.smoke:
        ns = [3]
        compositions = ["homogeneous-claude"]
        trials = 1
        pairs = pairs[:1]
    else:
        ns = [int(x) for x in args.ns.split(",")] if args.ns else [3, 5, 7]
        compositions = args.compositions.split(",") if args.compositions else [
            "homogeneous-claude",
            "heterogeneous",
        ]
        trials = args.trials

    if args.output is None:
        tag = "smoke" if args.smoke else "full"
        args.output = str(RESULTS_DIR / "04_ambiguous_spec" / f"{tag}.jsonl")
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = already_done(out_path) if args.resume else set()
    if not args.resume and out_path.exists():
        out_path.unlink()

    sem = asyncio.Semaphore(args.concurrency)
    cells = [
        (p, v, n, c, t)
        for p in pairs
        for v in ("unambiguous", "ambiguous")
        for n in ns
        for c in compositions
        for t in range(trials)
    ]
    total = len(cells)
    completed = 0

    print("=== Experiment 04: Ambiguous-Spec Detection ===")
    print(f"pairs:        {[p['id'] for p in pairs]}")
    print(f"N:            {ns}  comp: {compositions}  trials: {trials}")
    print(f"total cells:  {total}\n")

    with out_path.open("a") as fout:
        for p, v, n, c, t in cells:
            key = (p["id"], v, n, c, t)
            if key in done:
                completed += 1
                continue
            print(
                f"[{completed + 1}/{total}] {p['id']} {v} N={n} {c} trial={t}",
                flush=True,
            )
            try:
                rec = await run_cell(p, v, n, c, t, sem, args.timeout)
            except Exception as exc:  # noqa: BLE001
                print(f"    !! {exc!r}")
                completed += 1
                continue
            fout.write(json.dumps(rec) + "\n")
            fout.flush()
            scores = {k: round(d["score"] or 0, 2) for k, d in rec["per_decision"].items()}
            print(f"    scores: {scores}  {rec['duration_s']}s")
            completed += 1

    print(f"\nDone. {completed}/{total} cells.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
