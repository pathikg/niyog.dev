"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getAuth } from "@/lib/auth";

export default function Home() {
  const [authed, setAuthed] = useState<string | null>(null);

  useEffect(() => {
    const auth = getAuth();
    if (auth) setAuthed(auth.role);
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Nav */}
      <nav className="w-full px-8 py-4 flex justify-between items-center">
        <span className="text-xl font-bold tracking-tighter text-primary font-headline">
          NIYOG
        </span>
        <div className="flex items-center gap-4">
          {authed ? (
            <Link
              href={authed === "candidate" ? "/onboard" : "/dashboard"}
              className="px-5 py-2 bg-primary text-white font-headline font-bold text-sm rounded-lg hover:bg-primary-hover active:scale-[0.98] transition-all duration-200"
            >
              Go to Dashboard
            </Link>
          ) : (
            <Link
              href="/login"
              className="px-5 py-2 bg-primary text-white font-headline font-bold text-sm rounded-lg hover:bg-primary-hover active:scale-[0.98] transition-all duration-200"
            >
              Sign In
            </Link>
          )}
        </div>
      </nav>

      {/* Hero */}
      <main className="flex-1 flex items-center justify-center px-8">
        <div className="max-w-2xl text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-primary-container text-on-primary-container rounded-full text-xs font-headline font-bold uppercase tracking-widest mb-8">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
            Agentic Hiring Platform
          </div>

          <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight font-headline text-on-surface leading-tight mb-6">
            Hiring that actually{" "}
            <span className="text-primary">understands</span> people
          </h1>

          <p className="text-lg text-on-surface-variant font-body leading-relaxed mb-10 max-w-lg mx-auto">
            Upload your resume, chat with AI, and get matched to roles that fit.
            No forms. No black holes. Just conversations.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href={authed ? "/onboard" : "/login"}
              className="px-8 py-3.5 bg-primary text-white font-headline font-bold text-sm uppercase tracking-wide rounded-lg hover:bg-primary-hover active:scale-[0.98] transition-all duration-200 shadow-soft"
            >
              Get Started
            </Link>
            <a
              href="#how-it-works"
              className="px-8 py-3.5 bg-surface text-on-surface font-headline font-bold text-sm uppercase tracking-wide rounded-lg border border-outline hover:bg-surface-container active:scale-[0.98] transition-all duration-200"
            >
              How It Works
            </a>
          </div>
        </div>
      </main>

      {/* How it works */}
      <section id="how-it-works" className="px-8 py-20 bg-surface-container">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-sm font-headline font-bold uppercase tracking-widest text-on-surface-variant text-center mb-12">
            How It Works
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: "01",
                title: "Upload Resume",
                desc: "Drop your PDF and our AI reads it — skills, experience, education, everything extracted in seconds.",
              },
              {
                step: "02",
                title: "Chat & Refine",
                desc: "Review what we found, correct anything off, and fill in what your resume doesn't say — salary expectations, preferences, dealbreakers.",
              },
              {
                step: "03",
                title: "Get Matched",
                desc: "Your profile matches against open roles automatically. See why you fit, where gaps are, and which companies are interested.",
              },
            ].map((item) => (
              <div
                key={item.step}
                className="bg-surface rounded-xl p-8 shadow-card"
              >
                <span className="text-4xl font-extrabold font-headline text-outline">
                  {item.step}
                </span>
                <h3 className="text-lg font-bold font-headline text-on-surface mt-4 mb-2">
                  {item.title}
                </h3>
                <p className="text-sm text-on-surface-variant font-body leading-relaxed">
                  {item.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="w-full px-12 py-6 flex justify-between items-center border-t border-outline">
        <span className="font-headline font-bold text-on-surface">NIYOG</span>
        <span className="text-on-surface-variant text-sm font-body">
          &copy; {new Date().getFullYear()} Niyog
        </span>
      </footer>
    </div>
  );
}
