import { readFileSync } from "node:fs";

import { expect, test, type Page } from "@playwright/test";

// One citizen journey against the compose demo stack (dev sign-in enabled).
// Every run uses a fresh account so state never leaks between runs.
const INCOME_LINES = [
  "Applicant Name: Asha Devi",
  "Father's Name: Rajesh Devi",
  "Date of Birth: 12/03/1994",
  "Gender: Female",
  "Address: 14, Nehru Colony, Example Nagar",
  "Annual Income: Rs. 1,20,000",
];

const IDENTITY_LINES = ["Applicant Name: Asha Devi", "Aadhaar: 1234 5678 9012"];

type DemoDocument = { name: string; buffer: Buffer };

// A single-page text PDF, mirroring tests/factories.py on the backend: the
// pipeline needs a real text layer, and a generated file keeps binaries out
// of the repository.
function makeTextPdf(lines: string[]): Buffer {
  const contentLines = ["BT", "/F1 12 Tf", "72 760 Td", "14 TL"];
  for (const line of lines) {
    const escaped = line
      .replace(/\\/g, "\\\\")
      .replace(/\(/g, "\\(")
      .replace(/\)/g, "\\)");
    contentLines.push(`(${escaped}) Tj T*`);
  }
  contentLines.push("ET");
  const content = contentLines.join("\n");

  const objects = [
    "<< /Type /Catalog /Pages 2 0 R >>",
    "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R " +
      "/Resources << /Font << /F1 5 0 R >> >> >>",
    `<< /Length ${Buffer.byteLength(content, "latin1")} >>\nstream\n${content}\nendstream`,
    "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
  ];

  let pdf = "%PDF-1.4\n";
  const offsets: number[] = [];
  objects.forEach((object, index) => {
    offsets.push(Buffer.byteLength(pdf, "latin1"));
    pdf += `${index + 1} 0 obj\n${object}\nendobj\n`;
  });
  const xrefStart = Buffer.byteLength(pdf, "latin1");
  pdf += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  for (const offset of offsets) {
    pdf += `${String(offset).padStart(10, "0")} 00000 n \n`;
  }
  pdf +=
    "trailer\n" +
    `<< /Size ${objects.length + 1} /Root 1 0 R >>\n` +
    `startxref\n${xrefStart}\n%%EOF\n`;
  return Buffer.from(pdf, "latin1");
}

async function signIn(page: Page, email: string): Promise<void> {
  await page.goto("/");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByTestId("signed-in")).toContainText(email);
}

async function uploadDocuments(
  page: Page,
  documents: DemoDocument[],
): Promise<void> {
  await page.goto("/vault");
  await page
    .getByRole("button", { name: "Allow document processing" })
    .click();
  await expect(page.getByLabel("Document file")).toBeVisible();

  for (const document of documents) {
    await page.getByLabel("Document file").setInputFiles({
      name: document.name,
      mimeType: "application/pdf",
      buffer: document.buffer,
    });
    await page.getByRole("button", { name: "Upload document" }).click();
    await expect(
      page.getByTestId("document-row").filter({ hasText: document.name }),
    ).toContainText("Ready");
  }
}

async function promoteAndConfirmProfile(page: Page): Promise<void> {
  await page.goto("/profile");
  await page.getByRole("button", { name: "Allow profile storage" }).click();
  await expect(page.getByTestId("promote-section")).toBeVisible();

  await page
    .locator("li", { hasText: "income.pdf" })
    .getByRole("button", { name: "Use this document" })
    .click();

  // The promoted values arrive unconfirmed; a draft only seeds confirmed ones.
  await expect(
    page.getByTestId("profile-value").filter({ hasText: "Annual income" }),
  ).toContainText("120000");

  const confirm = page.getByRole("button", { name: "Confirm" });
  for (let guard = 0; guard < 10; guard += 1) {
    const remaining = await confirm.count();
    if (remaining === 0) {
      break;
    }
    await confirm.first().click();
    await expect(confirm).toHaveCount(remaining - 1);
  }
  await expect(confirm).toHaveCount(0);
}

