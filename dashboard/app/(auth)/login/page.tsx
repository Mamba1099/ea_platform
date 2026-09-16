import { Suspense } from "react";
import LoginForm from "@/components/login/login-form"

function LoginFallback() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-black px-4">
      <div className="w-full max-w-md">
        <div className="animate-pulse rounded-4xl border border-white/10 bg-white/3 p-8">
          <div className="mx-auto h-16 w-16 rounded-full bg-white/10" />
          <div className="mx-auto mt-6 h-3 w-24 rounded bg-white/10" />
          <div className="mx-auto mt-3 h-7 w-40 rounded bg-white/10" />

          <div className="mt-8 space-y-5">
            <div className="h-12 rounded-2xl bg-white/5" />
            <div className="h-12 rounded-2xl bg-white/5" />
            <div className="h-12 rounded-2xl bg-white/5" />
          </div>
        </div>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<LoginFallback />}>
      <LoginForm />
    </Suspense>
  );
}
