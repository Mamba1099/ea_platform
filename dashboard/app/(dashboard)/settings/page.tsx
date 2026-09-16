"use client";

import { useState } from "react";
import {
  Check,
  Database,
  LogOut,
  Moon,
  RefreshCw,
  Sun,
  Trash2,
} from "lucide-react";
import { signOut } from "next-auth/react";
import { useQueryClient } from "@tanstack/react-query";

export default function SettingsPage() {
  const queryClient = useQueryClient();

  const [cacheCleared, setCacheCleared] = useState(false);

  function clearDashboardCache() {
    queryClient.clear();

    try {
      sessionStorage.clear();
      localStorage.removeItem("ea-platform-cache");
      localStorage.removeItem("ea-platform-state");
    } catch {
      // Ignore storage errors (private mode, quota, etc.)
    }

    setCacheCleared(true);

    window.setTimeout(() => {
      setCacheCleared(false);
    }, 2500);
  }

  async function handleSignOut() {
    await signOut({
      callbackUrl: "/login",
    });
  }

  return (
    // CHANGED: min-h-dvh instead of min-h-screen — dvh accounts for the
    // mobile browser address bar, so the page never gets clipped at the bottom.
    // Also added overflow-x-hidden and safe-area-aware bottom padding.
    <main
      className="min-h-dvh w-full overflow-x-hidden px-4 pt-6 sm:px-6"
      style={{
        paddingBottom: "calc(8rem + env(safe-area-inset-bottom, 0px))",
      }}
    >
      <div className="mx-auto w-full max-w-3xl space-y-6">
        {/* Header */}
        <section>
          <p className="text-xs uppercase tracking-[0.35em] text-sky-400">
            Platform
          </p>

          {/* CHANGED: smaller on mobile, larger on desktop */}
          <h1 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">
            Settings
          </h1>

          <p className="mt-1 text-sm leading-5 text-white/45 sm:text-white/40">
            Manage dashboard preferences and local application data.
          </p>
        </section>

        {/* Appearance */}
        <section className="overflow-hidden rounded-3xl border border-white/10 bg-white/3">
          <div className="border-b border-white/10 px-5 py-4">
            {/* CHANGED: items-start + icon nudge so it aligns with the title */}
            <div className="flex items-start gap-3">
              <Sun size={18} className="mt-0.5 shrink-0 text-sky-400" />

              <div className="min-w-0">
                <h2 className="font-medium">Appearance</h2>

                <p className="mt-1 text-xs leading-5 text-white/45 sm:text-white/30">
                  Dashboard theme preferences.
                </p>
              </div>
            </div>
          </div>

          <div className="grid gap-3 p-5 sm:grid-cols-3">
            <button
              type="button"
              className="flex items-center justify-center gap-2 rounded-2xl border border-sky-400/20 bg-sky-400/10 px-4 py-3 text-sm text-sky-300 transition active:scale-[0.98] active:bg-sky-400/15 focus-visible:outline focus-visible:outline-offset-2 focus-visible:outline-sky-400"
            >
              <Moon size={16} />
              Dark
            </button>

            <button
              type="button"
              disabled
              className="flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/40 sm:text-white/30"
            >
              <Sun size={16} />
              Light
              <span className="text-[10px] uppercase tracking-wider">Soon</span>
            </button>

            <button
              type="button"
              disabled
              className="flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/40 sm:text-white/30"
            >
              System
              <span className="text-[10px] uppercase tracking-wider">Soon</span>
            </button>
          </div>
        </section>

        {/* Cache */}
        <section className="overflow-hidden rounded-3xl border border-white/10 bg-white/3">
          <div className="border-b border-white/10 px-5 py-4">
            {/* CHANGED: items-start + icon nudge */}
            <div className="flex items-start gap-3">
              <Database size={18} className="mt-0.5 shrink-0 text-sky-400" />

              <div className="min-w-0">
                <h2 className="font-medium">Dashboard Cache</h2>

                <p className="mt-1 text-xs leading-5 text-white/45 sm:text-white/30">
                  Clear locally cached dashboard data. This does not delete EA
                  data, trading history, deployments, or database records.
                </p>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <p className="text-sm font-medium">Clear cached data</p>

              <p className="mt-1 text-xs leading-5 text-white/45 sm:text-white/30">
                TanStack Query and browser-side application cache.
              </p>
            </div>

            {/* CHANGED: active state + focus ring */}
            <button
              type="button"
              onClick={clearDashboardCache}
              className={`inline-flex shrink-0 items-center justify-center gap-2 rounded-2xl border px-4 py-3 text-sm font-medium transition active:scale-[0.98] focus-visible:outline focus-visible:outline-offset-2 focus-visible:outline-sky-400 ${
                cacheCleared
                  ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-300"
                  : "border-white/10 bg-white/5 text-white/70 hover:bg-white/10 active:bg-white/15"
              }`}
            >
              {cacheCleared ? (
                <>
                  <Check size={16} />
                  Cleared
                </>
              ) : (
                <>
                  <Trash2 size={16} />
                  Clear Cache
                </>
              )}
            </button>
          </div>
        </section>

        {/* Refresh */}
        <section className="overflow-hidden rounded-3xl border border-white/10 bg-white/3 p-5">
          <div className="flex items-start gap-3">
            <RefreshCw size={18} className="mt-0.5 shrink-0 text-sky-400" />

            <div className="min-w-0">
              <h2 className="font-medium">Live Data</h2>

              <p className="mt-2 text-xs leading-5 text-white/45 sm:text-white/30">
                EA telemetry is refreshed automatically while the dashboard is
                open.
              </p>
            </div>
          </div>
        </section>

        {/* Sign out */}
        <section className="overflow-hidden rounded-3xl border border-red-400/20 bg-red-400/5 p-5">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <h2 className="font-medium">Sign out</h2>

              <p className="mt-1 text-xs leading-5 text-white/45 sm:text-white/30">
                End your current administrator session.
              </p>
            </div>

            {/* CHANGED: active state + focus ring */}
            <button
              type="button"
              onClick={handleSignOut}
              className="inline-flex shrink-0 items-center justify-center gap-2 rounded-2xl border border-red-400/20 bg-red-400/5 px-4 py-3 text-sm font-medium text-red-300 transition hover:bg-red-400/10 active:scale-[0.98] active:bg-red-400/20 focus-visible:outline focus-visible:outline-offset-2 focus-visible:outline-red-400"
            >
              <LogOut size={16} />
              Sign Out
            </button>
          </div>
        </section>
      </div>
    </main>
  );
}