async function openNewDraft(page: Page): Promise<void> {
  await page.goto("/applications");
  await page
    .getByRole("button", { name: "Allow application preparation" })
    .click();
  await expect(page.locator("#service-picker")).toBeVisible();
  await page
    .locator("#service-picker")
    .selectOption({ label: "Income Certificate (Delhi)" });
  await page.getByRole("button", { name: "Start new application" }).click();
  await page.getByTestId("draft-row").getByRole("link").click();
}

async function attachEvidence(
  page: Page,
  groupId: string,
  filename: string,
  expectedLinks: number,
): Promise<void> {
  const select = page.locator(`#attach-${groupId}`);
  await select.selectOption({ label: filename });
  await select.locator("..").getByRole("button", { name: "Attach" }).click();
  await expect(page.getByRole("button", { name: "Remove" })).toHaveCount(
    expectedLinks,
  );
}

test("a citizen prepares a complete packet through the web app", async ({
  page,
}) => {
  const email = `e2e-${Date.now()}@example.com`;

  await signIn(page, email);
  await uploadDocuments(page, [
    { name: "income.pdf", buffer: makeTextPdf(INCOME_LINES) },
    { name: "identity.pdf", buffer: makeTextPdf(IDENTITY_LINES) },
  ]);
  await promoteAndConfirmProfile(page);
  await openNewDraft(page);

  // The Assist-only boundary is on the draft itself, before any work.
  await expect(page.getByTestId("submission-notice")).toContainText(
    "RINAVI prepares this draft for your review only",
  );

  const purpose = page.locator("#field-purpose");
  await purpose.fill("Scholarship application");
  await purpose
    .locator("..")
    .getByRole("button", { name: "Save" })
    .click();

  // residence_proof accepts residence and identity documents (an Aadhaar line
  // carries the address), but not an income-only document.
  await attachEvidence(page, "identity_proof", "identity.pdf", 1);
  await attachEvidence(page, "income_evidence", "income.pdf", 2);
  await attachEvidence(page, "residence_proof", "identity.pdf", 3);

  // The checkbox is controlled: it flips only after the declaration request
  // succeeds, so click and then poll rather than assert synchronously.
  await page.locator("#declaration").click();
  await expect(page.locator("#declaration")).toBeChecked();
  await expect(page.getByTestId("draft-ready")).toBeVisible();

  await page.getByRole("button", { name: "Preview final draft" }).click();
  await expect(page.getByTestId("export-text")).toContainText(
    "NOT a submission",
  );
  await expect(page.getByTestId("export-text")).toContainText(
    "Asha Devi",
  );
});

// Item 102: the controls the privacy notice promises. The export is checked by
// reading the downloaded file, because the promise is about its contents, not
// about a button having been clicked.
test("a citizen downloads their account record and deletes the account", async ({
  page,
}) => {
  const email = `e2e-account-${Date.now()}@example.com`;

  await signIn(page, email);
  await uploadDocuments(page, [
    { name: "income.pdf", buffer: makeTextPdf(INCOME_LINES) },
  ]);

  await page.goto("/account");
  await expect(page.getByTestId("account-user")).toContainText(email);

  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page
      .getByRole("button", { name: "Download account record and permissions" })
      .click(),
  ]);
  expect(download.suggestedFilename()).toBe("rinavi-account-export.json");
  const path = await download.path();
  if (!path) {
    throw new Error("the export was not saved to disk");
  }
  const exported = JSON.parse(readFileSync(path, "utf8"));
  expect(exported.user.email).toBe(email);
  // Exactly the server contract: no documents, no profile values.
  expect(Object.keys(exported).sort()).toEqual(["consent_records", "user"]);
  expect(
    exported.consent_records.map((record: { purpose: string }) => record.purpose),
  ).toContain("documents.processing");

  page.on("dialog", (dialog) => void dialog.accept());
  await page.getByRole("button", { name: "Delete my account" }).click();
  await expect(page).toHaveURL(/\/$/);

  // The session went with the account: the sign-in form is back.
  await expect(page.getByLabel("Email")).toBeVisible();

  // Signing in again creates a new account; the old documents are not there.
  await signIn(page, email);
  await page.goto("/vault");
  await expect(
    page.getByRole("button", { name: "Allow document processing" }),
  ).toBeVisible();
  await expect(page.getByTestId("document-row")).toHaveCount(0);
});
