"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Circle,
  RefreshCw,
  Terminal,
  XCircle,
} from "lucide-react";

import { getEAEvents } from "@/lib/api";
import type { EAEvent } from "@/lib/types";

function formatTime(value?: string | null) {
  if (!value) return "--:--:--";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "--:--:--";
  }

  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(date);
}

function formatDate(value?: string | null) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
  }).format(date);
}

function eventLevel(type: string) {
  const normalized = type.toUpperCase();

  if (normalized.includes("ERROR") || normalized.includes("FAIL")) {
    return "ERROR";
  }

  if (
    normalized.includes("PAUSE") ||
    normalized.includes("STOP") ||
    normalized.includes("WARN")
  ) {
    return "WARN";
  }

  if (
    normalized.includes("START") ||
    normalized.includes("RESUME") ||
    normalized.includes("RUN")
  ) {
    return "INFO";
  }

  return "INFO";
}

function eventClass(level: string) {
  switch (level) {
    case "ERROR":
      return "text-red-400";

    case "WARN":
      return "text-amber-400";

    default:
      return "text-emerald-400";
  }
}

function eventIcon(type: string) {
  const normalized = type.toUpperCase();

  if (normalized.includes("ERROR") || normalized.includes("FAIL")) {
    return <XCircle size={13} />;
  }

  if (
    normalized.includes("START") ||
    normalized.includes("RESUME") ||
    normalized.includes("RUN")
  ) {
    return <CheckCircle2 size={13} />;
  }

  if (normalized.includes("PAUSE") || normalized.includes("STOP")) {
    return <Circle size={13} />;
  }

  return <Activity size={13} />;
}

function eventTitle(event: EAEvent) {
  return event.event_type.replaceAll("_", " ");
}

