import { Suspense } from "react";

import { PacketPage } from "@/features/locker/PacketPage";

export default function PacketRoute({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return (
    <Suspense fallback={<p>Loading…</p>}>
      {params.then(({ id }) => (
        <PacketPage caseId={id} />
      ))}
    </Suspense>
  );
}
