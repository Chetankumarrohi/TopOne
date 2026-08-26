"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type User = {
  id: number;
  full_name: string;
  email: string;
  is_active: boolean;
};

type FinancialProfile = {
  net_worth: number;
  savings_rate: number;
  debt_to_income_ratio: number;
  emergency_months: number;
  investment_ratio: number;
};

type RiskProfile = {
  final_risk_score: number;
  risk_category: string;
  capacity_score: number;
  behaviour_score: number;
};

type Goal = {
  id: number;
  status: string;
};

type WealthDNA = {
  wealth_score: number;
  investor_personality: string;
  financial_stability_score: number;
  savings_discipline_score: number;
  debt_health_score: number;
  emergency_preparedness_score: number;
  investment_readiness_score: number;
  goal_readiness_score: number;
  risk_alignment_score: number;
  strongest_trait: string | null;
  improvement_area: string | null;
};

export default function DashboardPage() {
  const router = useRouter();

  const [user, setUser] = useState<User | null>(null);
  const [financialProfile, setFinancialProfile] =
    useState<FinancialProfile | null>(null);
  const [riskProfile, setRiskProfile] =
    useState<RiskProfile | null>(null);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [wealthDNA, setWealthDNA] =
    useState<WealthDNA | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      const token = localStorage.getItem("access_token");

      if (!token) {
        router.push("/login");
        return;
      }

      const headers = {
        Authorization: `Bearer ${token}`,
      };

      try {
        const userResponse = await fetch(
          "http://127.0.0.1:8000/users/me",
          { headers }
        );

        if (!userResponse.ok) {
          localStorage.removeItem("access_token");
          localStorage.removeItem("token_type");
          router.push("/login");
          return;
        }

        setUser(await userResponse.json());

        const financialResponse = await fetch(
          "http://127.0.0.1:8000/financial-profile",
          { headers }
        );

        if (financialResponse.ok) {
          setFinancialProfile(
            await financialResponse.json()
          );
        }

        const riskResponse = await fetch(
          "http://127.0.0.1:8000/risk/profile",
          { headers }
        );

        let riskExists = false;

        if (riskResponse.ok) {
          setRiskProfile(await riskResponse.json());
          riskExists = true;
        }

        const goalsResponse = await fetch(
          "http://127.0.0.1:8000/goals",
          { headers }
        );

        let goalsExist = false;

        if (goalsResponse.ok) {
          const goalsData = await goalsResponse.json();
          setGoals(goalsData);
          goalsExist = goalsData.length > 0;
        }

        const wealthResponse = await fetch(
          "http://127.0.0.1:8000/wealth-dna",
          { headers }
        );

        if (wealthResponse.ok) {
          setWealthDNA(await wealthResponse.json());
        } else if (
          wealthResponse.status === 404 &&
          riskExists &&
          goalsExist
        ) {
          const generateResponse = await fetch(
            "http://127.0.0.1:8000/wealth-dna/generate",
            {
              method: "POST",
              headers,
            }
          );

          if (generateResponse.ok) {
            setWealthDNA(
              await generateResponse.json()
            );
          }
        }
      } catch {
        setError(
          "Could not connect to TopOne backend."
        );
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, [router]);

  function handleLogout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("token_type");
    router.push("/login");
  }

  const activeGoals = goals.filter(
    (goal) => goal.status === "ACTIVE"
  ).length;

  const firstName =
    user?.full_name?.split(" ")[0] || "there";

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#05070b] text-white">
        <div className="text-center">
          <div className="mx-auto h-9 w-9 animate-spin rounded-full border-2 border-white/10 border-t-emerald-300" />
          <p className="mt-5 text-sm text-white/40">
            Preparing your financial workspace...
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#05070b] text-white">
      {/* Ambient background */}
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute left-[18%] top-[-16rem] h-[28rem] w-[28rem] rounded-full bg-emerald-400/[0.06] blur-[110px]" />
        <div className="absolute right-[-8rem] top-[20rem] h-[26rem] w-[26rem] rounded-full bg-cyan-400/[0.04] blur-[120px]" />
        <div
          className="absolute inset-0 opacity-[0.11]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px)",
            backgroundSize: "72px 72px",
            maskImage:
              "linear-gradient(to bottom, black, transparent 88%)",
          }}
        />
      </div>

      <nav className="relative z-20 border-b border-white/[0.06] bg-[#05070b]/70 backdrop-blur-2xl">
        <div className="mx-auto flex max-w-[1450px] items-center justify-between px-6 py-5 lg:px-10">
          <button
            onClick={() => router.push("/dashboard")}
            className="group flex items-center gap-3"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-emerald-400/20 bg-emerald-400/[0.07]">
              <div className="h-3 w-3 rounded-full bg-emerald-300 shadow-[0_0_16px_rgba(110,231,183,.75)]" />
            </div>
            <span className="text-xl font-semibold tracking-[-0.03em]">
              TopOne
            </span>
          </button>

          <div className="flex items-center gap-3">
            <div className="hidden items-center gap-2 lg:flex">
              <button
                onClick={() => router.push("/portfolio")}
                className="rounded-full border border-white/[0.08] bg-white/[0.03] px-4 py-2 text-sm text-white/55 transition duration-300 hover:border-white/15 hover:bg-white/[0.06] hover:text-white"
              >
                Portfolio
              </button>

              <button
                onClick={() => router.push("/invest")}
                className="rounded-full border border-emerald-400/15 bg-emerald-400/[0.055] px-4 py-2 text-sm text-emerald-200 transition duration-300 hover:border-emerald-400/30 hover:bg-emerald-400/[0.09]"
              >
                Invest
              </button>
            </div>

            {user && (
              <div className="hidden text-right sm:block">
                <p className="text-sm font-medium text-white/85">
                  {user.full_name}
                </p>
                <p className="text-xs text-white/30">
                  {user.email}
                </p>
              </div>
            )}

            <button
              onClick={handleLogout}
              className="rounded-full border border-white/[0.08] bg-white/[0.035] px-4 py-2 text-sm text-white/55 transition duration-300 hover:border-white/15 hover:bg-white/[0.06] hover:text-white"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      <section className="relative z-10 mx-auto max-w-[1450px] px-6 py-10 lg:px-10 lg:py-12">
        {error && (
          <div className="mb-6 rounded-2xl border border-red-400/15 bg-red-400/[0.04] px-5 py-4 text-sm text-red-200/80">
            {error}
          </div>
        )}

        {/* Hero */}
        <div className="relative overflow-hidden rounded-[32px] border border-white/[0.08] bg-white/[0.025] p-7 shadow-[0_30px_100px_rgba(0,0,0,.25)] backdrop-blur-2xl sm:p-9">
          <div className="pointer-events-none absolute right-[-5rem] top-[-7rem] h-72 w-72 rounded-full bg-emerald-300/[0.08] blur-[70px]" />

          <div className="relative flex flex-col gap-8 xl:flex-row xl:items-end xl:justify-between">
            <div className="max-w-3xl">
              <div className="flex items-center gap-2 text-[11px] font-medium tracking-[0.17em] text-emerald-200/70">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-300 shadow-[0_0_10px_rgba(110,231,183,.8)]" />
                FINANCIAL INTELLIGENCE ACTIVE
              </div>

              <h1 className="mt-5 text-4xl font-semibold tracking-[-0.045em] sm:text-5xl lg:text-6xl">
                Good to see you,
                <span className="text-white/36"> {firstName}.</span>
              </h1>

              <p className="mt-5 max-w-2xl text-sm leading-6 text-white/40 sm:text-base">
                Your financial identity is connected. TopOne is tracking
                your financial health, risk profile, goals and future trajectory
                in one place.
              </p>

              <div className="mt-7 flex flex-col gap-3 sm:flex-row">
                {wealthDNA ? (
                  <button
                    onClick={() =>
                      router.push("/financial-twin")
                    }
                    className="rounded-full bg-emerald-300 px-6 py-3 text-sm font-medium text-[#04100c] transition duration-300 hover:-translate-y-0.5 hover:bg-emerald-200"
                  >
                    Open Financial Twin →
                  </button>
                ) : (
                  <button
                    onClick={() =>
                      router.push(
                        financialProfile
                          ? riskProfile
                            ? "/goals"
                            : "/risk-assessment"
                          : "/financial-profile"
                      )
                    }
                    className="rounded-full bg-emerald-300 px-6 py-3 text-sm font-medium text-[#04100c] transition duration-300 hover:-translate-y-0.5 hover:bg-emerald-200"
                  >
                    Continue Setup →
                  </button>
                )}

                <button
                  onClick={() => router.push("/goals")}
                  className="rounded-full border border-white/[0.09] bg-white/[0.035] px-6 py-3 text-sm text-white/65 transition duration-300 hover:border-white/15 hover:bg-white/[0.06] hover:text-white"
                >
                  Manage Goals
                </button>

                <button
                  onClick={() => router.push("/portfolio")}
                  className="rounded-full border border-white/[0.09] bg-white/[0.035] px-6 py-3 text-sm text-white/65 transition duration-300 hover:border-white/15 hover:bg-white/[0.06] hover:text-white"
                >
                  Portfolio
                </button>

                <button
                  onClick={() => router.push("/invest")}
                  className="rounded-full border border-emerald-400/15 bg-emerald-400/[0.055] px-6 py-3 text-sm text-emerald-200 transition duration-300 hover:border-emerald-400/30 hover:bg-emerald-400/[0.09]"
                >
                  Discover Investments
                </button>
              </div>
            </div>

            <div className="grid w-full gap-3 sm:grid-cols-3 xl:w-auto xl:min-w-[470px]">
              <HeroStat
                label="Net Worth"
                value={
                  financialProfile
                    ? `₹${formatMoney(
                        financialProfile.net_worth
                      )}`
                    : "—"
                }
                detail="Current position"
              />
              <HeroStat
                label="Wealth DNA"
                value={
                  wealthDNA
                    ? `${Math.round(
                        wealthDNA.wealth_score
                      )}/100`
                    : "Locked"
                }
                detail={
                  wealthDNA
                    ? wealthDNA.investor_personality
                    : "Complete setup"
                }
              />
              <HeroStat
                label="Active Goals"
                value={String(activeGoals)}
                detail="Tracked plans"
              />
            </div>
          </div>
        </div>

        {/* Module cards */}
        <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4 2xl:grid-cols-7">
          <ModuleCard
            eyebrow="PROFILE"
            title="Financial Profile"
            value={
              financialProfile
                ? "Completed"
                : "Not completed"
            }
            detail={
              financialProfile
                ? `Net worth ₹${formatMoney(
                    financialProfile.net_worth
                  )}`
                : "Add your financial foundation."
            }
            active={!!financialProfile}
            onClick={() =>
              router.push("/financial-profile")
            }
          />

          <ModuleCard
            eyebrow="RISK"
            title="Risk Profile"
            value={
              riskProfile
                ? riskProfile.risk_category
                : "Pending"
            }
            detail={
              riskProfile
                ? `Risk score ${Math.round(
                    riskProfile.final_risk_score
                  )}/100`
                : "Complete your assessment."
            }
            active={!!riskProfile}
            onClick={() => {
              if (financialProfile) {
                router.push("/risk-assessment");
              }
            }}
          />

          <ModuleCard
            eyebrow="DNA"
            title="Wealth DNA"
            value={
              wealthDNA
                ? `${Math.round(
                    wealthDNA.wealth_score
                  )}/100`
                : "Locked"
            }
            detail={
              wealthDNA
                ? wealthDNA.investor_personality
                : "Unlock after risk + goals."
            }
            active={!!wealthDNA}
          />

          <ModuleCard
            eyebrow="GOALS"
            title="Financial Goals"
            value={String(activeGoals)}
            detail={
              activeGoals > 0
                ? `${activeGoals} active ${
                    activeGoals === 1 ? "goal" : "goals"
                  }`
                : "Create your first goal."
            }
            active={activeGoals > 0}
            onClick={() => router.push("/goals")}
          />

          <ModuleCard
            eyebrow="TWIN"
            title="Financial Twin"
            value={wealthDNA ? "Active" : "Locked"}
            detail={
              wealthDNA
                ? "Explore your future trajectory."
                : "Complete Wealth DNA first."
            }
            active={!!wealthDNA}
            onClick={() => {
              if (wealthDNA) {
                router.push("/financial-twin");
              }
            }}
          />

          <ModuleCard
            eyebrow="PORTFOLIO"
            title="Connected Investments"
            value="Portfolio"
            detail="Track mutual funds, stocks, ETFs and more."
            active
            onClick={() => router.push("/portfolio")}
          />

          <ModuleCard
            eyebrow="INVEST"
            title="Discover & Invest"
            value="Explore"
            detail="Find investment opportunities matched to your profile."
            active
            onClick={() => router.push("/invest")}
          />
        </div>

        {/* Main intelligence grid */}
        <div className="mt-6 grid gap-5 xl:grid-cols-[1.35fr_.65fr]">
          <div className="rounded-[28px] border border-white/[0.08] bg-white/[0.025] p-6 sm:p-7">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="text-[11px] font-medium tracking-[0.15em] text-white/28">
                  FINANCIAL SIGNALS
                </p>
                <h2 className="mt-2 text-2xl font-medium tracking-[-0.03em]">
                  Your financial foundation
                </h2>
              </div>
              {financialProfile && (
                <p className="text-xs text-white/28">
                  Live from your profile
                </p>
              )}
            </div>

            {financialProfile ? (
              <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                <SignalCard
                  label="Net Worth"
                  value={`₹${formatMoney(
                    financialProfile.net_worth
                  )}`}
                  score={Math.min(
                    financialProfile.net_worth > 0
                      ? 100
                      : 15,
                    100
                  )}
                />
                <SignalCard
                  label="Savings Rate"
                  value={`${financialProfile.savings_rate.toFixed(
                    1
                  )}%`}
                  score={Math.min(
                    (financialProfile.savings_rate / 30) *
                      100,
                    100
                  )}
                />
                <SignalCard
                  label="Debt / Income"
                  value={`${financialProfile.debt_to_income_ratio.toFixed(
                    1
                  )}%`}
                  score={Math.max(
                    100 -
                      financialProfile.debt_to_income_ratio,
                    0
                  )}
                />
                <SignalCard
                  label="Emergency Cover"
                  value={`${financialProfile.emergency_months.toFixed(
                    1
                  )} mo`}
                  score={Math.min(
                    (financialProfile.emergency_months / 6) *
                      100,
                    100
                  )}
                />
                <SignalCard
                  label="Investment Ratio"
                  value={`${financialProfile.investment_ratio.toFixed(
                    1
                  )}%`}
                  score={Math.min(
                    financialProfile.investment_ratio * 2,
                    100
                  )}
                />
              </div>
            ) : (
              <EmptyState
                title="Financial profile incomplete"
                text="Add your income, expenses, assets and liabilities to activate your financial signals."
                button="Complete profile"
                onClick={() =>
                  router.push("/financial-profile")
                }
              />
            )}
          </div>

          <div className="relative overflow-hidden rounded-[28px] border border-emerald-400/15 bg-gradient-to-b from-emerald-400/[0.07] to-emerald-400/[0.025] p-6 sm:p-7">
            <div className="pointer-events-none absolute right-[-4rem] top-[-4rem] h-40 w-40 rounded-full bg-emerald-300/[0.1] blur-3xl" />
            <div className="relative">
              <p className="text-[11px] font-medium tracking-[0.15em] text-emerald-200/70">
                TOPONE INSIGHT
              </p>

              {wealthDNA ? (
                <>
                  <h3 className="mt-5 text-2xl font-medium leading-snug tracking-[-0.03em]">
                    You are a{" "}
                    <span className="text-emerald-200">
                      {wealthDNA.investor_personality}
                    </span>
                    .
                  </h3>

                  <p className="mt-4 text-sm leading-6 text-white/40">
                    Your strongest trait is{" "}
                    <span className="text-white/80">
                      {wealthDNA.strongest_trait ??
                        "still developing"}
                    </span>
                    . Your biggest improvement opportunity is{" "}
                    <span className="text-white/80">
                      {wealthDNA.improvement_area ??
                        "still being identified"}
                    </span>
                    .
                  </p>

                  <button
                    onClick={() =>
                      router.push("/financial-twin")
                    }
                    className="mt-7 text-sm font-medium text-emerald-200 transition hover:translate-x-1"
                  >
                    Explore your Financial Twin →
                  </button>
                </>
              ) : riskProfile ? (
                <>
                  <h3 className="mt-5 text-2xl font-medium leading-snug tracking-[-0.03em]">
                    Your risk profile is active.
                  </h3>
                  <p className="mt-4 text-sm leading-6 text-white/40">
                    Create at least one financial goal to unlock your Wealth DNA
                    and Financial Twin.
                  </p>
                  <button
                    onClick={() => router.push("/goals")}
                    className="mt-7 text-sm font-medium text-emerald-200 transition hover:translate-x-1"
                  >
                    Create a financial goal →
                  </button>
                </>
              ) : (
                <>
                  <h3 className="mt-5 text-2xl font-medium leading-snug tracking-[-0.03em]">
                    Complete your financial identity.
                  </h3>
                  <p className="mt-4 text-sm leading-6 text-white/40">
                    TopOne unlocks progressively as your financial profile,
                    risk assessment and goals come together.
                  </p>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Wealth DNA */}
        {wealthDNA && (
          <div className="mt-6 rounded-[30px] border border-white/[0.08] bg-white/[0.025] p-6 sm:p-8">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p className="text-[11px] font-medium tracking-[0.16em] text-emerald-200/70">
                  WEALTH DNA
                </p>
                <h2 className="mt-3 text-3xl font-semibold tracking-[-0.04em]">
                  {wealthDNA.investor_personality}
                </h2>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-white/38">
                  A live profile of your financial behaviour, readiness and
                  resilience.
                </p>
              </div>

              <div className="flex items-end gap-2">
                <span className="text-6xl font-semibold tracking-[-0.05em] text-emerald-200">
                  {Math.round(wealthDNA.wealth_score)}
                </span>
                <span className="pb-2 text-lg text-white/20">
                  /100
                </span>
              </div>
            </div>

            <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <DNAStat
                label="Financial Stability"
                value={wealthDNA.financial_stability_score}
              />
              <DNAStat
                label="Savings Discipline"
                value={wealthDNA.savings_discipline_score}
              />
              <DNAStat
                label="Debt Health"
                value={wealthDNA.debt_health_score}
              />
              <DNAStat
                label="Emergency Preparedness"
                value={
                  wealthDNA.emergency_preparedness_score
                }
              />
              <DNAStat
                label="Investment Readiness"
                value={
                  wealthDNA.investment_readiness_score
                }
              />
              <DNAStat
                label="Goal Readiness"
                value={wealthDNA.goal_readiness_score}
              />
              <DNAStat
                label="Risk Alignment"
                value={wealthDNA.risk_alignment_score}
              />

              <button
                onClick={() =>
                  router.push("/financial-twin")
                }
                className="group rounded-[20px] border border-emerald-400/15 bg-emerald-400/[0.06] p-5 text-left transition duration-300 hover:-translate-y-1 hover:border-emerald-400/30 hover:bg-emerald-400/[0.09]"
              >
                <p className="text-[10px] uppercase tracking-[0.12em] text-emerald-200/50">
                  NEXT
                </p>
                <p className="mt-3 text-lg font-medium">
                  Financial Twin
                </p>
                <p className="mt-2 text-xs leading-5 text-white/32">
                  Open your forward-looking financial model.
                </p>
                <p className="mt-5 text-sm text-emerald-200 transition group-hover:translate-x-1">
                  Open →
                </p>
              </button>
            </div>
          </div>
        )}
      </section>
    </main>
  );
}

