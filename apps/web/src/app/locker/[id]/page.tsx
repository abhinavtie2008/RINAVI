import { Suspense } from "react";

import { CaseDetail } from "@/features/locker/CaseDetail";

async function CasePageContent({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <CaseDetail caseId={id} />;
}

export default function CasePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return (
    <Suspense fallback={<p>Loading…</p>}>
      <CasePageContent params={params} />
    </Suspense>
  );
}
