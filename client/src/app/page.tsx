"use client";

import Link from "next/link";

const wealthBars = [24, 31, 38, 46, 52, 61, 68, 76, 86, 94];

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-[#05070b] text-white">
      {/* Ambient background */}
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute left-1/2 top-[-18rem] h-[34rem] w-[34rem] -translate-x-1/2 rounded-full bg-emerald-400/[0.08] blur-[120px]" />
        <div className="absolute right-[-12rem] top-[28rem] h-[30rem] w-[30rem] rounded-full bg-cyan-400/[0.05] blur-[120px]" />
        <div className="absolute bottom-[-14rem] left-[-10rem] h-[28rem] w-[28rem] rounded-full bg-teal-400/[0.05] blur-[120px]" />
        <div
          className="absolute inset-0 opacity-[0.16]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.04) 1px, transparent 1px)",
            backgroundSize: "64px 64px",
            maskImage:
              "linear-gradient(to bottom, black, transparent 82%)",
          }}
        />
      </div>

      <nav className="relative z-20 mx-auto flex max-w-7xl items-center justify-between px-6 py-6 lg:px-10">
        <Link href="/" className="group flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-emerald-400/20 bg-emerald-400/[0.08] shadow-lg shadow-emerald-950/30 transition duration-300 group-hover:scale-105 group-hover:border-emerald-400/40">
            <div className="h-3 w-3 rounded-full bg-emerald-300 shadow-[0_0_18px_rgba(110,231,183,.8)]" />
          </div>
          <div className="text-xl font-semibold tracking-[-0.03em]">
            TopOne
          </div>
        </Link>

        <div className="hidden items-center gap-8 text-sm text-white/45 md:flex">
          <a href="#features" className="transition duration-300 hover:text-white">
            Features
          </a>
          <a href="#how-it-works" className="transition duration-300 hover:text-white">
            How it works
          </a>
          <a href="#security" className="transition duration-300 hover:text-white">
            Security
          </a>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="hidden rounded-full px-5 py-2.5 text-sm text-white/60 transition duration-300 hover:bg-white/[0.05] hover:text-white sm:block"
          >
            Sign in
          </Link>

          <Link
            href="/register"
            className="rounded-full border border-white/80 bg-white px-5 py-2.5 text-sm font-medium text-black shadow-lg shadow-black/20 transition duration-300 hover:scale-[1.03] hover:bg-emerald-50 active:scale-[0.98]"
          >
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative z-10 mx-auto flex max-w-7xl flex-col items-center px-6 pb-28 pt-20 text-center lg:px-10 lg:pt-28">
        <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-emerald-400/15 bg-emerald-400/[0.055] px-4 py-2 text-[11px] font-medium tracking-[0.18em] text-emerald-200/90 shadow-lg shadow-emerald-950/20 backdrop-blur-xl">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-300 shadow-[0_0_12px_rgba(110,231,183,.9)]" />
          AI-NATIVE WEALTH OPERATING SYSTEM
        </div>

        <h1 className="max-w-6xl text-5xl font-semibold leading-[0.98] tracking-[-0.055em] sm:text-6xl lg:text-[92px]">
          Your money has a story.
          <br />
          <span className="bg-gradient-to-r from-emerald-200 via-teal-200 to-cyan-200 bg-clip-text text-transparent">
            Make its future visible.
          </span>
        </h1>

        <p className="mt-8 max-w-2xl text-base leading-7 text-white/45 sm:text-lg">
          TopOne turns your finances, goals and risk profile into a living
          financial model — then helps you understand what to do next.
        </p>


        <div className="mt-10 flex flex-col gap-3 sm:flex-row">
          <Link
            href="/register"
            className="group inline-flex items-center justify-center gap-2 rounded-full bg-emerald-300 px-7 py-3.5 font-medium text-[#04100c] shadow-xl shadow-emerald-950/30 transition duration-300 hover:-translate-y-0.5 hover:bg-emerald-200 active:translate-y-0"
          >
            Build My Wealth Profile
            <span className="transition duration-300 group-hover:translate-x-1">→</span>
          </Link>

          <a
            href="#features"
            className="inline-flex items-center justify-center rounded-full border border-white/10 bg-white/[0.045] px-7 py-3.5 font-medium text-white/80 backdrop-blur-xl transition duration-300 hover:-translate-y-0.5 hover:border-white/20 hover:bg-white/[0.075] hover:text-white"
          >
            Explore TopOne
          </a>
        </div>

        {/* Financial core */}
        <div className="relative mt-20 w-full max-w-6xl">
          <div className="pointer-events-none absolute left-1/2 top-[-6rem] h-64 w-64 -translate-x-1/2 rounded-full bg-emerald-400/[0.09] blur-[90px]" />

          <div className="relative overflow-hidden rounded-[36px] border border-white/[0.09] bg-white/[0.035] p-3 shadow-[0_35px_120px_rgba(0,0,0,.55)] backdrop-blur-2xl sm:p-4">
            <div className="rounded-[28px] border border-white/[0.07] bg-[#080b10]/90 p-5 text-left sm:p-8">
              <div className="flex flex-col gap-5 border-b border-white/[0.07] pb-7 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <div className="flex items-center gap-2 text-xs text-white/35">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-300" />
                    LIVE FINANCIAL MODEL
                  </div>
                  <h2 className="mt-2 text-2xl font-medium tracking-[-0.03em]">
                    Your financial life, connected.
                  </h2>
                </div>

                <div className="inline-flex w-fit items-center gap-2 rounded-full border border-emerald-400/15 bg-emerald-400/[0.06] px-4 py-2 text-xs text-emerald-200">
                  <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-300" />
                  Financial Twin Active
                </div>
              </div>

              <div className="mt-6 grid gap-4 md:grid-cols-4">
                <DashboardCard label="Net Worth" value="₹12.4L" detail="+8.4% this year" />
                <DashboardCard label="Wealth DNA" value="82 / 100" detail="Strong profile" />
                <DashboardCard label="Risk Profile" value="Moderate" detail="Balanced capacity" />
                <DashboardCard label="Goal Readiness" value="76%" detail="3 active goals" />
              </div>

              <div className="mt-4 grid gap-4 lg:grid-cols-[1.55fr_.8fr]">
                <div className="rounded-[24px] border border-white/[0.07] bg-white/[0.025] p-6">
                  <div className="flex items-end justify-between">
                    <div>
                      <p className="text-xs uppercase tracking-[0.14em] text-white/30">
                        Future trajectory
                      </p>
                      <h3 className="mt-2 text-xl font-medium">
                        Projected net worth
                      </h3>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-white/30">10Y projection</p>
                      <p className="mt-1 text-lg font-medium text-emerald-200">₹38.6L</p>
                    </div>
                  </div>

                  <div className="mt-9 flex h-48 items-end gap-2">
                    {wealthBars.map((height, index) => (
                      <div key={index} className="group flex h-full flex-1 items-end">
                        <div
                          className="w-full rounded-t-md bg-gradient-to-t from-emerald-500/10 via-emerald-400/35 to-emerald-200/90 transition duration-300 group-hover:brightness-125"
                          style={{ height: `${height}%` }}
                        />
                      </div>
                    ))}
                  </div>

                  <div className="mt-4 flex justify-between text-[10px] uppercase tracking-[0.12em] text-white/20">
                    <span>Now</span>
                    <span>3Y</span>
                    <span>5Y</span>
                    <span>10Y</span>
                  </div>
                </div>

                <div className="relative overflow-hidden rounded-[24px] border border-emerald-400/15 bg-gradient-to-b from-emerald-400/[0.08] to-emerald-400/[0.025] p-6">
                  <div className="pointer-events-none absolute right-[-3rem] top-[-3rem] h-36 w-36 rounded-full bg-emerald-300/[0.12] blur-3xl" />

                  <div className="relative">
                    <p className="text-xs uppercase tracking-[0.14em] text-emerald-200/70">
                      TopOne Insight
                    </p>


                    <h3 className="mt-5 text-2xl font-medium leading-snug tracking-[-0.03em]">
                      Your emergency fund is the next move.
                    </h3>

                    <p className="mt-4 text-sm leading-6 text-white/42">
                      Building another 1.8 months of expenses could improve your
                      resilience before increasing equity exposure.
                    </p>

                    <div className="mt-8 rounded-2xl border border-white/[0.07] bg-black/10 p-4">
                      <p className="text-xs text-white/30">Priority</p>
                      <p className="mt-1 text-sm font-medium text-white/80">
                        Strengthen financial runway
                      </p>
                    </div>

                    <button className="mt-7 text-sm font-medium text-emerald-200 transition hover:translate-x-1">
                      View recommendation →
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature system */}
      <section id="features" className="relative z-10 mx-auto max-w-7xl px-6 py-24 lg:px-10">
        <div className="max-w-2xl">
          <p className="text-xs font-medium tracking-[0.18em] text-emerald-300">
            BUILT AROUND YOUR FINANCIAL IDENTITY
          </p>
          <h2 className="mt-4 text-4xl font-semibold tracking-[-0.04em] sm:text-5xl">
            More than a dashboard.
            <span className="text-white/35"> A financial operating system.</span>
          </h2>
        </div>

        <div className="mt-12 grid gap-4 md:grid-cols-3">
          <FeatureCard
            number="01"
            title="Wealth DNA"
            text="A living profile of your stability, savings discipline, debt health, readiness and risk alignment."
          />
          <FeatureCard
            number="02"
            title="Financial Twin"
            text="A forward-looking model that shows where your current choices could take your net worth and goals."
          />
          <FeatureCard
            number="03"
            title="Decision Intelligence"
            text="Clear, explainable priorities based on your real financial context — not generic advice."
          />
        </div>
      </section>

      <section id="how-it-works" className="relative z-10 mx-auto max-w-7xl px-6 py-24 lg:px-10">
        <div className="overflow-hidden rounded-[32px] border border-white/[0.08] bg-white/[0.025] p-8 sm:p-10">
          <p className="text-xs font-medium tracking-[0.18em] text-emerald-300">HOW IT WORKS</p>
          <div className="mt-8 grid gap-8 md:grid-cols-4">
            {[
              ["01", "Build your profile", "Income, expenses, assets, liabilities and protection."],
              ["02", "Understand your risk", "Behaviour and capacity combined into one risk profile."],
              ["03", "Define your goals", "Turn future plans into measurable financial targets."],
              ["04", "Activate intelligence", "Wealth DNA and Financial Twin connect everything together."],
            ].map(([number, title, text]) => (
              <div key={number}>
                <p className="text-xs text-emerald-300/70">{number}</p>
                <h3 className="mt-3 text-lg font-medium">{title}</h3>
                <p className="mt-3 text-sm leading-6 text-white/35">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="security" className="relative z-10 mx-auto max-w-7xl px-6 pb-28 pt-16 lg:px-10">
        <div className="flex flex-col gap-6 rounded-[32px] border border-white/[0.08] bg-gradient-to-r from-white/[0.035] to-emerald-400/[0.035] p-8 sm:flex-row sm:items-center sm:justify-between sm:p-10">
          <div className="max-w-2xl">
            <p className="text-xs font-medium tracking-[0.18em] text-emerald-300">SECURITY & CONTROL</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-[-0.04em]">
              Your financial identity stays yours.
            </h2>
            <p className="mt-3 text-sm leading-6 text-white/40">
              Authentication, protected APIs and user-specific financial data are
              built into the core experience.
            </p>
          </div>

          <Link
            href="/register"
            className="inline-flex shrink-0 items-center justify-center rounded-full bg-white px-6 py-3 text-sm font-medium text-black transition hover:scale-[1.03]"
          >
            Create your profile
          </Link>
        </div>
      </section>
    </main>
  );
}

function DashboardCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="group rounded-[20px] border border-white/[0.07] bg-white/[0.025] p-5 transition duration-300 hover:-translate-y-1 hover:border-emerald-400/20 hover:bg-white/[0.045]">
      <p className="text-[11px] uppercase tracking-[0.12em] text-white/28">{label}</p>
      <p className="mt-3 text-2xl font-medium tracking-[-0.03em]">{value}</p>
      <p className="mt-2 text-xs text-emerald-200/60">{detail}</p>
    </div>
  );
}

function FeatureCard({
  number,
  title,
  text,
}: {
  number: string;
  title: string;
  text: string;
}) {
  return (
    <div className="group rounded-[26px] border border-white/[0.08] bg-white/[0.025] p-7 transition duration-300 hover:-translate-y-1 hover:border-emerald-400/20 hover:bg-white/[0.045]">
      <div className="flex items-center justify-between">
        <span className="text-xs text-emerald-300/60">{number}</span>
        <span className="h-2 w-2 rounded-full bg-white/15 transition group-hover:bg-emerald-300" />
      </div>
      <h3 className="mt-8 text-xl font-medium tracking-[-0.03em]">{title}</h3>
      <p className="mt-3 text-sm leading-6 text-white/36">{text}</p>
    </div>
  );
}