function HeroStat({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-[20px] border border-white/[0.07] bg-black/10 p-5">
      <p className="text-[10px] uppercase tracking-[0.13em] text-white/25">
        {label}
      </p>
      <p className="mt-3 text-2xl font-medium tracking-[-0.03em]">
        {value}
      </p>
      <p className="mt-2 truncate text-xs text-white/28">
        {detail}
      </p>
    </div>
  );
}

function ModuleCard({
  eyebrow,
  title,
  value,
  detail,
  active = false,
  onClick,
}: {
  eyebrow: string;
  title: string;
  value: string;
  detail: string;
  active?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!onClick}
      className={`group rounded-[22px] border p-5 text-left transition duration-300 ${
        active
          ? "border-emerald-400/15 bg-emerald-400/[0.035]"
          : "border-white/[0.07] bg-white/[0.022]"
      } ${
        onClick
          ? "hover:-translate-y-1 hover:border-emerald-400/25 hover:bg-white/[0.04]"
          : ""
      }`}
    >
      <div className="flex items-center justify-between">
        <p className="text-[10px] font-medium tracking-[0.14em] text-white/25">
          {eyebrow}
        </p>
        <span
          className={`h-1.5 w-1.5 rounded-full ${
            active
              ? "bg-emerald-300 shadow-[0_0_10px_rgba(110,231,183,.6)]"
              : "bg-white/15"
          }`}
        />
      </div>

      <p className="mt-5 text-sm text-white/38">
        {title}
      </p>

      <p
        className={`mt-2 text-xl font-medium tracking-[-0.03em] ${
          active
            ? "text-emerald-200"
            : "text-white/80"
        }`}
      >
        {value}
      </p>

      <p className="mt-3 min-h-10 text-xs leading-5 text-white/28">
        {detail}
      </p>
    </button>
  );
}

