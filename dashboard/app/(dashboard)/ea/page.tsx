"use client";

import {
  Activity,
  CirclePause,
  Play,
  RotateCcw,
  Server,
  Square,
  Wifi,
} from "lucide-react";
import { useEA } from "@/hooks/use-ea";

function formatNumber(value: number | null | undefined, digits = 2) {
  if (value == null || !Number.isFinite(value)) return "—";
  return value.toFixed(digits);
}

function statusLabel(status?: string | null) {
  if (!status) return "OFFLINE";
  return status.replaceAll("_", " ");
}

function statusDotClass(status?: string | null) {
  switch (status) {
    case "RUNNING":
      return "bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,0.8)]";

    case "PAUSED":
      return "bg-amber-400 shadow-[0_0_12px_rgba(251,191,36,0.6)]";

    case "STARTING":
      return "bg-sky-400 shadow-[0_0_12px_rgba(56,189,248,0.6)]";

    case "STOPPING":
      return "bg-orange-400 shadow-[0_0_12px_rgba(251,146,60,0.6)]";

    case "ERROR":
      return "bg-red-400 shadow-[0_0_12px_rgba(248,113,113,0.7)]";

    default:
      return "bg-white/30";
  }
}

export default function EAPage() {
  const {
    data,
    isLoading,
    isFetching,
    error,
    refetch,
    start,
    pause,
    resume,
    stop,
  } = useEA();

  const anyMutationPending =
    start.isPending || pause.isPending || resume.isPending || stop.isPending;

  if (isLoading && !data) {
    return (
      <main
        className="min-h-dvh px-4 pt-6 sm:px-6"
        style={{
          paddingBottom: "calc(7rem + env(safe-area-inset-bottom, 0px))",
        }}
      >
        <div className="mx-auto max-w-6xl">
          <div className="animate-pulse rounded-4xl border border-white/10 bg-white/5 p-10">
            <div className="h-5 w-40 rounded bg-white/10" />
            <div className="mt-4 h-10 w-72 rounded bg-white/10" />
            <div className="mt-10 h-72 rounded-3xl bg-white/5" />
          </div>
        </div>
      </main>
    );
  }

  const registry = data?.registry;
  const ea = data?.ea;
  const basket = ea?.basket;
  const health = data?.health;
  const mt5 = data?.mt5;

  const eaStatus = ea?.status;

  const canStart =
    !anyMutationPending && eaStatus !== "RUNNING" && eaStatus !== "STARTING";

  const canPause = !anyMutationPending && eaStatus === "RUNNING";

  const canResume = !anyMutationPending && eaStatus === "PAUSED";

  const canStop =
    !anyMutationPending && eaStatus !== "STOPPED" && eaStatus !== "STOPPING";

  return (
    <main
      className="min-h-dvh px-4 pt-6 sm:px-6"
      style={{
        paddingBottom: "calc(7rem + env(safe-area-inset-bottom, 0px))",
      }}
    >
      <div className="mx-auto max-w-6xl space-y-6">
        {/* Header */}
        <section className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="text-xs uppercase tracking-[0.35em] text-sky-400">
              Expert Operations
            </p>

            <h1 className="mt-2 truncate text-2xl font-semibold tracking-tight sm:text-3xl">
              {registry?.name ?? "AI Basket EA"}
            </h1>

            <p className="mt-1 text-sm text-white/50">
              {registry?.symbol ?? "XAUUSD.m"} · v{registry?.version ?? "—"}
            </p>
          </div>

          <button
            type="button"
            onClick={() => void refetch()}
            disabled={isFetching}
            aria-label="Refresh"
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-white/10 bg-white/5 text-white/70 transition hover:bg-white/10 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline focus-visible:outline-offset-2 focus-visible:outline-sky-400"
          >
            <RotateCcw size={18} className={isFetching ? "animate-spin" : ""} />
          </button>
        </section>

        {/* Main EA card — image as background */}
        <section className="relative overflow-hidden rounded-4xl border border-sky-400/20 p-5 shadow-2xl shadow-sky-950/30 sm:p-8">
          {/* Background image */}
          <img
            src="/assets/image.jpeg"
            alt=""
            aria-hidden="true"
            className="absolute inset-0 h-full w-full object-fill"
          />

          <div className="absolute inset-0 bg-black/60 sm:bg-black/50" />

          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-2/3 bg-linear-to-t from-black via-black/90 to-transparent sm:h-1/2 sm:from-black/80 sm:via-black/40" />

          {/* Subtle sky glow */}
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(0,149,255,0.15),transparent_55%)]" />

          {/* Content */}
          <div className="relative flex flex-col items-center">
            {/* Status pill */}
            <div className="mb-5 flex items-center gap-2 rounded-full border border-sky-400/30 bg-black/70 px-4 py-2 text-xs uppercase tracking-widest text-white/90 backdrop-blur-md">
              <span
                className={`h-2.5 w-2.5 rounded-full ${statusDotClass(
                  eaStatus,
                )}`}
              />

              {statusLabel(eaStatus)}
            </div>

            {/* Basket */}
            <div className="mt-2 text-center text-2xl font-semibold text-white drop-shadow-[0_2px_8px_rgba(0,0,0,0.9)] sm:text-3xl">
              {basket?.state ?? "NO BASKET"}
            </div>

            <div className="mt-1 text-sm text-white/80 drop-shadow-[0_1px_4px_rgba(0,0,0,0.9)]">
              {basket?.direction ?? "NONE"}
            </div>

            {/* Controls — 2×2 grid on mobile, single row on desktop */}
            <div className="mt-7 grid w-full grid-cols-2 gap-2.5 sm:flex sm:w-auto sm:flex-wrap sm:justify-center sm:gap-3">
              <button
                type="button"
                disabled={!canStart}
                onClick={() => start.mutate()}
                className="flex items-center justify-center gap-2 rounded-full border border-sky-400/50 bg-linear-to-b from-slate-500/90 to-black px-4 py-3 text-sm font-medium text-white shadow-lg shadow-black/60 transition hover:border-sky-400/70 hover:from-slate-700 hover:to-black active:scale-95 disabled:cursor-not-allowed disabled:opacity-70 sm:px-5"
              >
                <Play size={16} />
                {start.isPending ? "Starting..." : "Start"}
              </button>

              <button
                type="button"
                disabled={!canPause}
                onClick={() => pause.mutate()}
                className="flex items-center justify-center gap-2 rounded-full border border-amber-400/50 bg-linear-to-b from-slate-900/95 to-black px-4 py-3 text-sm font-medium text-amber-300 shadow-lg shadow-black/60 transition hover:border-amber-400/70 hover:from-slate-800 hover:to-black active:scale-95 disabled:cursor-not-allowed disabled:opacity-70 sm:px-5"
              >
                <CirclePause size={16} />
                {pause.isPending ? "Pausing..." : "Pause"}
              </button>

              <button
                type="button"
                disabled={!canResume}
                onClick={() => resume.mutate()}
                className="flex items-center justify-center gap-2 rounded-full border border-emerald-400/50 bg-linear-to-b from-slate-800/90 to-black px-4 py-3 text-sm font-medium text-emerald-300 shadow-lg shadow-black/60 transition hover:border-emerald-400/70 hover:from-slate-800 hover:to-black active:scale-95 disabled:cursor-not-allowed disabled:opacity-70 sm:px-5"
              >
                <Play size={16} />
                {resume.isPending ? "Resuming..." : "Resume"}
              </button>

              <button
                type="button"
                disabled={!canStop}
                onClick={() => stop.mutate()}
                className="flex items-center justify-center gap-2 rounded-full border border-red-400/50 bg-linear-to-b from-slate-900/95 to-black px-4 py-3 text-sm font-medium text-red-300 shadow-lg shadow-black/60 transition hover:border-red-400/70 hover:from-slate-800 hover:to-black active:scale-95 disabled:cursor-not-allowed disabled:opacity-40 sm:px-5"
              >
                <Square size={15} />
                {stop.isPending ? "Stopping..." : "Stop"}
              </button>
            </div>
          </div>
        </section>

        {/* Telemetry */}
        <section className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {[
            ["Positions", basket?.positions ?? 0],
            ["Floating P/L", formatNumber(basket?.floating_pnl)],
            ["Daily P/L", formatNumber(basket?.daily_profit)],
            ["Price", formatNumber(basket?.current_price)],
            ["ATR", formatNumber(basket?.atr)],
            ["Spread", formatNumber(basket?.spread)],
          ].map(([label, value]) => (
            <div
              key={label}
              className="rounded-2xl border border-white/10 bg-white/3 p-4"
            >
              <p className="text-xs text-white/40">{label}</p>

              <p className="mt-2 text-lg font-semibold">{value}</p>
            </div>
          ))}
        </section>

        {/* Runtime information */}
        <section className="grid gap-4 md:grid-cols-2">
          <div className="rounded-3xl border border-white/10 bg-white/3 p-5">
            <div className="flex items-center gap-2">
              <Server size={18} className="text-sky-400" />
              <h2 className="font-medium">Terminal</h2>
            </div>

            <div className="mt-5 space-y-3 text-sm">
              <div className="flex justify-between gap-4">
                <span className="text-white/40">MT5</span>
                <span>{mt5?.running ? "Running" : "Stopped"}</span>
              </div>

              <div className="flex justify-between gap-4">
                <span className="text-white/40">PID</span>
                <span>{mt5?.pid ?? "—"}</span>
              </div>

              <div className="flex justify-between gap-4">
                <span className="text-white/40">Terminal connection</span>

                <span>
                  {ea?.terminal_connected ? "Connected" : "Disconnected"}
                </span>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-white/10 bg-white/3 p-5">
            <div className="flex items-center gap-2">
              <Wifi size={18} className="text-emerald-400" />
              <h2 className="font-medium">Health</h2>
            </div>

            <div className="mt-5 space-y-3 text-sm">
              <div className="flex justify-between gap-4">
                <span className="text-white/40">Status</span>
                <span>{health?.message ?? "Unknown"}</span>
              </div>

              <div className="flex justify-between gap-4">
                <span className="text-white/40">Telemetry age</span>
                <span>
                  {health ? `${health.file_age_seconds.toFixed(1)}s` : "—"}
                </span>
              </div>

              <div className="flex justify-between gap-4">
                <span className="text-white/40">Healthy</span>
                <span>{health?.healthy ? "Yes" : "No"}</span>
              </div>
            </div>
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

              <div className="flex min-w-0 items-center gap-2">
                <Activity size={15} className="shrink-0 text-sky-400" />

                <h2 className="truncate font-mono text-[11px] uppercase tracking-wider text-white/50 sm:text-xs">
                  AI_BASKET_EA / DECISION_ENGINE
                </h2>
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

                <span className="text-white/80">ea decision --inspect</span>
              </div>

              <div className="mt-2 flex gap-2">
                <span className="select-none text-sky-400">&gt;</span>

                <span className="text-white/60">DECISION:</span>

                <span className="font-semibold text-emerald-300">
                  {basket?.last_decision ?? "WAIT"}
                </span>
              </div>

              <div className="flex items-start gap-2">
                <span className="select-none text-sky-400">&gt;</span>

                <span className="shrink-0 text-white/60">REASON:</span>

                <span className="min-w-0 wrap-break-word text-white/75">
                  {basket?.last_reason ?? "No decision available"}
                </span>
              </div>

              <div className="flex gap-2">
                <span className="select-none text-sky-400">&gt;</span>

                <span className="text-white/60">PRICE:</span>

                <span className="text-white/75">
                  {basket?.current_price?.toFixed(2) ?? "—"}
                </span>
              </div>

              <div className="flex gap-2">
                <span className="select-none text-sky-400">&gt;</span>

                <span className="text-white/60">ATR:</span>

                <span className="text-white/75">
                  {basket?.atr?.toFixed(2) ?? "—"}
                </span>
              </div>

              <div className="flex gap-2">
                <span className="select-none text-sky-400">&gt;</span>

                <span className="text-white/60">SPREAD:</span>

                <span className="text-white/75">
                  {basket?.spread?.toFixed(2) ?? "—"}
                </span>
              </div>

              <div className="mt-1 flex gap-2">
                <span className="select-none text-sky-400">&gt;</span>

                <span className="text-white/60">BASKET:</span>

                <span className="text-white/75">
                  {basket?.state ?? "NO BASKET"}
                </span>
              </div>

              <div className="mt-2 flex gap-2">
                <span className="select-none text-emerald-400">$</span>

                <span className="text-white/50">_</span>

                <span className="inline-block h-4 w-1.5 animate-pulse bg-emerald-400/70" />
              </div>
            </div>
          </div>
        </section>

        {/* API error */}
        {error instanceof Error && (
          <div className="rounded-2xl border border-red-400/20 bg-red-400/5 px-4 py-3 text-sm text-red-300">
            {error.message}
          </div>
        )}

        {/* Mutation error */}
        {[start, pause, resume, stop].some((mutation) => mutation.isError) && (
          <div className="rounded-2xl border border-red-400/20 bg-red-400/5 px-4 py-3 text-sm text-red-300">
            An EA control command failed. Check the EA status and try again.
          </div>
        )}
      </div>
    </main>
  );
}
