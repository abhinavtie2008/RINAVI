#!/usr/bin/env node
// Keeps the static GitHub Pages demo (docs/assets/js) in step with the code it copies.
//
//   1. catalog/services/**   -> docs/assets/js/pack.js    service and pack data must match exactly
//   2. extraction.py regexes -> docs/assets/js/extract.js  rule text must match
//   3. extraction behaviour  -> both implementations run the same fixtures; results must match
//
// Usage (from anywhere): node scripts/check_demo_sync.mjs
// Needs Python 3.10+ for step 3 (PYTHON=... to choose one). It stubs pypdf, so no install is needed.
//
// Known gap, not checked: Python's \d also matches non-ASCII digits (for example Devanagari
// "५०००"), while the demo reads ASCII digits only. The demo is synthetic-only and says it reads
// text files, so this is accepted; it would be a divergence worth closing if the demo grows.

import assert from "node:assert/strict";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const EXTRACTION_PY = path.join(root, "backend/app/modules/documents/extraction.py");
const failures = [];

function check(name, fn) {
  try {
    fn();
    console.log(`ok   ${name}`);
  } catch (error) {
    failures.push(name);
    console.log(`FAIL ${name}\n${String(error.message).split("\n").map((l) => "     " + l).join("\n")}`);
  }
}

const readJson = (p) => JSON.parse(readFileSync(p, "utf8"));
// Objects built inside a vm context have another realm's prototypes; a JSON round trip makes
// them comparable with assert.deepStrictEqual.
const plain = (value) => JSON.parse(JSON.stringify(value));

// Load the demo scripts the way the browser does: plain scripts that fill globalThis.RINAVI.
const sandbox = vm.createContext({});
for (const file of ["pack.js", "extract.js"]) {
  const full = path.join(root, "docs/assets/js", file);
  vm.runInContext(readFileSync(full, "utf8"), sandbox, { filename: full });
}
const demo = sandbox.RINAVI;

// ---------------------------------------------------------------- 1. service packs
const servicesDir = path.join(root, "catalog/services");
const catalogServices = [];
for (const department of readdirSync(servicesDir, { withFileTypes: true })) {
  if (!department.isDirectory()) continue;
  for (const service of readdirSync(path.join(servicesDir, department.name), { withFileTypes: true })) {
    const dir = path.join(servicesDir, department.name, service.name);
    if (service.isDirectory() && existsSync(path.join(dir, "service.json"))) catalogServices.push(dir);
  }
}

check("demo lists exactly the services in catalog/", () => {
  const fromCatalog = catalogServices.map((dir) => readJson(path.join(dir, "service.json")).slug).sort();
  const fromDemo = plain(demo.catalog.services).map((s) => s.slug).sort();
  assert.deepEqual(fromDemo, fromCatalog, "Update the services in docs/assets/js/pack.js to match catalog/services.");
});

for (const dir of catalogServices) {
  const service = readJson(path.join(dir, "service.json"));
  const packPath = path.join(dir, "versions", service.latest_version, "service_pack.json");
  check(`service.json for ${service.slug} matches the demo`, () => {
    const copy = demo.catalog.services.find((s) => s.slug === service.slug);
    assert.ok(copy, `${service.slug} is missing from docs/assets/js/pack.js`);
    assert.deepStrictEqual(plain(copy), service, "Copy the new service.json values into docs/assets/js/pack.js.");
  });
  check(`service_pack.json ${service.latest_version} for ${service.slug} matches the demo`, () => {
    const copy = demo.catalog.packs[service.slug];
    assert.ok(copy, `no pack for ${service.slug} in docs/assets/js/pack.js`);
    assert.deepStrictEqual(plain(copy), readJson(packPath), "Copy the new service_pack.json into docs/assets/js/pack.js.");
  });
}

// ---------------------------------------------------------------- 2. extraction rule text
const python = readFileSync(EXTRACTION_PY, "utf8");
const rules = demo.extract.rules;
const QUOTED = String.raw`r"((?:[^"\\]|\\.)*)"`;
// "’" and the character itself mean the same inside a regex, so compare them as one.
const unescapeU = (s) => s.replace(/\\u([0-9a-fA-F]{4})/g, (_, hex) => String.fromCharCode(parseInt(hex, 16)));

check("extraction field patterns match extraction.py", () => {
  const re = new RegExp(String.raw`"(\w+)":\s*re\.compile\(\s*${QUOTED},\s*re\.IGNORECASE\s*\)`, "g");
  const fromPython = {};
  for (const [, key, pattern] of python.matchAll(re)) fromPython[key] = unescapeU(pattern.replace("(?P<value>", "("));
  assert.ok(Object.keys(fromPython).length >= 7, "could not read _PATTERNS from extraction.py; update this script");
  const fromDemo = {};
  for (const [key, regex] of Object.entries(rules.PATTERNS)) {
    assert.equal(regex.flags, "i", `${key} must be case-insensitive, like re.IGNORECASE`);
    fromDemo[key] = unescapeU(regex.source);
  }
  assert.deepStrictEqual(fromDemo, fromPython, "A pattern in docs/assets/js/extract.js differs from extraction.py.");
});

check("extraction field keys match FIELD_KEYS", () => {
  const block = /FIELD_KEYS\s*=\s*\(([^)]*)\)/.exec(python);
  assert.ok(block, "could not read FIELD_KEYS from extraction.py; update this script");
  const keys = [...block[1].matchAll(/"(\w+)"/g)].map((m) => m[1]);
  assert.deepStrictEqual(Object.keys(rules.PATTERNS), keys);
});

