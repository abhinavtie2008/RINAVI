import { VaultPage } from "@/features/vault/VaultPage";

export default function VaultRoute() {
  return (
    <main className="flex min-h-screen flex-col items-center gap-6 py-12">
      <h1 className="text-2xl font-semibold">Document vault</h1>
      <VaultPage />
    </main>
  );
}
