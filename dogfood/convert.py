"""Dogfood converter: project .md artifacts -> .sarib (Candidate A surface).
The self-hosting test (RH2 instrument): the project's own decision log and risk
register become queryable, op-editable .sarib knowledge.
Run: python dogfood/convert.py   (from repo root)
"""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]


def decisions():
    src = (ROOT / "decisions" / "decision-log.md").read_text(encoding="utf-8")
    out = ["---", "sarib: 0.1", "vocab: std@0.1", "title: .sarib Decision Log", "---", "",
           "# Decision Log {#decision-log}", ""]
    blocks = re.split(r"\n## (D-\d+) · ", src)[1:]
    for i in range(0, len(blocks), 2):
        did, body = blocks[i], blocks[i + 1]
        title, rest = body.split("\n", 1)
        meta = dict(re.findall(r"\*\*(Date|Stage|Status):\*\* ([^·\n]+)", rest))
        out.append(f"## {did}: {title.strip()} {{.decision #{did.lower()}}} ^{did.lower()}")
        out.append(f"date:: {meta.get('Date','').strip()}")
        out.append(f"stage:: {meta.get('Stage','').strip()}")
        out.append(f"status:: {meta.get('Status','').strip().split(' ')[0].rstrip('—').lower() or 'provisional'}")
        m = re.search(r"\*\*Reversal condition:\*\* (.+)", rest)
        if m:
            out.append(f"reversal:: {m.group(1).strip()}")
        m = re.search(r"\*\*Choice:\*\* (.+)", rest)
        if m:
            out.append("")
            out.append(m.group(1).strip())
        out.append("")
    (ROOT / "dogfood" / "decision-log.sarib").write_text("\n".join(out), encoding="utf-8")
    return len(blocks) // 2


def risks():
    src = (ROOT / "risks" / "risk-register.md").read_text(encoding="utf-8")
    out = ["---", "sarib: 0.1", "vocab: std@0.1", "title: .sarib Risk Register", "---", "",
           "# Risk Register {#risk-register}", ""]
    n = 0
    cat = ""
    for line in src.splitlines():
        m = re.match(r"^## \d+\. (R[A-Z]) — (.+)$", line)
        if m:
            cat = m.group(2)
            out.append(f"## {m.group(1)} — {cat} {{.section}}")
            out.append("")
            continue
        m = re.match(r"^\| (R[A-Z]\d+) \| ([^|]+) \| ([LMH]) \| ([LMH]) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| (🔴|🟠|🟡|🟢) (\w+)", line)
        if m:
            rid, risk, lik, imp, phase, signal, mitig, _, status = [x.strip() for x in m.groups()]
            out.append(f"### {rid}: {risk} {{.risk #{rid.lower()}}} ^{rid.lower()}")
            out.append(f"likelihood:: {lik}")
            out.append(f"impact:: {imp}")
            out.append(f"phase:: {phase}")
            out.append(f"status:: {status}")
            out.append(f"signal:: {signal}")
            out.append("")
            out.append(mitig)
            out.append("")
            n += 1
    (ROOT / "dogfood" / "risk-register.sarib").write_text("\n".join(out), encoding="utf-8")
    return n


if __name__ == "__main__":
    print(f"decisions: {decisions()} converted")
    print(f"risks:     {risks()} converted")
