"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { getAuth, logout } from "@/lib/auth";
import { useRouter } from "next/navigation";

const navLinks = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/onboard", label: "Onboard" },
];

export default function TopNav() {
  const pathname = usePathname();
  const auth = getAuth();
  const router = useRouter();

  return (
    <nav className="fixed top-0 w-full bg-surface-container border-b border-outline z-50">
      <div className="flex justify-between items-center w-full px-8 py-3 max-w-full mx-auto">
        <div className="flex items-center gap-12">
          <Link
            href="/dashboard"
            className="text-xl font-bold tracking-tighter text-primary font-headline"
          >
            NIYOG
          </Link>
          <div className="hidden md:flex gap-8 items-center">
            {navLinks.map((link) => {
              const isActive = pathname.startsWith(link.href);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`pb-1 font-headline text-sm font-medium tracking-tight transition-colors duration-200 ${
                    isActive
                      ? "text-primary border-b-2 border-primary"
                      : "text-on-surface-variant hover:text-primary"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>
        </div>
        <div className="flex items-center gap-4">
          {auth && (
            <span className="text-sm text-on-surface-variant font-body">
              {auth.name}
            </span>
          )}
          <button
            onClick={() => {
              logout();
              router.push("/login");
            }}
            className="text-sm text-on-surface-variant hover:text-primary font-headline font-medium transition-colors duration-200"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}
