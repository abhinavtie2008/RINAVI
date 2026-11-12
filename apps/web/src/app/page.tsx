import { AppBanner } from "@/components/AppBanner";
import { SignInArea } from "@/features/auth/SignInArea";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6">
      <AppBanner />
      <SignInArea />
    </main>
  );
}
