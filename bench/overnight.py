"""Overnight G2 supervisor. Retries every API provider on a fixed cadence so that
quota resets (Groq daily tokens, Gemini 20/day, OpenRouter 50/day) are picked up
without supervision. Local models are already complete. Idempotent + cache-backed:
every pass resumes from results/*.jsonl, so re-running only fills missing cells.

Exits when all target models reach full coverage (432 cells) OR max passes hit.
Prints a timestamped progress line each pass; nothing is ever dropped.

Run:  python bench/overnight.py           (defaults: 18 passes, 75 min apart)
"""
from __future__ import annotations
import json, pathlib, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "bench" / "g2-corpus" / "results"
PY = sys.executable
FULL = 432
PASSES = int(sys.argv[1]) if len(sys.argv) > 1 else 18
GAP_S = int(sys.argv[2]) if len(sys.argv) > 2 else 75 * 60

# API providers to chase (local tier done; cerebras intentionally excluded)
TARGETS = {
    "groq": ["llama-3.3-70b-versatile", "openai/gpt-oss-120b", "qwen/qwen3.6-27b", "llama-3.1-8b-instant"],
    "gemini": ["gemini-3.5-flash"],
    "openrouter": ["nvidia/nemotron-3-super-120b-a12b:free"],
}


def cells(provider, model):
    slug = "".join(c if c.isalnum() or c in "._-" else "_" for c in f"{provider}_{model}")
    p = RESULTS / f"raw-{slug}.jsonl"
    if not p.exists():
        return 0
    return sum(1 for l in p.read_text(encoding="utf-8").splitlines() if '"qid"' in l)


def snapshot():
    return {(pv, m): cells(pv, m) for pv, ms in TARGETS.items() for m in ms}


def done(snap):
    return all(v >= FULL for v in snap.values())


def log(msg):
    # no wall clock available in-tool; use a monotonic pass marker instead
    print(msg, flush=True)


def main():
    log("overnight supervisor start")
    for pv, ms in TARGETS.items():
        for m in ms:
            log(f"  target {pv}/{m}: {cells(pv, m)}/{FULL}")
    for i in range(1, PASSES + 1):
        snap = snapshot()
        if done(snap):
            log(f"pass {i}: MATRIX COMPLETE — all targets at {FULL}")
            break
        for pv in TARGETS:
            if all(cells(pv, m) >= FULL for m in TARGETS[pv]):
                continue
            log(f"pass {i}: running --providers {pv}")
            try:
                subprocess.run([PY, str(ROOT / "bench" / "run_g2.py"), "run", "--providers", pv],
                               cwd=str(ROOT), timeout=3 * 3600)
            except Exception as e:
                log(f"pass {i}: {pv} raised {e!r} (cached; will retry)")
        after = snapshot()
        gained = sum(after.values()) - sum(snap.values())
        log(f"pass {i} done: +{gained} cells | " +
            " ".join(f"{pv.split('/')[0]}/{m.split('/')[-1]}={after[(pv, m)]}"
                     for pv, m in after))
        subprocess.run([PY, str(ROOT / "bench" / "run_g2.py"), "report"], cwd=str(ROOT))
        if done(after):
            log(f"pass {i}: MATRIX COMPLETE")
            break
        if i < PASSES:
            time.sleep(GAP_S)
    subprocess.run([PY, str(ROOT / "bench" / "run_g2.py"), "report"], cwd=str(ROOT))
    final = snapshot()
    log("FINAL: " + " ".join(f"{pv}/{m.split('/')[-1]}={v}/{FULL}" for (pv, m), v in final.items()))
    log("complete=" + str(done(final)))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
