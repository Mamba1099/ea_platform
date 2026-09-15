"use client";

import { useEffect } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-black px-4">
      <div className="w-full max-w-md rounded-4xl border border-red-400/20 bg-white/3 p-10 text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full border border-red-400/20 bg-red-400/10">
          <AlertTriangle size={28} className="text-red-400" />
        </div>

        <h1 className="mt-6 text-2xl font-semibold">Something went wrong</h1>

        <p className="mt-3 text-sm text-white/40">
          The dashboard encountered an unexpected error.
        </p>

        <button
          type="button"
          onClick={() => reset()}
          className="mt-7 inline-flex items-center gap-2 rounded-full bg-white px-5 py-3 text-sm font-medium text-black transition hover:bg-white/90"
        >
          <RotateCcw size={16} />
          Try again
        </button>
      </div>
    </main>
  );
}
