#!/usr/bin/env node
/**
 * Sprint 0 — RA11 tokenizer verification (Stage 10 D-046 freeze gate, G8).
 * Measures: (1) token cost of every .sarib surface sigil, standalone and in realistic context;
 *           (2) whole-file token cost of examples/A-prose-native.sarib vs examples/B-outline-dense.sarib
 *               (raw and comment-stripped).
 * Requires: npm i gpt-tokenizer   (bundles BPE ranks offline — no network at runtime)
 * Run:      node bench/tokenizer_check.js [repoRoot]
 * Encodings: o200k_base (GPT-4o/o-series), cl100k_base (GPT-4/3.5), r50k_base (GPT-2 lineage,
 *            rough proxy for older byte-BPE vocabularies). Open-weight tokenizers (Llama/Qwen)
 *            could not be fetched in-sandbox — flagged as residual in the report.
 */
const fs = require("fs");
const path = require("path");

const root = process.argv[2] || path.join(__dirname, "..");
const encs = {
  o200k: require("gpt-tokenizer/cjs/encoding/o200k_base"),
  cl100k: require("gpt-tokenizer/cjs/encoding/cl100k_base"),
  r50k: require("gpt-tokenizer/cjs/encoding/r50k_base"),
};

const sigils = [
  // bare sigils
  "::", "[[", "]]", "{.", "{#", "^", "#", "-", ">", "|", ":::",
  // realistic in-context lines (Candidate A conventions, D-046)
  "status:: done",
  "due:: 2026-08-01",
  "[due:: 2026-08-01]",
  "priority:: high",
  "[[Target]]",
  "[[Adopt the new billing provider]]",
  "[depends-on:: [[Migrate invoices]]]",
  "{.task}",
  "{.task #migrate-invoices}",
  "### Migrate invoices {.task #migrate-invoices} ^t1",
  "^t1",
  "## Tasks [0/2 done]",
  // Candidate B conventions
  "@task Migrate invoices ^t1 | status=todo due=2026-08-01 pri=high",
  "> depends-on #d1",
];

function row(s) {
  const counts = Object.fromEntries(
    Object.entries(encs).map(([n, e]) => [n, e.encode(s).length])
  );
  return { s, ...counts, chars: s.length };
}

console.log("== Sigil & construct token costs ==");
console.log("tokens (o200k / cl100k / r50k) | chars | string");
for (const s of sigils) {
  const r = row(s);
  console.log(
    `${String(r.o200k).padStart(3)} /${String(r.cl100k).padStart(3)} /${String(r.r50k).padStart(3)}  | ${String(r.chars).padStart(3)}  | ${JSON.stringify(r.s)}`
  );
}

// token-per-char sanity for the load-bearing multi-char sigils, in context
console.log("\n== In-context boundary check (o200k token strings) ==");
for (const s of ["status:: done", "[depends-on:: [[Migrate invoices]]]", "{.task #migrate}", "^t1"]) {
  const ids = encs.o200k.encode(s);
  const pieces = ids.map((id) => JSON.stringify(encs.o200k.decode([id])));
  console.log(`${JSON.stringify(s)}\n   -> ${ids.length} tokens: ${pieces.join(" ")}`);
}

function stripA(t) {
  return t.replace(/<!--[\s\S]*?-->/g, "").replace(/\n{3,}/g, "\n\n");
}
function stripB(t) {
  return t
    .split("\n")
    .filter((l) => !/^\s*;/.test(l))
    .map((l) => l.replace(/\s+;[^"]*$/, "")) // trailing ; comments
    .join("\n");
}

console.log("\n== Whole-file comparison: examples A vs B ==");
const A = fs.readFileSync(path.join(root, "examples", "A-prose-native.sarib"), "utf8");
const B = fs.readFileSync(path.join(root, "examples", "B-outline-dense.sarib"), "utf8");
const cases = {
  "A raw": A,
  "B raw": B,
  "A comment-stripped": stripA(A),
  "B comment-stripped": stripB(B),
};
for (const [name, text] of Object.entries(cases)) {
  const o = encs.o200k.encode(text).length;
  const c = encs.cl100k.encode(text).length;
  console.log(`${name.padEnd(20)} o200k=${String(o).padStart(4)}  cl100k=${String(c).padStart(4)}  chars=${text.length}`);
}
const a = encs.o200k.encode(stripA(A)).length;
const b = encs.o200k.encode(stripB(B)).length;
console.log(`\nB vs A (comment-stripped, o200k): B is ${(100 * (1 - b / a)).toFixed(1)}% fewer tokens`);
