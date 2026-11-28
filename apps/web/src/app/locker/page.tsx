import type { Metadata } from "next";

import { CasesPage } from "@/features/locker/CasesPage";

export const metadata: Metadata = { title: "Case locker" };

export default function Locker() {
  return <CasesPage />;
}
