import { Suspense } from "react";

import { CaseDetail } from "@/features/locker/CaseDetail";

export default function CasePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return (
    <Suspense fallback={<p>Loading…</p>}>
      {params.then(({ id }) => (
        <CaseDetail caseId={id} />
      ))}
    </Suspense>
  );
}
