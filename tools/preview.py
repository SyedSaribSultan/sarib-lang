"""Shim: the previewer now lives in the package as `sarib.preview` so it can run
from any folder (`python -m sarib.preview`), not just a repo checkout.
This keeps the documented `python tools/preview.py <file.sarib>` path working and
prefers the in-repo impl/ over any installed copy.
"""
import pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "impl"))
from sarib.preview import main

if __name__ == "__main__":
    main()
