import Link from "next/link";

import { AppBanner } from "@/components/AppBanner";
import { SignInArea } from "@/features/auth/SignInArea";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6">
      <AppBanner />
      <SignInArea />
      <nav className="flex gap-4 text-sm">
        <Link href="/vault" className="underline">
          Document vault
        </Link>
      </nav>
    </main>
  );
}
