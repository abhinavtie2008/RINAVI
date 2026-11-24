import { AccountPage } from "@/features/account/AccountPage";

export default function AccountRoute() {
  return (
    <main className="flex min-h-screen flex-col items-center gap-6 py-12">
      <h1 className="text-2xl font-semibold">Your data</h1>
      <AccountPage />
    </main>
  );
}