function SignalCard({
  label,
  value,
  score,
}: {
  label: string;
  value: string;
  score: number;
}) {
  const safeScore = Math.min(
    Math.max(score, 0),
    100
  );

  return (
    <div className="rounded-[18px] border border-white/[0.06] bg-black/10 p-4">
      <p className="text-[10px] uppercase tracking-[0.11em] text-white/24">
        {label}
      </p>
      <p className="mt-3 text-lg font-medium">
        {value}
      </p>
      <div className="mt-4 h-1 overflow-hidden rounded-full bg-white/[0.07]">
        <div
          className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-emerald-200"
          style={{ width: `${safeScore}%` }}
        />
      </div>
    </div>
  );
}

function DNAStat({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  const safeValue = Math.min(
    Math.max(value, 0),
    100
  );

  return (
    <div className="rounded-[20px] border border-white/[0.06] bg-black/10 p-5">
      <div className="flex items-end justify-between gap-4">
        <p className="text-xs leading-5 text-white/32">
          {label}
        </p>
        <p className="text-lg font-medium text-emerald-200">
          {Math.round(value)}
        </p>
      </div>
      <div className="mt-4 h-1 overflow-hidden rounded-full bg-white/[0.07]">
        <div
          className="h-full rounded-full bg-emerald-300"
          style={{
            width: `${safeValue}%`,
          }}
        />
      </div>
    </div>
  );
}

function EmptyState({
  title,
  text,
  button,
  onClick,
}: {
  title: string;
  text: string;
  button: string;
  onClick: () => void;
}) {
  return (
    <div className="mt-6 rounded-[22px] border border-dashed border-white/[0.08] bg-black/10 p-8">
      <h3 className="text-lg font-medium">{title}</h3>
      <p className="mt-2 max-w-xl text-sm leading-6 text-white/35">
        {text}
      </p>
      <button
        onClick={onClick}
        className="mt-5 text-sm font-medium text-emerald-200"
      >
        {button} →
      </button>
    </div>
  );
}

function formatMoney(value: number) {
  return new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 0,
  }).format(value);
}