export default function HistoryPage() {
  const [events, setEvents] = useState<EAEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  async function loadHistory(initial = false) {
    try {
      if (initial) {
        setLoading(true);
      } else {
        setRefreshing(true);
      }

      setError("");

      const eventResponse = await getEAEvents();

      setEvents(eventResponse.events ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load history.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadHistory(true);
  }, []);

  if (loading) {
    return (
      <main
        className="min-h-dvh w-full overflow-x-hidden px-3 pt-5 sm:px-6 sm:pt-6"
        style={{
          paddingBottom: "calc(8rem + env(safe-area-inset-bottom, 0px))",
        }}
      >
        <div className="mx-auto w-full max-w-6xl">
          <div className="w-full animate-pulse overflow-hidden rounded-3xl border border-white/10 bg-black/40 p-4 sm:p-6">
            <div className="h-3 w-20 rounded bg-white/10" />
            <div className="mt-4 h-8 w-40 rounded bg-white/10" />

            <div className="mt-7 h-105 rounded-2xl bg-white/5" />
          </div>
        </div>
      </main>
    );
  }

  return (
    <main
      className="min-h-dvh w-full overflow-x-hidden px-3 pt-6 sm:px-6 sm:pt-12"
      style={{
        paddingBottom: "calc(8rem + env(safe-area-inset-bottom, 0px))",
      }}
    >
      <div className="mx-auto w-full max-w-6xl min-w-0 space-y-5 sm:space-y-6">
        {/* Header */}
        <section className="flex min-w-0 items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <p className="text-[10px] uppercase tracking-[0.28em] text-sky-400 sm:text-xs sm:tracking-[0.35em]">
              Activity
            </p>

            <h1 className="mt-2 truncate text-2xl font-semibold tracking-tight sm:text-3xl">
              History
            </h1>

            <p className="mt-1 max-w-xl text-sm leading-5 text-white/45">
              Trade activity and AI_BASKET_EA lifecycle activity.
            </p>
          </div>

          <button
            type="button"
            aria-label="Refresh history"
            onClick={() => void loadHistory()}
            disabled={refreshing}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-white/10 bg-white/5 text-white/60 transition hover:bg-white/10 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline focus-visible:outline-offset-2 focus-visible:outline-sky-400"
          >
            <RefreshCw size={17} className={refreshing ? "animate-spin" : ""} />
          </button>
        </section>

        {/* Error */}
        {error && (
          <section className="w-full min-w-0 overflow-hidden rounded-2xl border border-red-400/20 bg-red-400/5 px-4 py-3 text-sm leading-5 text-red-300">
            <p className="wrap-break-word">{error}</p>
          </section>
        )}

        {/* EA Lifecycle Terminal */}
        <section className="overflow-hidden rounded-3xl border border-white/10 bg-black/50 shadow-2xl shadow-black/30">
          {/* Terminal header */}
          <div className="flex items-center justify-between border-b border-white/10 bg-white/3 px-4 py-3 sm:px-5">
            <div className="flex min-w-0 items-center gap-2">
              <Terminal size={16} className="shrink-0 text-sky-400" />

              <h2 className="truncate font-mono text-sm font-medium tracking-wide">
                AI_BASKET_EA / TERMINAL
              </h2>
            </div>

            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.55)]" />

              <span className="hidden text-[10px] uppercase tracking-widest text-white/25 sm:inline">
                activity
              </span>
            </div>
          </div>

          {/* Terminal controls bar */}
          <div className="flex items-center gap-4 overflow-x-auto border-b border-white/5 bg-black/70 px-4 py-2 font-mono text-[10px] whitespace-nowrap text-white/20 sm:px-5">
            <span>EVENTS {events.length}</span>

            <span className="text-white/10">|</span>

            <span>DATE {formatDate(events[0]?.created_at)}</span>
          </div>

          {/* Terminal body — FIXED HEIGHT + INTERNAL SCROLL */}
          <div
            className="h-[55dvh] max-h-140 min-h-80 overflow-auto overscroll-contain bg-[#050505] p-3 sm:p-5"
            tabIndex={0}
          >
            {events.length === 0 ? (
              <div className="px-1 py-6 font-mono text-xs leading-6 text-white/25">
                <div>$ ea activity</div>

                <div className="mt-4">No lifecycle events recorded.</div>

                <div className="mt-8">$ _</div>
              </div>
            ) : (
              <div className="font-mono text-[11px] leading-6 sm:text-xs">
                <div className="mb-4 text-white/20">$ ea activity --follow</div>

                {[...events]
                  .sort(
                    (a, b) =>
                      new Date(a.created_at).getTime() -
                      new Date(b.created_at).getTime(),
                  )
                  .map((event) => {
                    const level = eventLevel(event.event_type);
                    const levelClass = eventClass(level);

                    return (
                      <div
                        key={event.id}
                        className="border-b border-white/2.5 py-2.5 sm:grid sm:grid-cols-[76px_58px_minmax(200px,auto)_1fr] sm:gap-2 sm:py-1.5"
                      >
                        {/* Time + Level — same row on mobile, separate grid cells on desktop */}
                        <div className="flex items-center gap-3 sm:contents">
                          <span className="text-white/25">
                            {formatTime(event.created_at)}
                          </span>

                          <span
                            className={`flex items-center gap-1.5 ${levelClass}`}
                          >
                            {eventIcon(event.event_type)}
                            {level}
                          </span>
                        </div>

                        {/* Event title */}
                        <span className="mt-1 block wrap-break-word uppercase tracking-wide text-white/75 sm:mt-0 sm:inline">
                          {eventTitle(event)}
                        </span>

                        {/* Message */}
                        <span className="mt-0.5 block wrap-break-word text-white/40 sm:mt-0 sm:inline sm:text-white/35">
                          {event.message || ""}
                        </span>
                      </div>
                    );
                  })}

                <div className="mt-5 text-white/20">$ _</div>
              </div>
            )}
          </div>
        </section>

        {/* Footer note */}
        <section className="rounded-3xl border border-white/10 bg-white/3 p-4 sm:p-5">
          <div className="flex min-w-0 items-start gap-3">
            <AlertTriangle
              size={17}
              className="mt-0.5 shrink-0 text-amber-400/80"
            />

            <p className="min-w-0 wrap-break-word text-sm leading-6 text-white/40">
              The terminal shows recorded EA lifecycle activity. It does not
              represent every EA heartbeat or every raw MetaTrader terminal log
              line.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
