"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  BrainCircuit,
  ChevronRight,
  Compass,
  Dna,
  Goal,
  Landmark,
  LineChart,
  Moon,
  PiggyBank,
  Sun,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  UserRound,
  WalletCards,
} from "lucide-react";

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

type GoalItem = {
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


type PortfolioSummary = {
  total_invested: number;
  current_value: number;
  total_gain: number;
  total_gain_percentage: number;
  number_of_holdings: number;
};

type PortfolioHistoryPoint = {
  date: string;
  market_value: number;
  invested_value: number;
  pnl?: number;
};

type ThemeMode = "dark" | "light";

const API_BASE = "/api-backend";

export default function DashboardPage() {
  const router = useRouter();

  const [user, setUser] = useState<User | null>(null);
  const [financialProfile, setFinancialProfile] =
    useState<FinancialProfile | null>(null);
  const [riskProfile, setRiskProfile] =
    useState<RiskProfile | null>(null);
  const [goals, setGoals] = useState<GoalItem[]>([]);
  const [wealthDNA, setWealthDNA] =
    useState<WealthDNA | null>(null);

  const [portfolioSummary, setPortfolioSummary] =
    useState<PortfolioSummary | null>(null);
  const [portfolioHistory, setPortfolioHistory] =
    useState<PortfolioHistoryPoint[]>([]);

  const [theme, setTheme] =
    useState<ThemeMode>("dark");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const saved =
      localStorage.getItem("investigenie-theme");

    const initialTheme: ThemeMode =
      saved === "light" ? "light" : "dark";

    setTheme(initialTheme);
    document.documentElement.dataset.theme =
      initialTheme;
  }, []);

  function toggleTheme() {
    const nextTheme: ThemeMode =
      theme === "dark" ? "light" : "dark";

    setTheme(nextTheme);
    document.documentElement.dataset.theme =
      nextTheme;
    localStorage.setItem(
      "investigenie-theme",
      nextTheme
    );
  }

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      const token = localStorage.getItem("access_token");

      if (!token) {
        router.replace("/login");
        return;
      }

      const headers = {
        Authorization: `Bearer ${token}`,
      };

      try {
        const userResponse = await fetch(
          `${API_BASE}/users/me`,
          { headers }
        );

        if (!userResponse.ok) {
          localStorage.removeItem("access_token");
          localStorage.removeItem("token_type");
          router.replace("/login");
          return;
        }

        const userData = await userResponse.json();

        if (!cancelled) {
          setUser(userData);
        }

        const [
          financialResponse,
          riskResponse,
          goalsResponse,
          portfolioSummaryResponse,
          portfolioHistoryResponse,
        ] = await Promise.all([
          fetch(`${API_BASE}/financial-profile`, {
            headers,
          }),
          fetch(`${API_BASE}/risk/profile`, {
            headers,
          }),
          fetch(`${API_BASE}/goals`, {
            headers,
          }),
          fetch(`${API_BASE}/portfolio/summary`, {
            headers,
          }),
          fetch(`${API_BASE}/portfolio/history`, {
            headers,
          }),
        ]);

        let riskExists = false;
        let goalsExist = false;

        if (financialResponse.ok) {
          const financialData =
            await financialResponse.json();

          if (!cancelled) {
            setFinancialProfile(financialData);
          }
        }

        if (riskResponse.ok) {
          const riskData = await riskResponse.json();

          riskExists = true;

          if (!cancelled) {
            setRiskProfile(riskData);
          }
        }

        if (goalsResponse.ok) {
          const goalsData = await goalsResponse.json();

          goalsExist = goalsData.length > 0;

          if (!cancelled) {
            setGoals(goalsData);
          }
        }

        if (portfolioSummaryResponse.ok) {
          const portfolioData =
            await portfolioSummaryResponse.json();

          if (!cancelled) {
            setPortfolioSummary(portfolioData);
          }
        }

        /*
          Portfolio history is optional for now.
          If the backend route is not available yet,
          the UI renders a clean empty state instead
          of inventing performance data.
        */
        if (portfolioHistoryResponse.ok) {
          const historyData =
            await portfolioHistoryResponse.json();

          if (
            !cancelled &&
            Array.isArray(historyData)
          ) {
            setPortfolioHistory(historyData);
          }
        }

        const wealthResponse = await fetch(
          `${API_BASE}/wealth-dna`,
          { headers }
        );

        if (wealthResponse.ok) {
          const wealthData =
            await wealthResponse.json();

          if (!cancelled) {
            setWealthDNA(wealthData);
          }
        } else if (
          wealthResponse.status === 404 &&
          riskExists &&
          goalsExist
        ) {
          const generateResponse = await fetch(
            `${API_BASE}/wealth-dna/generate`,
            {
              method: "POST",
              headers,
            }
          );

          if (generateResponse.ok) {
            const generatedData =
              await generateResponse.json();

            if (!cancelled) {
              setWealthDNA(generatedData);
            }
          }
        }
      } catch {
        if (!cancelled) {
          setError(
            "Could not connect to InvestiGenie backend."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadDashboard();

    return () => {
      cancelled = true;
    };
  }, [router]);

  const activeGoals = useMemo(
    () =>
      goals.filter(
        (goal) => goal.status === "ACTIVE"
      ).length,
    [goals]
  );

  const setupProgress = useMemo(() => {
    const complete = [
      !!financialProfile,
      !!riskProfile,
      activeGoals > 0,
      !!wealthDNA,
    ].filter(Boolean).length;

    return Math.round((complete / 4) * 100);
  }, [
    financialProfile,
    riskProfile,
    activeGoals,
    wealthDNA,
  ]);

  const firstName =
    user?.full_name?.trim().split(/\s+/)[0] ||
    "there";

  if (loading) {
    return <DashboardSkeleton />;
  }

  const sharedProps = {
    firstName,
    financialProfile,
    riskProfile,
    activeGoals,
    wealthDNA,
    setupProgress,
    portfolioSummary,
    portfolioHistory,
    theme,
    toggleTheme,
    router,
  };

  return (
    <main className="relative min-h-screen overflow-x-hidden bg-[var(--background)] text-[var(--foreground)]">
      <AmbientBackground />

      {error && (
        <div className="relative z-20 mx-4 mt-4 rounded-2xl border border-red-400/15 bg-red-400/[0.05] px-4 py-3 text-sm text-red-200/80 sm:mx-6 lg:mx-8">
          {error}
        </div>
      )}

      {/* Mobile is intentionally a different app experience. */}
      <div className="relative z-10 lg:hidden">
        <MobileDashboard {...sharedProps} />
      </div>

      {/* Desktop / laptop keeps a richer workspace layout. */}
      <div className="relative z-10 hidden lg:block">
        <DesktopDashboard {...sharedProps} />
      </div>
    </main>
  );
}

