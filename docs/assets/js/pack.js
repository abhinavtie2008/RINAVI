/* Service catalog for the demo.
   The service and pack below are copied from catalog/services/edistrict/income-certificate
   in the RINAVI repository (service.json and versions/1.0.0/service_pack.json). */
(function () {
  "use strict";
  const R = (globalThis.RINAVI = globalThis.RINAVI || {});

  const service = {
    slug: "delhi-income-certificate",
    name: "Income Certificate (Delhi)",
    geography: "Delhi",
    department: "Revenue Department, Government of NCT of Delhi",
    latest_version: "1.0.0",
    summary: "Prepare a Delhi income certificate application with source-linked profile values and evidence checks.",
    tags: ["income certificate", "delhi", "e-district"],
    fee: "No application fee listed by the official source",
    processing_time: "Indicative only: around 14 days after submission; not a guarantee",
    sources: [
      { title: "e-District Delhi", url: "https://edistrict.delhigovt.nic.in/" },
      { title: "Revenue Department, GNCTD — Income Certificate", url: "https://revenue.delhi.gov.in/revenue/income-certificate" },
    ],
  };

  const pack = {
    pack_version: "1.0.0",
    service_slug: "delhi-income-certificate",
    guidance: {
      what_it_is:
        "An income certificate is issued by the Revenue Department, Government of NCT of Delhi, certifying income from all sources. It is commonly requested for scholarships, fee concessions, and welfare schemes.",
      eligibility_notes: [
        "Apply through e-District Delhi only if the official service accepts your Delhi residence and circumstances.",
        "The certificate is issued by the competent Revenue Department authority after its own verification.",
      ],
      official_channel_steps: [
        "Register on edistrict.delhigovt.nic.in with your mobile number.",
        "Select the Revenue Department and the Income Certificate service.",
        "Fill the online form and upload self-attested supporting documents.",
        "Review, make the official declaration, and submit the application yourself.",
        "Save the application number and use the official portal to track status.",
      ],
      not_a_submission_notice:
        "RINAVI prepares this draft for your review only. RINAVI does not submit applications, make declarations on your behalf, or guarantee acceptance, approval, or processing time. You must review, sign, and submit through the official channel yourself.",
    },
    checklist_groups: [
      { id: "identity_proof", label: "Identity proof", requirement: "at_least_one", accepted_classifications: ["identity"] },
      { id: "residence_proof", label: "Residence proof", requirement: "at_least_one", accepted_classifications: [] },
      { id: "income_evidence", label: "Income evidence", requirement: "at_least_one", accepted_classifications: ["income"] },
      { id: "photograph", label: "Photograph", requirement: "optional", accepted_classifications: [] },
    ],
    form_template: {
      fields: [
        { id: "applicant_name", label: "Applicant name", binding: "full_name", required: true, format: "text" },
        { id: "father_or_husband_name", label: "Father's / husband's name", binding: "father_name", required: true, format: "text" },
        { id: "date_of_birth", label: "Date of birth", binding: "date_of_birth", required: true, format: "date" },
        { id: "gender", label: "Gender", binding: "gender", required: false, format: "text" },
        { id: "residence_address", label: "Residence address", binding: "address", required: true, format: "text" },
        { id: "annual_income", label: "Annual income (INR)", binding: "annual_income", required: true, format: "numeric" },
        { id: "occupation", label: "Occupation", binding: null, required: false, format: "text" },
        { id: "purpose", label: "Purpose of certificate", binding: null, required: true, format: "text" },
      ],
      declaration: {
        required: true,
        text: "I declare that the particulars given in this application are true and complete to the best of my knowledge and belief. I understand that providing false information may lead to rejection of the application and action under applicable law.",
      },
    },
  };

  // The backend adds these to every packet snapshot (backend/app/modules/applications/service.py).
  const PORTAL_DOWN_GUIDANCE =
    "If the portal is unavailable, nothing here changes. Your packet stays in the locker. Try the official channel again later — RINAVI does not submit on your behalf.";
  const ACKNOWLEDGEMENT_GUIDANCE =
    "No acknowledgement yet? Some portals send receipts later. Check your SMS and email, then look up your application on the official portal.";

  R.catalog = {
    services: [service],
    packs: { "delhi-income-certificate": pack },
    PORTAL_DOWN_GUIDANCE,
    ACKNOWLEDGEMENT_GUIDANCE,
  };

  // Colour is information: one hue per kind of evidence, used everywhere.
  R.HUE = {
    group: { identity_proof: "h-lav", residence_proof: "h-peach", income_evidence: "h-mint", photograph: "h-sky" },
    classification: { identity: "h-lav", income: "h-mint", residence: "h-peach", unsupported: "h-neutral" },
    docStatus: { processed: "h-mint", needs_attention: "h-rose", processing: "h-sky", quarantined: "h-sky" },
    profileStatus: { unconfirmed: "h-butter", confirmed: "h-mint", stale: "h-rose" },
    caseStatus: {
      prepared: "h-lav",
      submitted: "h-sky",
      acknowledged: "h-mint",
      outcome_received: "h-mint",
      abandoned: "h-neutral",
      uncertain: "h-butter",
    },
    purpose: {
      "documents.processing": "h-lav",
      "profile.storage": "h-mint",
      "applications.preparation": "h-peach",
      "locker.tracking": "h-sky",
    },
  };

  R.LABELS = {
    field: {
      full_name: "Full name",
      father_name: "Father's name",
      date_of_birth: "Date of birth",
      gender: "Gender",
      address: "Address",
      annual_income: "Annual income",
    },
    classification: { identity: "Identity", income: "Income", residence: "Residence", unsupported: "Not recognised" },
    docStatus: { processed: "Ready", needs_attention: "Needs attention", processing: "Processing", quarantined: "Queued" },
    profileStatus: { unconfirmed: "Needs review", confirmed: "Confirmed", stale: "Needs re-check" },
    caseStatus: {
      prepared: "Prepared",
      submitted: "Submitted",
      acknowledged: "Acknowledged",
      outcome_received: "Outcome received",
      abandoned: "Abandoned",
      uncertain: "Uncertain",
    },
    requirement: { at_least_one: "At least one needed", optional: "Optional" },
    note: {
      ocr_not_configured: "Images wait for text recognition, which isn't available yet.",
      pdf_not_read_in_demo: "This demo reads text files only. Use a .txt file, or the full app for PDFs.",
      no_fields_detected: "No fields were found. Each line should look like “Name: …”.",
      empty_file: "The file is empty.",
      not_text: "That file isn't readable as text.",
    },
    purpose: {
      "documents.processing": {
        label: "Document processing",
        description: "Reading a document you upload so its fields can be extracted.",
      },
      "profile.storage": {
        label: "Profile storage",
        description: "Keeping those values in your profile so you can review them.",
      },
      "applications.preparation": {
        label: "Application preparation",
        description: "Filling an application draft from your profile and documents.",
      },
      "locker.tracking": {
        label: "Application tracking",
        description: "Recording what happened to an application you filed yourself.",
      },
    },
  };

  R.SAMPLES = [
    {
      key: "identity",
      title: "Identity card",
      hue: "h-lav",
      filename: "identity-card-sample.txt",
      text: [
        "SAMPLE DOCUMENT (synthetic data, not a real ID)",
        "Name: Asha Verma",
        "Father's name: Rakesh Verma",
        "Date of birth: 12/03/1994",
        "Gender: Female",
        "Aadhaar number: 0000 0000 0000",
        "",
      ].join("\n"),
    },
    {
      key: "income",
      title: "Income statement",
      hue: "h-mint",
      filename: "income-statement-sample.txt",
      text: [
        "SAMPLE DOCUMENT (synthetic data, not a real statement)",
        "Name: Asha Verma",
        "Employer: Sample Traders Pvt Ltd",
        "Period: April 2025 to March 2026",
        "Annual income: Rs 2,40,000",
        "",
      ].join("\n"),
    },
    {
      key: "residence",
      title: "Address proof",
      hue: "h-peach",
      filename: "address-proof-sample.txt",
      text: [
        "SAMPLE DOCUMENT (synthetic data, not a real bill)",
        "Name: Asha Verma",
        "Address: 14 Sample Lane, Rohini, Delhi 110085",
        "Document: Sample electricity bill",
        "",
      ].join("\n"),
    },
  ];
})();
