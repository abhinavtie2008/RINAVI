import Link from "next/link";

export function SiteNav() {
  return (
    <nav aria-label="Main" className="flex gap-4 text-sm">
      <Link href="/applications" className="underline">
        Applications
      </Link>
      <Link href="/locker" className="underline">
        Locker
      </Link>
    </nav>
  );
}