check("extraction helper patterns match extraction.py", () => {
  // The demo anchors some patterns because Python uses .match() or .fullmatch() on them.
  const table = {
    _AMOUNT: ["AMOUNT", false, false],
    _SCALE_WORD: ["SCALE_WORD", false, false],
    _CURRENCY_PREFIX: ["CURRENCY_PREFIX", false, false],
    _PAREN_AMOUNT: ["PAREN_AMOUNT", true, false],
    _ISO_DATE: ["ISO_DATE", true, true],
    _DAY_FIRST_DATE: ["DAY_FIRST_DATE", true, true],
  };
  const re = new RegExp(String.raw`^(_[A-Z_]+)\s*=\s*re\.compile\(${QUOTED}(?:,\s*re\.IGNORECASE)?\)`, "gm");
  const fromPython = Object.fromEntries([...python.matchAll(re)].map((m) => [m[1], m[2]]));
  for (const [pyName, [jsName, anchoredStart, anchoredEnd]] of Object.entries(table)) {
    assert.ok(pyName in fromPython, `${pyName} not found in extraction.py; update this script`);
    let source = unescapeU(rules[jsName].source);
    if (anchoredStart) source = source.replace(/^\^/, "");
    if (anchoredEnd) source = source.replace(/\$$/, "");
    assert.equal(source, unescapeU(fromPython[pyName]), `${jsName} differs from ${pyName} in extraction.py`);
  }
});

// ---------------------------------------------------------------- 3. extraction behaviour
const fixtures = [
  ...demo.SAMPLES.map((s) => s.text),
  "Name: Asha Verma\nFather's name: Rakesh Verma\nDOB: 12/03/1994\nGender: Female\nAddress: 14 Sample Lane, Delhi\nIncome: Rs 2,40,000\nAadhaar: 0000 0000 0000",
  "Name: A\r\nIncome: 5",
  "   Name   :   Asha    Verma  \n\tAddress\t:\t1  High  St",
  "Applicant Name: B\nName: ignored second name",
  "Name:\nName: \nGender:",
  "no recognised lines here",
  "",
  "\n\n\nName: on line four",
  "Aadhaar number: 1234 5678 9012",
  "Aadhaar: 12345",
  "Address: only an address",
  "Income: 10\nAadhaar: 1",
  ...["Father's name: X", "Father\u2019s Name: Y", "Fathers name: Z", "Father\u2018s name: W", "Father`s name: V", "Father name: U"],
  ...["Male", "FEMALE", "other", "Non-binary", " female "].map((g) => `Gender: ${g}`),
  ...["2000-02-31", "31/12/2000", "31-12-2000", "2000-12-31", "0050-01-01", "0000-01-01", "29/02/2000", "29/02/1900", "12 March 1994", "1994-3-12", "00/00/2000"].map((d) => `DOB: ${d}`),
  "Date of birth : 1994-03-12",
  ...[
    "Rs 120,000.00", "Rs. 1,20,000", "INR 50000", "\u20b91,20,000", "1.2 lakh", "2 lacs", "3 crore", "5 million",
    "(5,000)", "-5000", "Rs -5,000", "INR -5000", "Rs. (5,000)", "(5,000) approx", "Rs 5,000-7,000",
    "0", "007", "abc", "12,34,567", "Rs 1000.50", "about 5000 per year", "", "Rs",
  ].map((v) => `Annual income: ${v}`),
  "Income: 240000",
];

function runPython(texts) {
  const program = [
    "import importlib.util, json, sys, types",
    "sys.modules['pypdf'] = types.ModuleType('pypdf'); sys.modules['pypdf'].PdfReader = None",
    "spec = importlib.util.spec_from_file_location('extraction', sys.argv[1])",
    "mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)",
    "out = []",
    "for text in json.load(sys.stdin):",
    "    found = mod.extract_candidates(text)",
    "    out.append({'classification': mod.classify(found), 'fields': [",
    "        {'field_key': c.field_key, 'value': c.value, 'confidence': c.confidence, 'locator': c.locator}",
    "        for c in found if c.field_key != 'aadhaar_number']})",
    "print(json.dumps(out))",
  ].join("\n");
  const candidates = process.env.PYTHON ? [process.env.PYTHON] : ["python3", "python"];
  for (const exe of candidates) {
    // Probe first: on some systems "python3" is a stub that exists but does not run.
    const probe = spawnSync(exe, ["--version"], { encoding: "utf8" });
    const version = /^Python 3\.(\d+)/.exec(`${probe.stdout || ""}${probe.stderr || ""}`);
    if (probe.error || probe.status !== 0 || !version || Number(version[1]) < 10) continue;
    const result = spawnSync(exe, ["-I", "-c", program, EXTRACTION_PY], { input: JSON.stringify(texts), encoding: "utf8" });
    if (result.status !== 0) throw new Error(`${exe} failed:\n${result.stderr}`);
    return JSON.parse(result.stdout);
  }
  throw new Error("Python 3.10+ was not found. Install it, or set PYTHON to its path.");
}

check(`extraction.py and extract.js agree on ${fixtures.length} fixtures`, () => {
  const expected = runPython(fixtures);
  const mismatches = [];
  fixtures.forEach((text, i) => {
    const got = plain(demo.extract(text));
    const actual = { classification: got.classification, fields: got.fields };
    try {
      assert.deepStrictEqual(actual, expected[i]);
    } catch {
      mismatches.push(`input ${JSON.stringify(text)}\n  extraction.py: ${JSON.stringify(expected[i])}\n  extract.js:    ${JSON.stringify(actual)}`);
    }
  });
  assert.equal(mismatches.length, 0, `${mismatches.length} fixture(s) differ:\n${mismatches.join("\n")}`);
});

if (failures.length) {
  console.error(`\n${failures.length} check(s) failed. The demo under docs/ has drifted from the code it copies.`);
  process.exit(1);
}
console.log("\nDemo is in step with the catalog and the extraction rules.");
