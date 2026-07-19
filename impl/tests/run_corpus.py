"""Conformance corpus runner (Stage 13 §6, RG2/RM22).
Each case: corpus/NN-name.sarib -> corpus/NN-name.expected (canonical form).
Also enforces: G6 round-trip (canon(parse(fmt(parse(x)))) == canon(parse(x)))
and fmt idempotence (D-051). Exit 0 = conforming.
Regenerate expectations: python run_corpus.py --bless
"""
import pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from sarib import parse, canon, fmt

CORPUS = pathlib.Path(__file__).parent / "corpus"


def main():
    bless = "--bless" in sys.argv
    fails = 0
    for case in sorted(CORPUS.glob("*.sarib")):
        exp = case.with_suffix(".expected")
        src = case.read_text(encoding="utf-8")
        got = canon(parse(src))
        # G6 round-trip + D-051 idempotence
        rt = canon(parse(fmt(parse(src))))
        rt_ok = rt == got
        idem = fmt(parse(fmt(parse(src)))) == fmt(parse(src))
        if bless:
            exp.write_text(got, encoding="utf-8")
            status = "BLESSED"
        elif not exp.exists():
            status = "NO-EXPECTATION"; fails += 1
        elif got != exp.read_text(encoding="utf-8"):
            status = "FAIL-CANON"; fails += 1
        elif not rt_ok:
            status = "FAIL-ROUNDTRIP"; fails += 1
        elif not idem:
            status = "FAIL-IDEMPOTENCE"; fails += 1
        else:
            status = "ok"
        print(f"{status:16} {case.name}   (roundtrip={'ok' if rt_ok else 'FAIL'}, idempotent={'ok' if idem else 'FAIL'})")
    print(f"\n{'CONFORMING' if fails == 0 else f'{fails} FAILURES'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
