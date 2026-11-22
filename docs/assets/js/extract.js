/* Deterministic field extraction, ported from backend/app/modules/documents/extraction.py.
   Rules, not AI: each field comes from a "Label: value" line, with a confidence and a line locator.
   Aadhaar numbers are recognised only to classify a document as identity proof; the number itself
   is dropped here and never stored, matching the repo's "Aadhaar stays on the portal" rule. */
(function () {
  "use strict";
  const R = (globalThis.RINAVI = globalThis.RINAVI || {});

  const PATTERNS = {
    full_name: /^(?:applicant\s+)?name\s*:\s*(.+)$/i,
    father_name: /^father['’‘`]?s?\s+name\s*:\s*(.+)$/i,
    date_of_birth: /^(?:date\s+of\s+birth|dob)\s*:\s*(.+)$/i,
    gender: /^gender\s*:\s*(.+)$/i,
    address: /^address\s*:\s*(.+)$/i,
    annual_income: /^(?:annual\s+)?income\s*:\s*(.+)$/i,
    aadhaar_number: /^aadhaar(?:\s+number)?\s*:\s*(.+)$/i,
  };

  const AMOUNT = /\d[\d,]*(?:\.\d+)?/;
  const SCALE_WORD = /\b(?:lakhs?|lacs?|crores?|million|billion)\b/i;
  const CURRENCY_PREFIX = /^\s*(?:rs\.?|inr|₹)\s*/i;
  const PAREN_AMOUNT = /^\([\d,]+(?:\.\d+)?\)/;
  const ISO_DATE = /^(\d{4})-(\d{2})-(\d{2})$/;
  const DAY_FIRST_DATE = /^(\d{2})[/-](\d{2})[/-](\d{4})$/;

  function isoOrRaw(value, y, m, d) {
    const year = Number(y), month = Number(m), day = Number(d);
    const dt = new Date(Date.UTC(year, month - 1, day));
    if (year < 1 || dt.getUTCFullYear() !== year || dt.getUTCMonth() !== month - 1 || dt.getUTCDate() !== day) {
      return [value, "low"];
    }
    return [`${y}-${m}-${d}`, "high"];
  }

  function normDate(raw) {
    const value = raw.trim();
    let m = ISO_DATE.exec(value);
    if (m) return isoOrRaw(value, m[1], m[2], m[3]);
    m = DAY_FIRST_DATE.exec(value);
    if (m) return isoOrRaw(value, m[3], m[2], m[1]);
    return [value, "low"];
  }

  function normGender(raw) {
    const value = raw.trim().toLowerCase();
    return ["male", "female", "other"].includes(value) ? [value, "high"] : [raw.trim(), "low"];
  }

  function normIncome(raw) {
    const value = raw.trim();
    if (SCALE_WORD.test(value)) return [value, "low"];
    const rest = value.replace(CURRENCY_PREFIX, "").trim();
    if ((value.startsWith("(") && value.endsWith(")")) || rest.startsWith("-") || PAREN_AMOUNT.test(rest)) {
      return [value, "low"]; // accounting negatives are losses, never income
    }
    const amount = AMOUNT.exec(value);
    if (!amount) return [value, "low"];
    const rupees = amount[0].split(".")[0].replace(/,/g, "").replace(/^0+(?=\d)/, "");
    return [rupees, "high"];
  }

  function normPlain(raw) {
    const value = raw.trim();
    return value ? [value, "high"] : [value, "low"];
  }

  const NORMALIZERS = {
    full_name: normPlain,
    father_name: normPlain,
    date_of_birth: normDate,
    gender: normGender,
    address: normPlain,
    annual_income: normIncome,
    aadhaar_number: () => ["", "high"],
  };

  function classify(keys) {
    if (keys.has("annual_income")) return "income";
    if (keys.has("aadhaar_number")) return "identity";
    if (keys.has("address")) return "residence";
    return "unsupported";
  }

  /** Returns {fields, classification, lines}. fields exclude Aadhaar. */
  function extract(text) {
    const fields = [];
    const seen = new Set();
    const lines = String(text).split(/\r?\n/);
    lines.forEach((line, index) => {
      const stripped = line.split(/\s+/).filter(Boolean).join(" ");
      if (!stripped) return;
      for (const key of Object.keys(PATTERNS)) {
        if (seen.has(key)) continue;
        const match = PATTERNS[key].exec(stripped);
        if (!match) continue;
        const [value, confidence] = NORMALIZERS[key](match[1]);
        seen.add(key);
        if (key !== "aadhaar_number") {
          fields.push({ field_key: key, value, confidence, locator: `line ${index + 1}` });
        }
        break;
      }
    });
    return { fields, classification: classify(seen), lines: lines.length };
  }

  R.extract = extract;
})();
