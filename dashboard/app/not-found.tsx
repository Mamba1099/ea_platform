import Link from "next/link";
import { ArrowLeft, SearchX } from "lucide-react";

export default function NotFound() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-black px-4">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_top,rgba(0,149,255,0.10),transparent_45%)]" />

      <div className="relative w-full max-w-md text-center">
        <div className="rounded-4xl border border-white/10 bg-white/3 p-10 shadow-2xl">
          <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full border border-white/10 bg-white/5">
            <SearchX size={30} className="text-white/50" />
          </div>

          <p className="mt-7 text-xs uppercase tracking-[0.35em] text-sky-400">
            EA Platform
          </p>

          <h1 className="mt-3 text-5xl font-semibold tracking-tight">404</h1>

          <h2 className="mt-3 text-xl font-medium">Page not found</h2>

          <p className="mt-3 text-sm leading-6 text-white/40">
            The page you are looking for does not exist or may have been moved.
          </p>

          <Link
            href="/"
            className="mt-8 inline-flex items-center gap-2 rounded-full border border-sky-400/30 bg-sky-400/10 px-5 py-3 text-sm font-medium text-sky-300 transition hover:bg-sky-400/20"
          >
            <ArrowLeft size={16} />
            Back to dashboard
          </Link>
        </div>
      </div>
    </main>
  );
}
