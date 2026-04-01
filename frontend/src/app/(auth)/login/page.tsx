"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const auth = await login(email, password);
      if (auth.role === "candidate") {
        router.push("/onboard");
      } else {
        router.push("/dashboard");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold tracking-tighter text-primary font-headline">
            NIYOG
          </h1>
          <p className="mt-2 text-on-surface-variant text-sm font-body">
            Sign in to your account
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-headline font-bold uppercase tracking-widest text-on-surface-variant mb-2">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="candidate@niyog.dev"
              required
              className="w-full px-4 py-3 bg-surface-container text-on-surface font-body text-sm rounded-lg border-none outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200 placeholder:text-on-surface-variant/40"
            />
          </div>

          <div>
            <label className="block text-xs font-headline font-bold uppercase tracking-widest text-on-surface-variant mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              required
              className="w-full px-4 py-3 bg-surface-container text-on-surface font-body text-sm rounded-lg border-none outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200 placeholder:text-on-surface-variant/40"
            />
          </div>

          {error && (
            <p className="text-error text-sm font-body">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-primary text-white font-headline font-bold text-sm uppercase tracking-wide rounded-lg hover:bg-primary-hover active:scale-[0.98] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-soft"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <div className="mt-8 p-4 bg-surface rounded-lg border border-outline">
          <p className="text-[11px] font-headline font-bold uppercase tracking-widest text-on-surface-variant mb-3">
            Demo accounts
          </p>
          <div className="space-y-1 text-xs font-body text-on-surface-variant">
            <p>candidate@niyog.dev / cand123</p>
            <p>hr@niyog.dev / hr123</p>
          </div>
        </div>
      </div>
    </div>
  );
}
