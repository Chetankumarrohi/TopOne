"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

type FinancialTwin = {
  net_worth: number;
  monthly_income: number;
  monthly_expenses: number;
  monthly_surplus: number;

  savings_rate: number;
  emergency_months: number;
  debt_to_income_ratio: number;
  investment_ratio: number;

  risk_score: number;
  risk_category: string;

  wealth_score: number;
  investor_personality: string;

  active_goals: number;
  total_goal_target: number;
  total_goal_saved: number;
  goal_progress_percentage: number;

  projected_net_worth_1y: number;
  projected_net_worth_3y: number;
  projected_net_worth_5y: number;
  projected_net_worth_10y: number;

  financial_runway_months: number;
  financial_health_score: number;

  financial_status: string;
  next_priority: string;
};

type ProjectionPoint = {
  label: string;
  value: number;
};

export default function FinancialTwinPage() {
  const router = useRouter();

  const [twin, setTwin] =
    useState<FinancialTwin | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  useEffect(() => {
    async function loadTwin() {
      const token =
        localStorage.getItem("access_token");

      if (!token) {
        router.push("/login");
        return;
      }

      try {
        const response = await fetch(
          "http://127.0.0.1:8000/financial-twin",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        const data = await response.json();

        if (!response.ok) {
          setError(
            data.detail ||
              "Could not load your Financial Twin."
          );

          return;
        }

        setTwin(data);
      } catch {
        setError(
          "Could not connect to InvestiGenie backend."
        );
      } finally {
        setLoading(false);
      }
    }

    loadTwin();
  }, [router]);

  const projections = useMemo<ProjectionPoint[]>(() => {
    if (!twin) {
      return [];
    }

    return [
      {
        label: "Today",
        value: twin.net_worth,
      },
      {
        label: "1Y",
        value: twin.projected_net_worth_1y,
      },
      {
        label: "3Y",
        value: twin.projected_net_worth_3y,
      },
      {
        label: "5Y",
        value: twin.projected_net_worth_5y,
      },
      {
        label: "10Y",
        value: twin.projected_net_worth_10y,
      },
    ];
  }, [twin]);

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#05070b] text-white">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-white/10 border-t-emerald-400" />

          <p className="mt-5 text-sm text-white/45">
            Building your Financial Twin...
          </p>
        </div>
      </main>
    );
  }

  if (error || !twin) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#05070b] px-6 text-white">
        <div className="w-full max-w-lg rounded-[28px] border border-red-400/20 bg-red-400/[0.04] p-8 text-center">
          <p className="text-sm text-red-300">
            {error || "Financial Twin unavailable."}
          </p>

          <button
            onClick={() =>
              router.push("/dashboard")
            }
            className="mt-6 rounded-full bg-white px-6 py-3 text-sm font-medium text-black transition-all hover:scale-105"
          >
            Back to Dashboard
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#05070b] text-white">
      <nav className="border-b border-white/10">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5 lg:px-10">
          <button
            onClick={() =>
              router.push("/dashboard")
            }
            className="text-xl font-semibold tracking-tight"
          >
            Investi
            <span className="text-emerald-400">
              Genie
            </span>
          </button>

          <button
            onClick={() =>
              router.push("/dashboard")
            }
            className="rounded-full border border-white/10 bg-white/[0.04] px-5 py-2 text-sm text-white/65 transition-all hover:scale-105 hover:bg-white/[0.08] hover:text-white"
          >
            Back to Dashboard
          </button>
        </div>
      </nav>

      <section className="mx-auto max-w-7xl px-6 py-12 lg:px-10">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-medium text-emerald-300">
              FINANCIAL TWIN
            </p>

            <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">
              Your financial future,
              <br />
              modeled today.
            </h1>

            <p className="mt-4 max-w-2xl text-sm leading-6 text-white/45">
              InvestiGenie combines your current finances,
              risk profile, Wealth DNA and goals into a
              forward-looking financial simulation.
            </p>
          </div>

          <div className="rounded-[24px] border border-emerald-400/20 bg-emerald-400/[0.05] px-7 py-5">
            <p className="text-xs text-white/40">
              Financial Health
            </p>

            <div className="mt-2 flex items-end gap-2">
              <span className="text-5xl font-semibold text-emerald-300">
                {Math.round(
                  twin.financial_health_score
                )}
              </span>

              <span className="pb-1 text-lg text-white/25">
                /100
              </span>
            </div>

            <p className="mt-2 text-sm text-white/60">
              {twin.financial_status}
            </p>
          </div>
        </div>

        <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            label="Current Net Worth"
            value={`₹${formatMoney(
              twin.net_worth
            )}`}
            detail="Your present financial position"
          />

          <MetricCard
            label="Monthly Surplus"
            value={`₹${formatMoney(
              twin.monthly_surplus
            )}`}
            detail="After expenses and debt payments"
          />

          <MetricCard
            label="Wealth DNA"
            value={`${Math.round(
              twin.wealth_score
            )}/100`}
            detail={twin.investor_personality}
          />

          <MetricCard
            label="Risk Profile"
            value={twin.risk_category}
            detail={`Risk score ${Math.round(
              twin.risk_score
            )}/100`}
          />
        </div>

        <div className="mt-6 grid gap-5 lg:grid-cols-[1.6fr_1fr]">
          <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-7">
            <div className="flex items-end justify-between gap-4">
              <div>
                <p className="text-sm text-white/40">
                  Projected net worth
                </p>

                <h2 className="mt-2 text-2xl font-medium">
                  Your wealth trajectory
                </h2>
              </div>

              <div className="text-right">
                <p className="text-xs text-white/30">
                  10-year projection
                </p>

                <p className="mt-1 text-xl font-medium text-emerald-300">
                  ₹
                  {formatMoney(
                    twin.projected_net_worth_10y
                  )}
                </p>
              </div>
            </div>

            <ProjectionChart
              points={projections}
            />

            <p className="mt-6 text-xs leading-5 text-white/25">
              Projection is a simulation based on your
              current surplus and risk profile. It is
              not a guaranteed investment return.
            </p>
          </div>

          <div className="rounded-[28px] border border-emerald-400/15 bg-emerald-400/[0.05] p-7">
            <p className="text-sm text-emerald-300">
              Next Priority
            </p>

            <h3 className="mt-4 text-2xl font-medium leading-snug">
              {twin.next_priority}
            </h3>

            <div className="mt-8 space-y-4">
              <MiniMetric
                label="Emergency Runway"
                value={`${twin.financial_runway_months.toFixed(
                  1
                )} months`}
              />

              <MiniMetric
                label="Savings Rate"
                value={`${twin.savings_rate.toFixed(
                  1
                )}%`}
              />

              <MiniMetric
                label="Debt / Income"
                value={`${twin.debt_to_income_ratio.toFixed(
                  1
                )}%`}
              />
            </div>
          </div>
        </div>

        <div className="mt-6 grid gap-5 lg:grid-cols-2">
          <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-7">
            <p className="text-sm text-white/40">
              Goal intelligence
            </p>

            <div className="mt-5 flex items-end justify-between">
              <div>
                <p className="text-3xl font-semibold">
                  {twin.active_goals}
                </p>

                <p className="mt-1 text-sm text-white/40">
                  Active financial goals
                </p>
              </div>

              <p className="text-xl font-medium text-emerald-300">
                {twin.goal_progress_percentage.toFixed(
                  1
                )}
                %
              </p>
            </div>

            <div className="mt-5 h-2 overflow-hidden rounded-full bg-white/10">
              <div
                className="h-full rounded-full bg-emerald-400 transition-all duration-700"
                style={{
                  width: `${Math.min(
                    twin.goal_progress_percentage,
                    100
                  )}%`,
                }}
              />
            </div>

            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              <MiniMetric
                label="Target Value"
                value={`₹${formatMoney(
                  twin.total_goal_target
                )}`}
              />

              <MiniMetric
                label="Already Saved"
                value={`₹${formatMoney(
                  twin.total_goal_saved
                )}`}
              />
            </div>

            <button
              onClick={() =>
                router.push("/goals")
              }
              className="mt-6 text-sm font-medium text-emerald-300 transition-all hover:translate-x-1 hover:text-emerald-200"
            >
              Manage goals →
            </button>
          </div>

          <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-7">
            <p className="text-sm text-white/40">
              Financial resilience
            </p>

            <h3 className="mt-4 text-2xl font-medium">
              Your current financial structure
            </h3>

            <div className="mt-6 space-y-5">
              <ProgressMetric
                label="Emergency Preparedness"
                value={Math.min(
                  (twin.emergency_months / 6) * 100,
                  100
                )}
                display={`${twin.emergency_months.toFixed(
                  1
                )} months`}
              />

              <ProgressMetric
                label="Savings Discipline"
                value={Math.min(
                  (twin.savings_rate / 30) * 100,
                  100
                )}
                display={`${twin.savings_rate.toFixed(
                  1
                )}%`}
              />

              <ProgressMetric
                label="Investment Allocation"
                value={Math.min(
                  twin.investment_ratio,
                  100
                )}
                display={`${twin.investment_ratio.toFixed(
                  1
                )}%`}
              />
            </div>
          </div>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <ProjectionCard
            period="1 Year"
            value={
              twin.projected_net_worth_1y
            }
          />

          <ProjectionCard
            period="3 Years"
            value={
              twin.projected_net_worth_3y
            }
          />

          <ProjectionCard
            period="5 Years"
            value={
              twin.projected_net_worth_5y
            }
          />

          <ProjectionCard
            period="10 Years"
            value={
              twin.projected_net_worth_10y
            }
          />
        </div>
      </section>
    </main>
  );
}