type DashboardViewProps = {
  firstName: string;
  financialProfile: FinancialProfile | null;
  riskProfile: RiskProfile | null;
  activeGoals: number;
  wealthDNA: WealthDNA | null;
  setupProgress: number;
  portfolioSummary: PortfolioSummary | null;
  portfolioHistory: PortfolioHistoryPoint[];
  theme: ThemeMode;
  toggleTheme: () => void;
  router: ReturnType<typeof useRouter>;
};

function MobileDashboard({
  firstName,
  financialProfile,
  riskProfile,
  activeGoals,
  wealthDNA,
  setupProgress,
  portfolioSummary,
  portfolioHistory,
  theme,
  toggleTheme,
  router,
}: DashboardViewProps) {
  return (
    <div className="mx-auto w-full max-w-xl px-4 pb-6 pt-4 sm:px-5">
      <section>
        <p className="text-xs font-medium text-white/35">
          Good to see you,
        </p>

        <div className="mt-1 flex items-end justify-between gap-4">
          <h1 className="text-[2.05rem] font-semibold leading-tight tracking-[-0.05em]">
            {firstName}
          </h1>

          <div className="flex items-center gap-2">
            <ThemeToggle
              theme={theme}
              onToggle={toggleTheme}
            />

            <button
              type="button"
              onClick={() =>
                router.push("/financial-profile")
              }
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border border-white/[0.07] bg-white/[0.025] text-white/45 active:scale-95"
              aria-label="Open financial profile"
            >
              <UserRound size={18} />
            </button>
          </div>
        </div>

        <p className="mt-2 max-w-sm text-sm leading-6 text-white/30">
          Your money at a glance.
        </p>
      </section>

      <section className="relative mt-5 overflow-hidden rounded-[28px] border border-emerald-400/15 bg-gradient-to-br from-emerald-400/[0.09] via-white/[0.035] to-cyan-400/[0.035] p-5 shadow-[0_24px_70px_rgba(0,0,0,.28)]">
        <div className="pointer-events-none absolute right-[-3rem] top-[-4rem] h-44 w-44 rounded-full bg-emerald-300/[0.12] blur-3xl" />

        <div className="relative">
          <div className="flex items-center justify-between gap-3">
            <p className="text-[10px] font-medium tracking-[0.16em] text-emerald-200/65">
              TOTAL NET WORTH
            </p>

            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/15 bg-emerald-400/[0.055] px-2.5 py-1 text-[10px] text-emerald-100/70">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-300" />
              Live
            </span>
          </div>

          <p className="mt-4 text-[2.8rem] font-semibold leading-none tracking-[-0.055em]">
            {financialProfile
              ? `₹${formatCompactMoney(
                  financialProfile.net_worth
                )}`
              : "—"}
          </p>

          <p className="mt-2 text-xs text-white/30">
            {financialProfile
              ? "From your financial profile"
              : "Complete your profile to activate this view"}
          </p>

          <div className="mt-6 grid grid-cols-2 gap-2.5">
            <MobileHeroMetric
              label="Wealth DNA"
              value={
                wealthDNA
                  ? `${Math.round(
                      wealthDNA.wealth_score
                    )}/100`
                  : "Locked"
              }
              accent
            />

            <MobileHeroMetric
              label="Risk profile"
              value={
                riskProfile?.risk_category ||
                "Pending"
              }
            />
          </div>
        </div>
      </section>

      <PortfolioGrowthCard
        summary={portfolioSummary}
        history={portfolioHistory}
        compact
        onOpenPortfolio={() =>
          router.push("/portfolio")
        }
      />

      <section className="mt-4">
        <div className="mb-2 flex items-center justify-between">
          <p className="text-xs font-medium text-white/55">
            Quick actions
          </p>
        </div>

        <div className="grid grid-cols-4 gap-2">
          <MobileQuickAction
            icon={Compass}
            label="Invest"
            onClick={() => router.push("/invest")}
            primary
          />
          <MobileQuickAction
            icon={WalletCards}
            label="Portfolio"
            onClick={() =>
              router.push("/portfolio")
            }
          />
          <MobileQuickAction
            icon={Target}
            label="Goals"
            onClick={() => router.push("/goals")}
          />
          <MobileQuickAction
            icon={Dna}
            label="Twin"
            onClick={() =>
              router.push("/financial-twin")
            }
          />
        </div>
      </section>

      <section className="mt-5 rounded-[24px] border border-white/[0.07] bg-white/[0.025] p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-2xl border border-emerald-400/15 bg-emerald-400/[0.06] text-emerald-200">
              <Sparkles size={17} />
            </div>

            <div>
              <p className="text-[10px] font-medium tracking-[0.14em] text-emerald-200/60">
                INVESTIGENIE AI
              </p>
              <p className="mt-0.5 text-sm font-medium">
                Your next best move
              </p>
            </div>
          </div>
        </div>

        <p className="mt-4 text-sm leading-6 text-white/38">
          {getInsightText(
            wealthDNA,
            riskProfile,
            activeGoals
          )}
        </p>

        <button
          type="button"
          onClick={() =>
            router.push(
              wealthDNA
                ? "/financial-twin"
                : riskProfile
                  ? "/goals"
                  : "/risk-assessment"
            )
          }
          className="mt-4 inline-flex min-h-10 items-center gap-2 text-sm font-medium text-emerald-200/80"
        >
          View recommendation
          <ArrowRight size={14} />
        </button>
      </section>

      <section className="mt-5">
        <div className="mb-2 flex items-center justify-between">
          <p className="text-xs font-medium text-white/55">
            Your progress
          </p>

          <span className="text-xs font-medium text-emerald-200/75">
            {setupProgress}%
          </span>
        </div>

        <div className="overflow-hidden rounded-[24px] border border-white/[0.07] bg-white/[0.025]">
          <div className="px-4 pt-4">
            <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.07]">
              <div
                className="h-full rounded-full bg-emerald-300"
                style={{
                  width: `${setupProgress}%`,
                }}
              />
            </div>
          </div>

          <MobileProgressRow
            label="Financial profile"
            value={
              financialProfile
                ? "Ready"
                : "Complete"
            }
            done={!!financialProfile}
            onClick={() =>
              router.push("/financial-profile")
            }
          />

          <MobileProgressRow
            label="Risk profile"
            value={
              riskProfile
                ? riskProfile.risk_category
                : "Complete"
            }
            done={!!riskProfile}
            onClick={() =>
              router.push("/risk-assessment")
            }
          />

          <MobileProgressRow
            label="Goals"
            value={`${activeGoals} active`}
            done={activeGoals > 0}
            onClick={() => router.push("/goals")}
          />

          <MobileProgressRow
            label="Wealth DNA"
            value={
              wealthDNA
                ? `${Math.round(
                    wealthDNA.wealth_score
                  )}/100`
                : "Locked"
            }
            done={!!wealthDNA}
            onClick={() =>
              router.push("/financial-twin")
            }
            last
          />
        </div>
      </section>

      <section className="mt-5">
        <p className="mb-2 text-xs font-medium text-white/55">
          Financial signals
        </p>

        <div className="grid grid-cols-2 gap-2.5">
          <MobileSignalCard
            label="Savings rate"
            value={
              financialProfile
                ? `${financialProfile.savings_rate.toFixed(
                    1
                  )}%`
                : "—"
            }
            icon={PiggyBank}
          />

          <MobileSignalCard
            label="Emergency cover"
            value={
              financialProfile
                ? `${financialProfile.emergency_months.toFixed(
                    1
                  )} mo`
                : "—"
            }
            icon={ShieldCheck}
          />

          <MobileSignalCard
            label="Investment ratio"
            value={
              financialProfile
                ? `${financialProfile.investment_ratio.toFixed(
                    1
                  )}%`
                : "—"
            }
            icon={TrendingUp}
          />

          <MobileSignalCard
            label="Active goals"
            value={String(activeGoals)}
            icon={Goal}
          />
        </div>
      </section>

      <section className="mt-5">
        <button
          type="button"
          onClick={() => router.push("/invest")}
          className="group w-full rounded-[24px] border border-emerald-400/15 bg-emerald-400/[0.055] p-4 text-left active:scale-[0.99]"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-300 text-[#04100c]">
              <Compass size={19} />
            </div>

            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold">
                Discover investments
              </p>
              <p className="mt-1 text-xs text-white/30">
                Explore opportunities matched to your profile.
              </p>
            </div>

            <ChevronRight
              size={18}
              className="text-emerald-200/70"
            />
          </div>
        </button>
      </section>
    </div>
  );
}

