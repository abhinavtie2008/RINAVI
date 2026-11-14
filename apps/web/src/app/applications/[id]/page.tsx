import { Suspense } from "react";

import { DraftDetail } from "@/features/applications/DraftDetail";

export default function DraftPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return (
    <Suspense fallback={<p>Loading…</p>}>
      {params.then(({ id }) => (
        <DraftDetail draftId={id} />
      ))}
    </Suspense>
  );
}
