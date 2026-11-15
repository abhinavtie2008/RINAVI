import { ConsentPage } from "@/features/consent/ConsentPage";

export default function ConsentRoute() {
  return (
    <main className="flex min-h-screen flex-col items-center gap-6 py-12">
      <h1 className="text-2xl font-semibold">Consent</h1>
      <ConsentPage />
    </main>
  );
}