function DesktopDashboard({
  firstName,
  financialProfile,
  riskProfile,
  activeGoals,
  wealthDNA,
  setupProgress,
  portfolioSummary,
  portfolioHistory,
  theme,
  toggleTheme,
  router,
}: DashboardViewProps) {
  return (
    <div className="mx-auto w-full max-w-[1500px] px-8 pb-12 pt-8 xl:px-10">
      <section className="grid gap-5 xl:grid-cols-[1.45fr_.55fr]">
        <div className="relative overflow-hidden rounded-[32px] border border-white/[0.08] bg-white/[0.028] p-9 shadow-[0_30px_100px_rgba(0,0,0,.25)] backdrop-blur-2xl">
          <div className="pointer-events-none absolute right-[-5rem] top-[-7rem] h-72 w-72 rounded-full bg-emerald-300/[0.08] blur-[75px]" />

          <div className="relative">
            <div className="absolute right-0 top-0">
              <ThemeToggle
                theme={theme}
                onToggle={toggleTheme}
                withLabel
              />
            </div>

            <div className="flex items-center gap-2 pr-36 text-[11px] font-medium tracking-[0.17em] text-emerald-200/65">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-300 shadow-[0_0_10px_rgba(110,231,183,.8)]" />
              FINANCIAL INTELLIGENCE ACTIVE
            </div>

            <h1 className="mt-4 max-w-3xl text-6xl font-semibold leading-[1.02] tracking-[-0.05em]">
              Welcome back,
              <span className="text-white/35">
                {" "}
                {firstName}.
              </span>
            </h1>

            <p className="mt-4 max-w-2xl text-base leading-6 text-white/40">
              Your wealth, goals, risk and financial
              identity are connected in one decision
              workspace.
            </p>

            <div className="mt-6 flex gap-2.5">
              <button
                type="button"
                onClick={() =>
                  router.push(
                    wealthDNA
                      ? "/financial-twin"
                      : financialProfile
                        ? riskProfile
                          ? "/goals"
                          : "/risk-assessment"
                        : "/financial-profile"
                  )
                }
                className="inline-flex items-center justify-center gap-2 rounded-full bg-emerald-300 px-5 py-3 text-sm font-semibold text-[#04100c] transition hover:bg-emerald-200"
              >
                {wealthDNA
                  ? "Open Financial Twin"
                  : "Continue setup"}
                <ArrowRight size={16} />
              </button>

              <button
                type="button"
                onClick={() =>
                  router.push("/invest")
                }
                className="inline-flex items-center justify-center gap-2 rounded-full border border-white/[0.09] bg-white/[0.035] px-5 py-3 text-sm font-medium text-white/65 transition hover:bg-white/[0.06] hover:text-white"
              >
                Discover investments
              </button>
            </div>

            <div className="mt-7 grid grid-cols-4 gap-2.5">
              <MiniStat
                label="Net worth"
                value={
                  financialProfile
                    ? `₹${formatCompactMoney(
                        financialProfile.net_worth
                      )}`
                    : "—"
                }
              />
              <MiniStat
                label="Risk"
                value={
                  riskProfile?.risk_category ||
                  "Pending"
                }
              />
              <MiniStat
                label="Goals"
                value={String(activeGoals)}
              />
              <MiniStat
                label="Setup"
                value={`${setupProgress}%`}
              />
            </div>
          </div>
        </div>

        <InsightCard
          wealthDNA={wealthDNA}
          riskProfile={riskProfile}
          activeGoals={activeGoals}
          onAction={() =>
            router.push(
              wealthDNA
                ? "/financial-twin"
                : riskProfile
                  ? "/goals"
                  : "/risk-assessment"
            )
          }
        />
      </section>

      <PortfolioGrowthCard
        summary={portfolioSummary}
        history={portfolioHistory}
        onOpenPortfolio={() =>
          router.push("/portfolio")
        }
      />

      <section className="mt-5 grid grid-cols-4 gap-3">
        <QuickMetric
          icon={Landmark}
          label="Net Worth"
          value={
            financialProfile
              ? `₹${formatCompactMoney(
                  financialProfile.net_worth
                )}`
              : "—"
          }
          detail={
            financialProfile
              ? "Financial position"
              : "Complete profile"
          }
        />

        <QuickMetric
          icon={Dna}
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
          accent
        />

        <QuickMetric
          icon={ShieldCheck}
          label="Risk"
          value={
            riskProfile?.risk_category ||
            "Pending"
          }
          detail={
            riskProfile
              ? `${Math.round(
                  riskProfile.final_risk_score
                )}/100 score`
              : "Assessment required"
          }
        />

        <QuickMetric
          icon={Target}
          label="Goals"
          value={String(activeGoals)}
          detail={
            activeGoals === 1
              ? "Active goal"
              : "Active goals"
          }
        />
      </section>

      <section className="mt-5 grid gap-5 xl:grid-cols-[1.15fr_.85fr]">
        <FinancialSignalsCard
          profile={financialProfile}
          onComplete={() =>
            router.push("/financial-profile")
          }
        />

        <SetupJourneyCard
          financialProfile={financialProfile}
          riskProfile={riskProfile}
          activeGoals={activeGoals}
          wealthDNA={wealthDNA}
          progress={setupProgress}
          onNavigate={(href) =>
            router.push(href)
          }
        />
      </section>

      <section className="mt-5">
        <div className="mb-3 flex items-end justify-between gap-4">
          <div>
            <p className="text-[10px] font-medium uppercase tracking-[0.17em] text-white/25">
              YOUR WORKSPACE
            </p>
            <h2 className="mt-2 text-2xl font-semibold tracking-[-0.035em]">
              Everything connected in one place
            </h2>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <WorkspaceCard
            icon={WalletCards}
            eyebrow="PORTFOLIO"
            title="Your investments"
            description="Track holdings, value, allocation and gains."
            status="Open portfolio"
            onClick={() =>
              router.push("/portfolio")
            }
          />

          <WorkspaceCard
            icon={Compass}
            eyebrow="DISCOVER"
            title="Investment explorer"
            description="Explore funds and opportunities matched to your profile."
            status="Explore"
            onClick={() => router.push("/invest")}
            accent
          />

          <WorkspaceCard
            icon={Goal}
            eyebrow="GOALS"
            title="Financial goals"
            description={
              activeGoals
                ? `${activeGoals} active ${
                    activeGoals === 1
                      ? "goal"
                      : "goals"
                  } being tracked.`
                : "Create your first financial goal."
            }
            status="Manage goals"
            onClick={() => router.push("/goals")}
          />

          <WorkspaceCard
            icon={BrainCircuit}
            eyebrow="DIGITAL TWIN"
            title="Future trajectory"
            description={
              wealthDNA
                ? "Model your future financial path and priorities."
                : "Unlock after your financial identity is ready."
            }
            status={
              wealthDNA ? "Open Twin" : "Locked"
            }
            onClick={
              wealthDNA
                ? () =>
                    router.push(
                      "/financial-twin"
                    )
                : undefined
            }
          />
        </div>
      </section>

      {wealthDNA && (
        <section className="mt-5">
          <WealthDNACard
            wealthDNA={wealthDNA}
            onOpenTwin={() =>
              router.push("/financial-twin")
            }
          />
        </section>
      )}

      <section className="mt-5 grid gap-3 lg:grid-cols-3">
        <ActionCard
          icon={PiggyBank}
          title="Improve savings"
          text={
            financialProfile
              ? `Your current savings rate is ${financialProfile.savings_rate.toFixed(
                  1
                )}%.`
              : "Complete your profile to measure your savings discipline."
          }
          button="Financial profile"
          onClick={() =>
            router.push("/financial-profile")
          }
        />

        <ActionCard
          icon={TrendingUp}
          title="Build intelligently"
          text="Use your risk profile and goals to discover suitable investment opportunities."
          button="Discover investments"
          onClick={() => router.push("/invest")}
        />

        <ActionCard
          icon={ShieldCheck}
          title="Know your risk"
          text={
            riskProfile
              ? `Your current risk category is ${riskProfile.risk_category}.`
              : "Complete your risk assessment before making personalized investment decisions."
          }
          button="Risk assessment"
          onClick={() =>
            router.push("/risk-assessment")
          }
        />
      </section>
    </div>
  );
}

