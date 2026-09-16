"use client";

import {
  Activity,
  Bot,
  CircleCheck,
  CircleX,
  Server,
  ExternalLink,
} from "lucide-react";
import Link from "next/link";
import { useEA } from "@/hooks/use-ea";

function statusLabel(status?: string | null) {
  if (!status) return "OFFLINE";
  return status.replaceAll("_", " ");
}

export default function HomePage() {
  const { data, isLoading, isFetching, error } = useEA();

  if (isLoading && !data) {
    return (
      <main className="min-h-screen px-4 pb-28 pt-6 sm:px-6">
        <div className="mx-auto max-w-6xl">
          <div className="animate-pulse rounded-4xl border border-white/10 bg-white/3 p-8">
            <div className="h-4 w-40 rounded bg-white/10" />
            <div className="mt-4 h-10 w-64 rounded bg-white/10" />

            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[1, 2, 3, 4].map((item) => (
                <div key={item} className="h-36 rounded-3xl bg-white/3" />
              ))}
            </div>
          </div>
        </div>
      </main>
    );
  }

  const ea = data?.ea;
  const basket = ea?.basket;
  const health = data?.health;
  const mt5 = data?.mt5;
  const registry = data?.registry;

  const hasError = !!error;
  const isHealthy = health?.healthy === true;

  return (
    <main className="min-h-screen px-4 pb-28 pt-6 sm:px-6">
      <div className="mx-auto max-w-6xl space-y-6">
        {/* Header */}
        <section className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-sky-400">
              Platform Overview
            </p>

            <h1 className="mt-2 text-3xl font-semibold tracking-tight">
              Welcome back
            </h1>

            <p className="mt-1 text-sm text-white/40">
              Monitor your trading platform from one place.
            </p>
          </div>

          <div className="text-right">
            <p className="text-xs text-white/30">
              {isFetching ? "Updating..." : "Live"}
            </p>

            <p className="mt-1 text-xs text-white/20">
              {registry?.symbol ?? "XAUUSD.m"}
            </p>
          </div>
        </section>

        {/* Overview cards */}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* EA */}
          <div className="rounded-3xl border border-white/10 bg-white/3 p-5 transition hover:border-sky-400/20">
            <div className="flex items-center justify-between">
              <Bot className="text-sky-400" size={20} />

              <span
                className={`h-2.5 w-2.5 rounded-full ${
                  ea?.status === "RUNNING"
                    ? "bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.7)]"
                    : ea?.status === "PAUSED"
                      ? "bg-amber-400"
                      : "bg-white/20"
                }`}
              />
            </div>

            <p className="mt-4 text-sm text-white/40">EA</p>

            <p className="mt-1 text-xl font-semibold">
              {statusLabel(ea?.status)}
            </p>

            <p className="mt-1 text-xs text-white/25">
              {registry?.name ?? "AI Basket EA"}
            </p>
          </div>

          {/* MT5 */}
          <div className="rounded-3xl border border-white/10 bg-white/3 p-5 transition hover:border-sky-400/20">
            <div className="flex items-center justify-between">
              <Server className="text-sky-400" size={20} />

              <span
                className={`h-2.5 w-2.5 rounded-full ${
                  mt5?.running
                    ? "bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.7)]"
                    : "bg-white/20"
                }`}
              />
            </div>

            <p className="mt-4 text-sm text-white/40">MT5</p>

            <p className="mt-1 text-xl font-semibold">
              {mt5?.running ? "RUNNING" : "STOPPED"}
            </p>

            <p className="mt-1 text-xs text-white/25">PID {mt5?.pid ?? "—"}</p>
          </div>

          {/* Health */}
          <div className="rounded-3xl border border-white/10 bg-white/3 p-5 transition hover:border-sky-400/20">
            <div className="flex items-center justify-between">
              {isHealthy ? (
                <CircleCheck className="text-emerald-400" size={20} />
              ) : (
                <CircleX className="text-red-400" size={20} />
              )}

              <span
                className={`h-2.5 w-2.5 rounded-full ${
                  isHealthy ? "bg-emerald-400" : "bg-red-400"
                }`}
              />
            </div>

            <p className="mt-4 text-sm text-white/40">Health</p>

            <p className="mt-1 text-xl font-semibold">
              {hasError ? "ERROR" : isHealthy ? "HEALTHY" : "DEGRADED"}
            </p>

            <p className="mt-1 truncate text-xs text-white/25">
              {health?.message ?? "No health data"}
            </p>
          </div>

          {/* Positions */}
          <div className="rounded-3xl border border-white/10 bg-white/3 p-5 transition hover:border-sky-400/20">
            <Activity className="text-sky-400" size={20} />

            <p className="mt-4 text-sm text-white/40">Positions</p>

            <p className="mt-1 text-xl font-semibold">
              {basket?.positions ?? 0}
            </p>

            <p className="mt-1 text-xs text-white/25">
              {basket?.direction ?? "NONE"}
            </p>
          </div>
        </section>

        {/* Basket summary */}
        <section className="grid gap-4 lg:grid-cols-3">
          <div className="rounded-3xl border border-white/10 bg-white/3 p-6 lg:col-span-2">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm text-white/40">Basket</p>

                <p className="mt-2 text-2xl font-semibold">
                  {basket?.state ?? "NO BASKET"}
                </p>
              </div>

              <div className="text-right">
                <p className="text-xs text-white/30">Direction</p>

                <p className="mt-1 text-sm font-medium">
                  {basket?.direction ?? "NONE"}
                </p>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div>
                <p className="text-xs text-white/30">Floating P/L</p>
                <p className="mt-1 font-semibold">
                  {basket?.floating_pnl?.toFixed(2) ?? "—"}
                </p>
              </div>

              <div>
                <p className="text-xs text-white/30">Daily P/L</p>
                <p className="mt-1 font-semibold">
                  {basket?.daily_profit?.toFixed(2) ?? "—"}
                </p>
              </div>

              <div>
                <p className="text-xs text-white/30">Price</p>
                <p className="mt-1 font-semibold">
                  {basket?.current_price?.toFixed(2) ?? "—"}
                </p>
              </div>

              <div>
                <p className="text-xs text-white/30">ATR</p>
                <p className="mt-1 font-semibold">
                  {basket?.atr?.toFixed(2) ?? "—"}
                </p>
              </div>
            </div>
          </div>

          {/* Quick action */}
          <div className="rounded-3xl border border-sky-400/20 bg-sky-400/4 p-6">
            <p className="text-sm text-white/40">EA Control</p>

            <h2 className="mt-2 text-xl font-semibold">Manage AI Basket</h2>

            <p className="mt-2 text-sm leading-6 text-white/40">
              Open the dedicated EA control panel to start, pause, resume, or
              stop the expert.
            </p>

            <Link
              href="/ea"
              className="mt-6 inline-flex items-center gap-2 rounded-full bg-sky-500 px-5 py-3 text-sm font-medium text-black transition hover:bg-sky-400"
            >
              Open EA
              <ExternalLink size={15} />
            </Link>
          </div>
        </section>

        {/* Latest decision */}
        <section className="overflow-hidden rounded-3xl border border-emerald-400/15 bg-black/80 shadow-2xl shadow-black/20">
          {/* Terminal header */}
          <div className="flex items-center justify-between border-b border-white/10 bg-white/2 px-4 py-3 sm:px-5">
            <div className="flex min-w-0 items-center gap-3">
              <div className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-red-400/70" />
                <span className="h-2.5 w-2.5 rounded-full bg-amber-400/70" />
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/70" />
              </div>

              <div className="min-w-0">
                <p className="truncate font-mono text-[11px] uppercase tracking-wider text-white/40">
                  AI_BASKET_EA / DECISION_ENGINE
                </p>
              </div>
            </div>

            <span className="shrink-0 font-mono text-[10px] uppercase tracking-wider text-emerald-400/70">
              LIVE
            </span>
          </div>

          {/* Terminal body */}
          <div className="p-4 sm:p-5">
            <div className="font-mono text-xs leading-6 sm:text-sm">
              <div className="flex gap-2">
                <span className="select-none text-emerald-400">$</span>

                <span className="text-white/80">decision --latest</span>
              </div>

              <div className="mt-2 flex gap-2">
                <span className="select-none text-sky-400">&gt;</span>

                <span className="text-white/60">DECISION:</span>

                <span className="font-semibold text-emerald-300">
                  {basket?.last_decision ?? "WAIT"}
                </span>
              </div>

              <div className="flex gap-2">
                <span className="select-none text-sky-400">&gt;</span>

                <span className="text-white/60">REASON:</span>

                <span className="wrap-break-word text-white/75">
                  {basket?.last_reason ?? "No decision data available"}
                </span>
              </div>

              <div className="flex gap-2">
                <span className="select-none text-sky-400">&gt;</span>

                <span className="text-white/60">SPREAD:</span>

                <span className="text-white/75">
                  {basket?.spread?.toFixed(2) ?? "—"}
                </span>
              </div>

              <div className="flex gap-2">
                <span className="select-none text-sky-400">&gt;</span>

                <span className="text-white/60">ENGINE:</span>

                <span className="text-emerald-300">MONITORING</span>
              </div>

              <div className="mt-2 flex gap-2">
                <span className="select-none text-emerald-400">$</span>

                <span className="flex items-center text-white/50">
                  _
                  <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse bg-emerald-400/70" />
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* API error */}
        {error instanceof Error && (
          <section className="rounded-2xl border border-red-400/20 bg-red-400/5 px-4 py-3 text-sm text-red-300">
            {error.message}
          </section>
        )}
      </div>
    </main>
  );
}
