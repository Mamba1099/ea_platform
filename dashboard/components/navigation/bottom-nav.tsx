"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const tabs = [
  { href: "/", label: "Home", icon: "⌂" },
  { href: "/ea", label: "EA", icon: "◉", primary: true },
  { href: "/history", label: "History", icon: "≡" },
  { href: "/settings", label: "Settings", icon: "⚙" }
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-50 px-4 pb-4 sm:px-6">
      <div className="mx-auto flex max-w-2xl items-end justify-between rounded-3xl border border-sky-400/20 bg-slate-950/90 px-3 py-2 shadow-2xl shadow-sky-950/30 backdrop-blur-xl">
        {tabs.map((tab) => {
          const active = tab.href === "/" ? pathname === "/" : pathname.startsWith(tab.href);

          if (tab.primary) {
            return (
              <Link
                key={tab.href}
                href={tab.href}
                className="-mt-7 flex min-w-20 flex-col items-center gap-1"
              >
                <span className={`flex h-16 w-16 items-center justify-center rounded-full border text-xl shadow-lg transition ${
                  active
                    ? "border-sky-300 bg-sky-500/20 text-sky-300 shadow-sky-500/20"
                    : "border-sky-400/30 bg-slate-900 text-sky-200"
                }`}>
                  {tab.icon}
                </span>
                <span className={`text-[11px] font-semibold uppercase tracking-[0.18em] ${active ? "text-sky-300" : "text-slate-500"}`}>
                  {tab.label}
                </span>
              </Link>
            );
          }

          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`flex min-w-16 flex-col items-center gap-1 rounded-2xl px-2 py-2 text-[11px] uppercase tracking-[0.14em] transition ${
                active ? "text-sky-300" : "text-slate-500 hover:text-slate-300"
              }`}
            >
              <span className="text-lg leading-none">{tab.icon}</span>
              <span>{tab.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