function MobileHeroMetric({
  label,
  value,
  accent = false,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className="rounded-2xl border border-white/[0.07] bg-black/10 px-3.5 py-3.5">
      <p className="text-[9px] uppercase tracking-[0.12em] text-white/25">
        {label}
      </p>

      <p
        className={`mt-2 truncate text-base font-semibold ${
          accent
            ? "text-emerald-200"
            : "text-white"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

function MobileQuickAction({
  icon: Icon,
  label,
  onClick,
  primary = false,
}: {
  icon: typeof Compass;
  label: string;
  onClick: () => void;
  primary?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex min-w-0 flex-col items-center gap-2 rounded-[20px] border border-white/[0.06] bg-white/[0.02] px-2 py-3 active:scale-[0.97]"
    >
      <span
        className={`flex h-10 w-10 items-center justify-center rounded-2xl ${
          primary
            ? "bg-emerald-300 text-[#04100c]"
            : "border border-white/[0.07] bg-white/[0.035] text-white/45"
        }`}
      >
        <Icon size={18} />
      </span>

      <span className="w-full truncate text-center text-[10px] text-white/42">
        {label}
      </span>
    </button>
  );
}

function MobileProgressRow({
  label,
  value,
  done,
  onClick,
  last = false,
}: {
  label: string;
  value: string;
  done: boolean;
  onClick: () => void;
  last?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex min-h-14 w-full items-center gap-3 px-4 text-left ${
        last
          ? ""
          : "border-b border-white/[0.05]"
      }`}
    >
      <span
        className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-[10px] ${
          done
            ? "border-emerald-300/20 bg-emerald-300/[0.1] text-emerald-200"
            : "border-white/[0.08] bg-white/[0.025] text-white/30"
        }`}
      >
        {done ? "✓" : "•"}
      </span>

      <span className="min-w-0 flex-1 truncate text-sm text-white/55">
        {label}
      </span>

      <span className="max-w-[120px] truncate text-xs text-white/25">
        {value}
      </span>

      <ChevronRight
        size={15}
        className="shrink-0 text-white/18"
      />
    </button>
  );
}

function MobileSignalCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string;
  icon: typeof PiggyBank;
}) {
  return (
    <div className="rounded-[20px] border border-white/[0.065] bg-white/[0.022] p-4">
      <Icon
        size={17}
        strokeWidth={1.8}
        className="text-white/30"
      />

      <p className="mt-4 text-[9px] uppercase tracking-[0.11em] text-white/22">
        {label}
      </p>

      <p className="mt-1.5 text-lg font-semibold">
        {value}
      </p>
    </div>
  );
}

function AmbientBackground() {
  return (
    <div className="pointer-events-none fixed inset-0">
      <div className="absolute left-[8%] top-[-13rem] h-[30rem] w-[30rem] rounded-full bg-emerald-400/[0.055] blur-[120px]" />
      <div className="absolute right-[-10rem] top-[20rem] h-[28rem] w-[28rem] rounded-full bg-cyan-400/[0.035] blur-[120px]" />
      <div
        className="absolute inset-0 opacity-[0.09]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px)",
          backgroundSize: "72px 72px",
          maskImage:
            "linear-gradient(to bottom, black, transparent 90%)",
        }}
      />
    </div>
  );
}

function InsightCard({
  wealthDNA,
  riskProfile,
  activeGoals,
  onAction,
}: {
  wealthDNA: WealthDNA | null;
  riskProfile: RiskProfile | null;
  activeGoals: number;
  onAction: () => void;
}) {
  return (
    <div className="relative overflow-hidden rounded-[32px] border border-emerald-400/15 bg-gradient-to-b from-emerald-400/[0.075] to-emerald-400/[0.025] p-7">
      <div className="pointer-events-none absolute right-[-4rem] top-[-4rem] h-48 w-48 rounded-full bg-emerald-300/[0.11] blur-3xl" />

      <div className="relative flex h-full flex-col">
        <div className="flex items-center justify-between">
          <p className="text-[10px] font-medium tracking-[0.17em] text-emerald-200/65">
            INVESTIGENIE INSIGHT
          </p>

          <Sparkles
            size={18}
            className="text-emerald-200/70"
          />
        </div>

        <h2 className="mt-6 text-3xl font-semibold leading-tight tracking-[-0.035em]">
          {getInsightTitle(
            wealthDNA,
            riskProfile,
            activeGoals
          )}
        </h2>

        <p className="mt-4 text-sm leading-6 text-white/42">
          {getInsightText(
            wealthDNA,
            riskProfile,
            activeGoals
          )}
        </p>

        <div className="mt-auto pt-7">
          <button
            type="button"
            onClick={onAction}
            className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-emerald-300/15 bg-emerald-300/[0.07] px-4 text-sm font-medium text-emerald-100 transition hover:bg-emerald-300/[0.11]"
          >
            Continue
            <ArrowRight size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}

function getInsightTitle(
  wealthDNA: WealthDNA | null,
  riskProfile: RiskProfile | null,
  activeGoals: number
) {
  if (wealthDNA) {
    return `You are a ${wealthDNA.investor_personality}.`;
  }

  if (riskProfile && activeGoals === 0) {
    return "Your risk profile is ready.";
  }

  return "Complete your financial identity.";
}

function getInsightText(
  wealthDNA: WealthDNA | null,
  riskProfile: RiskProfile | null,
  activeGoals: number
) {
  if (wealthDNA) {
    return `Your strongest trait is ${
      wealthDNA.strongest_trait ||
      "still developing"
    }. Focus next on ${
      wealthDNA.improvement_area ||
      "building consistency"
    }.`;
  }

  if (riskProfile && activeGoals === 0) {
    return "Create at least one financial goal to connect your risk profile with your future financial plan.";
  }

  return "Finish your financial profile and risk assessment so InvestiGenie can personalize your recommendations.";
}

function MiniStat({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-white/[0.065] bg-black/10 px-4 py-3.5">
      <p className="text-[9px] uppercase tracking-[0.12em] text-white/25">
        {label}
      </p>

      <p className="mt-2 truncate text-lg font-semibold tracking-[-0.02em]">
        {value}
      </p>
    </div>
  );
}

function QuickMetric({
  icon: Icon,
  label,
  value,
  detail,
  accent = false,
}: {
  icon: typeof Landmark;
  label: string;
  value: string;
  detail: string;
  accent?: boolean;
}) {
  return (
    <div
      className={`rounded-[22px] border p-5 ${
        accent
          ? "border-emerald-400/15 bg-emerald-400/[0.045]"
          : "border-white/[0.07] bg-white/[0.025]"
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <Icon
          size={18}
          strokeWidth={1.8}
          className={
            accent
              ? "text-emerald-300"
              : "text-white/35"
          }
        />
      </div>

      <p className="mt-5 text-[10px] uppercase tracking-[0.12em] text-white/25">
        {label}
      </p>

      <p
        className={`mt-1.5 truncate text-xl font-semibold tracking-[-0.025em] ${
          accent
            ? "text-emerald-200"
            : "text-white"
        }`}
      >
        {value}
      </p>

      <p className="mt-1.5 truncate text-xs text-white/28">
        {detail}
      </p>
    </div>
  );
}

function FinancialSignalsCard({
  profile,
  onComplete,
}: {
  profile: FinancialProfile | null;
  onComplete: () => void;
}) {
  return (
    <div className="rounded-[26px] border border-white/[0.075] bg-white/[0.025] p-7">
      <p className="text-[10px] font-medium uppercase tracking-[0.17em] text-white/25">
        FINANCIAL SIGNALS
      </p>

      <h2 className="mt-2 text-2xl font-semibold tracking-[-0.035em]">
        Your financial foundation
      </h2>

      {profile ? (
        <div className="mt-6 grid grid-cols-5 gap-3">
          <SignalCard
            label="Net Worth"
            value={`₹${formatCompactMoney(
              profile.net_worth
            )}`}
            score={
              profile.net_worth > 0 ? 100 : 10
            }
          />

          <SignalCard
            label="Savings"
            value={`${profile.savings_rate.toFixed(
              1
            )}%`}
            score={
              (profile.savings_rate / 30) * 100
            }
          />

          <SignalCard
            label="Debt / Income"
            value={`${profile.debt_to_income_ratio.toFixed(
              1
            )}%`}
            score={
              100 -
              profile.debt_to_income_ratio
            }
          />

          <SignalCard
            label="Emergency"
            value={`${profile.emergency_months.toFixed(
              1
            )} mo`}
            score={
              (profile.emergency_months / 6) *
              100
            }
          />

          <SignalCard
            label="Invested"
            value={`${profile.investment_ratio.toFixed(
              1
            )}%`}
            score={profile.investment_ratio * 2}
          />
        </div>
      ) : (
        <div className="mt-6 rounded-2xl border border-dashed border-white/[0.08] bg-black/10 p-7">
          <p className="font-medium">
            Financial profile incomplete
          </p>

          <p className="mt-2 max-w-xl text-sm leading-6 text-white/35">
            Add your income, expenses, assets and
            liabilities to activate your financial
            signals.
          </p>

          <button
            type="button"
            onClick={onComplete}
            className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-emerald-200"
          >
            Complete profile
            <ArrowRight size={15} />
          </button>
        </div>
      )}
    </div>
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
      <p className="text-[9px] uppercase tracking-[0.11em] text-white/24">
        {label}
      </p>

      <p className="mt-2.5 truncate text-lg font-semibold">
        {value}
      </p>

      <div className="mt-4 h-1 overflow-hidden rounded-full bg-white/[0.07]">
        <div
          className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-emerald-200"
          style={{
            width: `${safeScore}%`,
          }}
        />
      </div>
    </div>
  );
}

function SetupJourneyCard({
  financialProfile,
  riskProfile,
  activeGoals,
  wealthDNA,
  progress,
  onNavigate,
}: {
  financialProfile: FinancialProfile | null;
  riskProfile: RiskProfile | null;
  activeGoals: number;
  wealthDNA: WealthDNA | null;
  progress: number;
  onNavigate: (href: string) => void;
}) {
  const steps = [
    [
      "Financial profile",
      !!financialProfile,
      "/financial-profile",
    ],
    [
      "Risk assessment",
      !!riskProfile,
      "/risk-assessment",
    ],
    [
      "Create a goal",
      activeGoals > 0,
      "/goals",
    ],
    [
      "Wealth DNA",
      !!wealthDNA,
      "/financial-twin",
    ],
  ] as const;

  return (
    <div className="rounded-[26px] border border-white/[0.075] bg-white/[0.025] p-7">
      <div className="flex items-end justify-between gap-5">
        <div>
          <p className="text-[10px] font-medium uppercase tracking-[0.17em] text-white/25">
            FINANCIAL IDENTITY
          </p>

          <h2 className="mt-2 text-2xl font-semibold tracking-[-0.035em]">
            Your setup journey
          </h2>
        </div>

        <div className="text-right">
          <p className="text-2xl font-semibold text-emerald-200">
            {progress}%
          </p>
          <p className="text-[10px] text-white/25">
            complete
          </p>
        </div>
      </div>

      <div className="mt-5 h-1.5 overflow-hidden rounded-full bg-white/[0.07]">
        <div
          className="h-full rounded-full bg-emerald-300"
          style={{
            width: `${progress}%`,
          }}
        />
      </div>

      <div className="mt-6 space-y-2">
        {steps.map(
          ([label, done, href], index) => (
            <button
              key={label}
              type="button"
              onClick={() =>
                onNavigate(href)
              }
              className="flex min-h-12 w-full items-center gap-3 rounded-2xl border border-white/[0.05] bg-black/10 px-4 text-left transition hover:border-white/[0.09] hover:bg-white/[0.025]"
            >
              <span
                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-[10px] ${
                  done
                    ? "border-emerald-300/20 bg-emerald-300/[0.1] text-emerald-200"
                    : "border-white/[0.08] bg-white/[0.025] text-white/30"
                }`}
              >
                {done ? "✓" : index + 1}
              </span>

              <span
                className={
                  done
                    ? "text-sm text-white/65"
                    : "text-sm text-white/45"
                }
              >
                {label}
              </span>

              <ArrowRight
                size={15}
                className="ml-auto text-white/20"
              />
            </button>
          )
        )}
      </div>
    </div>
  );
}

function WorkspaceCard({
  icon: Icon,
  eyebrow,
  title,
  description,
  status,
  onClick,
  accent = false,
}: {
  icon: typeof WalletCards;
  eyebrow: string;
  title: string;
  description: string;
  status: string;
  onClick?: () => void;
  accent?: boolean;
}) {
  return (
    <button
      type="button"
      disabled={!onClick}
      onClick={onClick}
      className={`group min-h-[190px] rounded-[24px] border p-6 text-left transition duration-300 ${
        accent
          ? "border-emerald-400/15 bg-emerald-400/[0.045]"
          : "border-white/[0.07] bg-white/[0.025]"
      } ${
        onClick
          ? "hover:-translate-y-1 hover:border-emerald-400/20 hover:bg-white/[0.04]"
          : ""
      }`}
    >
      <div className="flex items-center justify-between">
        <span
          className={`flex h-10 w-10 items-center justify-center rounded-2xl border ${
            accent
              ? "border-emerald-400/20 bg-emerald-400/[0.08] text-emerald-200"
              : "border-white/[0.07] bg-white/[0.025] text-white/40"
          }`}
        >
          <Icon
            size={19}
            strokeWidth={1.8}
          />
        </span>

        <p className="text-[9px] font-medium tracking-[0.15em] text-white/22">
          {eyebrow}
        </p>
      </div>

      <h3 className="mt-5 text-lg font-semibold tracking-[-0.025em]">
        {title}
      </h3>

      <p className="mt-2 min-h-10 text-sm leading-5 text-white/30">
        {description}
      </p>

      <div
        className={`mt-5 flex items-center gap-2 text-sm ${
          accent
            ? "text-emerald-200"
            : "text-white/45"
        }`}
      >
        {status}
        {onClick && (
          <ArrowRight
            size={15}
            className="transition group-hover:translate-x-1"
          />
        )}
      </div>
    </button>
  );
}

function WealthDNACard({
  wealthDNA,
  onOpenTwin,
}: {
  wealthDNA: WealthDNA;
  onOpenTwin: () => void;
}) {
  const stats = [
    [
      "Stability",
      wealthDNA.financial_stability_score,
    ],
    [
      "Savings",
      wealthDNA.savings_discipline_score,
    ],
    ["Debt", wealthDNA.debt_health_score],
    [
      "Emergency",
      wealthDNA.emergency_preparedness_score,
    ],
    [
      "Investing",
      wealthDNA.investment_readiness_score,
    ],
    [
      "Goals",
      wealthDNA.goal_readiness_score,
    ],
    [
      "Risk Fit",
      wealthDNA.risk_alignment_score,
    ],
  ] as const;

  return (
    <div className="overflow-hidden rounded-[28px] border border-white/[0.075] bg-white/[0.025] p-8">
      <div className="flex items-end justify-between gap-6">
        <div>
          <p className="text-[10px] font-medium tracking-[0.17em] text-emerald-200/65">
            WEALTH DNA
          </p>

          <h2 className="mt-3 text-3xl font-semibold tracking-[-0.04em]">
            {wealthDNA.investor_personality}
          </h2>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-white/35">
            A live view of your financial
            behaviour, readiness and resilience.
          </p>
        </div>

        <div className="flex items-end gap-2">
          <span className="text-6xl font-semibold tracking-[-0.05em] text-emerald-200">
            {Math.round(
              wealthDNA.wealth_score
            )}
          </span>

          <span className="pb-1.5 text-sm text-white/20">
            /100
          </span>
        </div>
      </div>

      <div className="mt-7 grid grid-cols-7 gap-2.5">
        {stats.map(([label, value]) => (
          <div
            key={label}
            className="rounded-[18px] border border-white/[0.06] bg-black/10 p-4"
          >
            <div className="flex items-center justify-between gap-2">
              <p className="truncate text-[10px] text-white/28">
                {label}
              </p>

              <p className="text-sm font-semibold text-emerald-200">
                {Math.round(value)}
              </p>
            </div>

            <div className="mt-3 h-1 overflow-hidden rounded-full bg-white/[0.07]">
              <div
                className="h-full rounded-full bg-emerald-300"
                style={{
                  width: `${Math.min(
                    Math.max(value, 0),
                    100
                  )}%`,
                }}
              />
            </div>
          </div>
        ))}
      </div>

      <button
        type="button"
        onClick={onOpenTwin}
        className="mt-6 inline-flex min-h-11 items-center gap-2 rounded-xl border border-emerald-400/15 bg-emerald-400/[0.06] px-4 text-sm font-medium text-emerald-200 transition hover:bg-emerald-400/[0.1]"
      >
        Open Financial Twin
        <ArrowRight size={15} />
      </button>
    </div>
  );
}

function ActionCard({
  icon: Icon,
  title,
  text,
  button,
  onClick,
}: {
  icon: typeof PiggyBank;
  title: string;
  text: string;
  button: string;
  onClick: () => void;
}) {
  return (
    <div className="rounded-[22px] border border-white/[0.065] bg-white/[0.022] p-5">
      <Icon
        size={19}
        className="text-white/35"
        strokeWidth={1.8}
      />

      <h3 className="mt-4 text-base font-semibold tracking-[-0.02em]">
        {title}
      </h3>

      <p className="mt-2 min-h-10 text-sm leading-5 text-white/30">
        {text}
      </p>

      <button
        type="button"
        onClick={onClick}
        className="mt-4 inline-flex min-h-10 items-center gap-2 text-sm font-medium text-emerald-200/80 transition hover:text-emerald-200"
      >
        {button}
        <ArrowRight size={14} />
      </button>
    </div>
  );
}


function ThemeToggle({
  theme,
  onToggle,
  withLabel = false,
}: {
  theme: ThemeMode;
  onToggle: () => void;
  withLabel?: boolean;
}) {
  const light = theme === "light";

  return (
    <button
      type="button"
      onClick={onToggle}
      className={`ig-theme-toggle inline-flex h-10 items-center justify-center gap-2 rounded-2xl border px-3 ${
        withLabel ? "min-w-[118px]" : "w-10"
      }`}
      aria-label={
        light
          ? "Switch to dark mode"
          : "Switch to light mode"
      }
      title={
        light
          ? "Switch to dark mode"
          : "Switch to light mode"
      }
    >
      {light ? (
        <Moon size={16} />
      ) : (
        <Sun size={16} />
      )}

      {withLabel && (
        <span className="text-xs font-medium">
          {light ? "Dark mode" : "Light mode"}
        </span>
      )}
    </button>
  );
}

function PortfolioGrowthCard({
  summary,
  history,
  onOpenPortfolio,
  compact = false,
}: {
  summary: PortfolioSummary | null;
  history: PortfolioHistoryPoint[];
  onOpenPortfolio: () => void;
  compact?: boolean;
}) {
  const [range, setRange] = useState<
    "1M" | "3M" | "6M" | "1Y" | "ALL"
  >("1Y");

  const points = useMemo(() => {
    const clean = history
      .filter(
        (point) =>
          point?.date &&
          Number.isFinite(point.market_value) &&
          Number.isFinite(point.invested_value)
      )
      .map((point) => ({
        ...point,
        timestamp: new Date(
          `${point.date}T00:00:00`
        ).getTime(),
      }))
      .filter((point) =>
        Number.isFinite(point.timestamp)
      )
      .sort(
        (a, b) => a.timestamp - b.timestamp
      );

    if (
      range === "ALL" ||
      clean.length === 0
    ) {
      return clean;
    }

    const latest =
      clean[clean.length - 1].timestamp;

    const days =
      range === "1M"
        ? 31
        : range === "3M"
          ? 93
          : range === "6M"
            ? 186
            : 366;

    const cutoff =
      latest - days * 24 * 60 * 60 * 1000;

    return clean.filter(
      (point) => point.timestamp >= cutoff
    );
  }, [history, range]);

  const chart = useMemo(() => {
    if (points.length < 2) {
      return null;
    }

    const width = 1000;
    const height = compact ? 230 : 300;
    const left = 10;
    const right = 10;
    const top = 18;
    const bottom = 18;

    const values = points.flatMap((point) => [
      point.market_value,
      point.invested_value,
    ]);

    let min = Math.min(...values);
    let max = Math.max(...values);

    if (max === min) {
      max += 1;
      min -= 1;
    }

    const padding = (max - min) * 0.1;
    min -= padding;
    max += padding;

    const x = (index: number) =>
      left +
      (index / (points.length - 1)) *
        (width - left - right);

    const y = (value: number) =>
      top +
      ((max - value) / (max - min)) *
        (height - top - bottom);

    const market = points
      .map(
        (point, index) =>
          `${x(index)},${y(point.market_value)}`
      )
      .join(" ");

    const invested = points
      .map(
        (point, index) =>
          `${x(index)},${y(point.invested_value)}`
      )
      .join(" ");

    const area = [
      `${x(0)},${height - bottom}`,
      ...points.map(
        (point, index) =>
          `${x(index)},${y(point.market_value)}`
      ),
      `${x(
        points.length - 1
      )},${height - bottom}`,
    ].join(" ");

    return {
      width,
      height,
      market,
      invested,
      area,
      min,
      max,
    };
  }, [points, compact]);

  const current =
    summary?.current_value ?? 0;
  const invested =
    summary?.total_invested ?? 0;
  const gain =
    summary?.total_gain ?? current - invested;
  const positive = gain >= 0;

  return (
    <section
      className={`mt-5 overflow-hidden rounded-[28px] border border-white/[0.075] bg-white/[0.025] ${
        compact ? "p-4" : "p-7"
      }`}
    >
      <div
        className={`flex ${
          compact
            ? "flex-col gap-3"
            : "items-start justify-between gap-5"
        }`}
      >
        <div>
          <div className="flex items-center gap-2">
            <LineChart
              size={16}
              className="text-emerald-300"
            />
            <p className="text-[10px] font-medium uppercase tracking-[0.16em] text-emerald-200/65">
              Portfolio growth
            </p>
          </div>

          <div className="mt-2 flex flex-wrap items-end gap-x-4 gap-y-1">
            <p
              className={`font-semibold tracking-[-0.04em] ${
                compact
                  ? "text-2xl"
                  : "text-3xl"
              }`}
            >
              ₹{formatCompactMoney(current)}
            </p>

            {summary && (
              <p
                className={`pb-1 text-sm font-medium ${
                  positive
                    ? "text-emerald-300"
                    : "text-red-300"
                }`}
              >
                {positive ? "+" : ""}
                {summary.total_gain_percentage.toFixed(
                  2
                )}
                %
              </p>
            )}
          </div>

          <p className="mt-1 text-xs text-white/30">
            Current value vs. invested capital over
            time
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-1 rounded-2xl border border-white/[0.06] bg-black/10 p-1">
          {(
            ["1M", "3M", "6M", "1Y", "ALL"] as const
          ).map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => setRange(item)}
              className={`min-h-8 rounded-xl px-2.5 text-[10px] font-medium transition ${
                range === item
                  ? "bg-emerald-300 text-[#04100c]"
                  : "text-white/35 hover:text-white/70"
              }`}
            >
              {item}
            </button>
          ))}
        </div>
      </div>

      {chart ? (
        <div className="mt-5">
          <svg
            viewBox={`0 0 ${chart.width} ${chart.height}`}
            className="block w-full"
            role="img"
            aria-label="Portfolio market value and invested value over time"
          >
            <defs>
              <linearGradient
                id="portfolioGrowthArea"
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop
                  offset="0%"
                  stopColor="var(--accent)"
                  stopOpacity="0.22"
                />
                <stop
                  offset="100%"
                  stopColor="var(--accent)"
                  stopOpacity="0"
                />
              </linearGradient>
            </defs>

            {[0.25, 0.5, 0.75].map(
              (ratio) => (
                <line
                  key={ratio}
                  x1="10"
                  x2="990"
                  y1={chart.height * ratio}
                  y2={chart.height * ratio}
                  className="ig-growth-grid"
                  strokeWidth="1"
                />
              )
            )}

            <polygon
              points={chart.area}
              className="ig-growth-area"
            />

            <polyline
              points={chart.invested}
              className="ig-invested-line"
            />

            <polyline
              points={chart.market}
              className="ig-growth-line"
            />
          </svg>

          <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex flex-wrap items-center gap-4 text-white/35">
              <span className="inline-flex items-center gap-2">
                <span className="h-2 w-5 rounded-full bg-emerald-300" />
                Portfolio value
              </span>
              <span className="inline-flex items-center gap-2">
                <span className="h-px w-5 bg-white/30" />
                Invested
              </span>
            </div>

            <div className="flex items-center gap-4">
              <span className="text-white/30">
                Invested ₹
                {formatCompactMoney(invested)}
              </span>
              <span
                className={
                  positive
                    ? "text-emerald-300"
                    : "text-red-300"
                }
              >
                {positive ? "+" : ""}
                ₹{formatCompactMoney(gain)}
              </span>
            </div>
          </div>
        </div>
      ) : (
        <div className="mt-5 overflow-hidden rounded-[22px] border border-dashed border-white/[0.08] bg-black/10">
          <div className="relative h-44">
            <svg
              viewBox="0 0 1000 220"
              className="absolute inset-0 h-full w-full opacity-70"
              aria-hidden="true"
            >
              {[55, 110, 165].map((y) => (
                <line
                  key={y}
                  x1="0"
                  x2="1000"
                  y1={y}
                  y2={y}
                  className="ig-growth-grid"
                  strokeWidth="1"
                />
              ))}
            </svg>

            <div className="relative flex h-full flex-col items-center justify-center px-6 text-center">
              <LineChart
                size={24}
                className="text-emerald-300/70"
              />
              <p className="mt-3 text-sm font-medium">
                Portfolio growth is ready for history
                data
              </p>
              <p className="mt-1 max-w-md text-xs leading-5 text-white/30">
                The graph will plot automatically once
                portfolio snapshots are available. No
                artificial performance data is shown.
              </p>

              <button
                type="button"
                onClick={onOpenPortfolio}
                className="mt-3 text-xs font-medium text-emerald-200"
              >
                Open portfolio →
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

function DashboardSkeleton() {
  return (
    <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <div className="lg:hidden">
        <div className="mx-auto max-w-xl animate-pulse px-4 pb-6 pt-4">
          <div className="h-6 w-28 rounded-lg bg-white/[0.04]" />
          <div className="mt-2 h-10 w-44 rounded-xl bg-white/[0.04]" />
          <div className="mt-5 h-56 rounded-[28px] border border-white/[0.06] bg-white/[0.025]" />
          <div className="mt-4 grid grid-cols-4 gap-2">
            {Array.from({ length: 4 }).map(
              (_, index) => (
                <div
                  key={index}
                  className="h-20 rounded-[20px] border border-white/[0.06] bg-white/[0.02]"
                />
              )
            )}
          </div>
          <div className="mt-5 h-44 rounded-[24px] border border-white/[0.06] bg-white/[0.02]" />
        </div>
      </div>

      <div className="hidden animate-pulse px-8 py-8 lg:block">
        <div className="mx-auto max-w-[1500px]">
          <div className="grid gap-5 xl:grid-cols-[1.45fr_.55fr]">
            <div className="h-[360px] rounded-[28px] border border-white/[0.06] bg-white/[0.025]" />
            <div className="h-[360px] rounded-[28px] border border-white/[0.06] bg-white/[0.025]" />
          </div>

          <div className="mt-5 grid grid-cols-4 gap-3">
            {Array.from({ length: 4 }).map(
              (_, index) => (
                <div
                  key={index}
                  className="h-32 rounded-[22px] border border-white/[0.06] bg-white/[0.02]"
                />
              )
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

function formatCompactMoney(
  value: number
) {
  const abs = Math.abs(value);

  if (abs >= 10_000_000) {
    return `${(
      value / 10_000_000
    ).toFixed(2)}Cr`;
  }

  if (abs >= 100_000) {
    return `${(
      value / 100_000
    ).toFixed(2)}L`;
  }

  if (abs >= 1_000) {
    return `${(
      value / 1_000
    ).toFixed(1)}K`;
  }

  return new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 0,
  }).format(value);
}