function ProjectionChart({
  points,
}: {
  points: ProjectionPoint[];
}) {
  const maxValue = Math.max(
    ...points.map((point) => point.value),
    1
  );

  return (
    <div className="mt-10">
      <div className="flex h-72 items-end gap-4">
        {points.map((point) => {
          const height =
            Math.max(
              (point.value / maxValue) * 100,
              5
            );

          return (
            <div
              key={point.label}
              className="flex h-full flex-1 flex-col justify-end"
            >
              <div className="mb-3 text-center text-xs text-white/35">
                ₹{formatCompactMoney(point.value)}
              </div>

              <div
                className="w-full rounded-t-xl bg-gradient-to-t from-emerald-500/20 to-emerald-300 transition-all duration-700 hover:brightness-125"
                style={{
                  height: `${height}%`,
                }}
              />

              <p className="mt-3 text-center text-xs text-white/40">
                {point.label}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-[22px] border border-white/10 bg-white/[0.03] p-6 transition-all duration-300 hover:-translate-y-1 hover:border-emerald-400/20">
      <p className="text-xs text-white/35">
        {label}
      </p>

      <p className="mt-3 text-2xl font-medium">
        {value}
      </p>

      <p className="mt-2 text-xs leading-5 text-white/30">
        {detail}
      </p>
    </div>
  );
}

function MiniMetric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl border border-white/8 bg-white/[0.03] p-4">
      <p className="text-xs text-white/30">
        {label}
      </p>

      <p className="mt-2 text-sm font-medium">
        {value}
      </p>
    </div>
  );
}

function ProgressMetric({
  label,
  value,
  display,
}: {
  label: string;
  value: number;
  display: string;
}) {
  return (
    <div>
      <div className="flex items-center justify-between">
        <p className="text-sm text-white/50">
          {label}
        </p>

        <p className="text-sm font-medium">
          {display}
        </p>
      </div>

      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-emerald-400"
          style={{
            width: `${Math.min(
              Math.max(value, 0),
              100
            )}%`,
          }}
        />
      </div>
    </div>
  );
}

function ProjectionCard({
  period,
  value,
}: {
  period: string;
  value: number;
}) {
  return (
    <div className="rounded-[22px] border border-white/10 bg-white/[0.03] p-6">
      <p className="text-xs text-white/35">
        {period}
      </p>

      <p className="mt-3 text-xl font-medium text-emerald-300">
        ₹{formatMoney(value)}
      </p>

      <p className="mt-2 text-xs text-white/25">
        Projected net worth
      </p>
    </div>
  );
}

function formatMoney(value: number) {
  return new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 0,
  }).format(value);
}

function formatCompactMoney(value: number) {
  return new Intl.NumberFormat("en-IN", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}