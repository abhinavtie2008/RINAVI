import { Suspense } from "react";

import { PacketPage } from "@/features/locker/PacketPage";

async function PacketPageContent({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <PacketPage caseId={id} />;
}

export default function PacketRoute({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return (
    <Suspense fallback={<p>Loading…</p>}>
      <PacketPageContent params={params} />
    </Suspense>
  );
}
