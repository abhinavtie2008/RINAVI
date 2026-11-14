import Link from "next/link";

import { AppBanner } from "@/components/AppBanner";
import { SignInArea } from "@/features/auth/SignInArea";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6">
      <AppBanner />
      <SignInArea />
      <nav className="flex gap-4 text-sm">
        <Link href="/catalog" className="underline">
          Services
        </Link>
        <Link href="/applications" className="underline">
          Applications
        </Link>
        <Link href="/locker" className="underline">
          Locker
        </Link>
        <Link href="/vault" className="underline">
          Document vault
        </Link>
        <Link href="/profile" className="underline">
          Your profile
        </Link>
      </nav>
    </main>
  );
}
