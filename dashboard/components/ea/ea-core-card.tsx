import { StatusPill } from "@/components/ui/status-pill";

export function EACoreCard() {
  return (
    <section className="glass glow-border relative overflow-hidden rounded-4xl p-6 sm:p-8">
      <div className="absolute -right-20 -top-20 h-52 w-52 rounded-full bg-sky-400/10 blur-3xl" />
      <div className="absolute -bottom-24 left-1/2 h-48 w-48 -translate-x-1/2 rounded-full bg-blue-600/10 blur-3xl" />

      <div className="relative flex flex-col items-center text-center">
        <StatusPill label="Running" tone="green" />
        <p className="mt-5 text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">AI Basket EA</p>
        <h1 className="mt-2 text-4xl font-black tracking-tight text-white sm:text-5xl">EA</h1>
        <p className="mt-3 text-sm text-slate-400">XAUUSD.m <span className="mx-2 text-slate-600">•</span> M5 <span className="mx-2 text-slate-600">•</span> v1.31</p>

        <div className="mt-8 flex h-44 w-44 items-center justify-center rounded-full border border-sky-400/25 bg-slate-950/70 shadow-[0_0_50px_rgba(14,165,233,0.12)]">
          <div className="flex h-32 w-32 flex-col items-center justify-center rounded-full border border-sky-400/15 bg-sky-400/4">
            <span className="text-xs uppercase tracking-[0.22em] text-slate-500">Basket</span>
            <span className="mt-2 text-2xl font-bold text-white">FLAT</span>
          </div>
        </div>

        <div className="mt-7 grid w-full grid-cols-3 gap-2">
          {[
            ["START", "Start EA"],
            ["PAUSE", "Pause EA"],
            ["RESUME", "Resume EA"]
          ].map(([label, aria]) => (
            <button
              key={label}
              type="button"
              aria-label={aria}
              className="rounded-2xl border border-sky-400/20 bg-slate-900/75 px-2 py-3 text-[11px] font-bold tracking-[0.18em] text-sky-200 transition hover:border-sky-300/40 hover:bg-sky-400/10 active:scale-[0.98]"
            >
              {label}
            </button>
          ))}
        </div>

        <p className="mt-4 text-[11px] text-slate-600">Controls will connect to FastAPI in the next milestone.</p>
      </div>
    </section>
  );
}
