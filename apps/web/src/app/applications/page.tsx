import type { Metadata } from "next";

import { ApplicationsPage } from "@/features/applications/ApplicationsPage";

export const metadata: Metadata = { title: "Applications" };

export default function Applications() {
  return <ApplicationsPage />;
}
