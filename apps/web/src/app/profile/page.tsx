import { ProfilePage } from "@/features/profile/ProfilePage";

export default function ProfileRoute() {
  return (
    <main className="flex min-h-screen flex-col items-center gap-6 py-12">
      <h1 className="text-2xl font-semibold">Your profile</h1>
      <ProfilePage />
    </main>
  );
}
