"""sarib — reference implementation of the .sarib knowledge language (v0.1).
Components per Stage 13: parser, canon(normalizer), model store, ops, query, render.
"""
from .parser import parse
from .canon import canon
from .render import fmt, VIEWS
from .ops import apply, fold, OpRejected
from .query import query

__version__ = "0.1.5"
