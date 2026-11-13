import { Suspense } from "react";

import { DraftDetail } from "@/features/applications/DraftDetail";

async function DraftPageContent({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <DraftDetail draftId={id} />;
}

export default function DraftPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return (
    <Suspense fallback={<p>Loading…</p>}>
      <DraftPageContent params={params} />
    </Suspense>
  );
}
