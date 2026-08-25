"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useParams,
  useRouter,
} from "next/navigation";

import {
  ArrowLeft,
  ArrowRight,
  CircleHelp,
  Gauge,
  LockKeyhole,
  Sparkles,
  Star,
  Trophy,
  UsersRound,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

const API_BASE = "/api-backend";


type InvestmentProduct = {
  id: number;
  name: string;
  product_type: string;

  isin: string | null;
  symbol: string | null;
  scheme_code?: string | null;

  provider: string | null;

  category: string | null;
  sub_category: string | null;
  asset_class: string | null;

  plan_type?: string | null;
  option_type?: string | null;

  risk_level: string | null;
  riskometer?: string | null;

  nav: number;
  nav_date?: string | null;

  previous_nav?: number | null;
  daily_change?: number | null;
  daily_change_percentage?: number | null;

  aum?: number | null;
  expense_ratio: number;

  exit_load?: string | null;
  benchmark?: string | null;

  launch_date?: string | null;
  fund_manager?: string | null;

  investment_objective?: string | null;

  minimum_sip: number;
  minimum_lumpsum: number;

  return_1d?: number | null;
  return_1m?: number | null;
  return_3m?: number | null;
  return_6m?: number | null;

  return_1y: number;
  return_3y: number;
  return_5y: number;

  volatility: number;

  alpha?: number | null;
  beta?: number | null;
  sharpe_ratio?: number | null;
  standard_deviation?: number | null;

  equity_percentage?: number | null;
  debt_percentage?: number | null;
  cash_percentage?: number | null;

  large_cap_percentage?: number | null;
  mid_cap_percentage?: number | null;
  small_cap_percentage?: number | null;

  purchase_allowed: boolean;
  sip_allowed: boolean;

  source: string;

  data_updated_at?: string | null;

  fund_health_score?: number | null;
  fund_status?: string | null;
  peer_percentile?: number | null;
  data_quality_score?: number | null;
};


type NAVPoint = {
  id: number;
  product_id: number;

  nav_date: string;
  nav: number;

  daily_change: number | null;
  daily_change_percentage: number | null;
};


type FundAnalytics = {
  product_id: number;

  scheme_code: string | null;
  name: string;

  nav?: number;
  nav_date?: string;

  history_points?: number;

  return_1d?: number | null;
  return_1m?: number | null;
  return_3m?: number | null;
  return_6m?: number | null;
  return_1y?: number | null;
  return_3y?: number | null;
  return_5y?: number | null;

  volatility?: number | null;
  standard_deviation?: number | null;
  sharpe_ratio?: number | null;

  max_drawdown?: number | null;
  cagr?: number | null;

  performance_score?: number | null;

  calculated_at?: string;

  status?: string;
};


type FundHealthHistoryPoint = {
  id: number;
  product_id: number;
  snapshot_date: string;
  calculated_at: string;
  fund_health_score: number | null;
  fund_status: string;
  history_days: number;
  data_quality_score: number | null;
  long_term_score: number | null;
  consistency_score: number | null;
  risk_adjusted_score: number | null;
  downside_score: number | null;
  volatility_score: number | null;
  momentum_score: number | null;
  peer_percentile: number | null;
  quality_score: number | null;
  fundamental_score: number | null;
  news_score: number | null;
  fund_health_summary: string | null;
};


type PeerMetricComparison = {
  fund: number | null;
  peer_median: number | null;
  difference: number | null;
  comparison:
    | "BETTER"
    | "WORSE"
    | "IN_LINE"
    | "UNAVAILABLE"
    | string;
};

type FundPeerComparison = {
  product_id: number;
  peer_group: string;
  category_label: string;

  category_rank: number | null;
  category_size: number;

  fund_status: string;

  metrics: {
    return_1y: PeerMetricComparison;
    return_3y: PeerMetricComparison;
    return_5y: PeerMetricComparison;

    volatility: PeerMetricComparison;
    expense_ratio: PeerMetricComparison;
    sharpe_ratio: PeerMetricComparison;
  };
};


type Range =
  | "1M"
  | "3M"
  | "6M"
  | "1Y"
  | "3Y"
  | "5Y"
  | "ALL";


const ranges: Range[] = [
  "1M",
  "3M",
  "6M",
  "1Y",
  "3Y",
  "5Y",
  "ALL",
];


export default function FundDetailPage() {
  const router = useRouter();

  const params = useParams();

  const productId =
    Number(params.id);


  const [product, setProduct] =
    useState<InvestmentProduct | null>(
      null
    );

  const [analytics, setAnalytics] =
    useState<FundAnalytics | null>(
      null
    );

  const [history, setHistory] =
    useState<NAVPoint[]>([]);

  const [healthHistory, setHealthHistory] =
    useState<FundHealthHistoryPoint[]>([]);

  const [peerComparison, setPeerComparison] =
    useState<FundPeerComparison | null>(
      null
    );

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [selectedRange, setSelectedRange] =
    useState<Range>("1Y");

  const [isPremium, setIsPremium] =
    useState(false);

  useEffect(() => {
    const tier =
      localStorage.getItem(
        "subscription_tier"
      );

    setIsPremium(
      tier?.toUpperCase() ===
        "PREMIUM"
    );
  }, []);


  useEffect(() => {
    async function loadFund() {
      const token =
        localStorage.getItem(
          "access_token"
        );

      if (!token) {
        router.push("/login");
        return;
      }

      if (
        !productId ||
        Number.isNaN(productId)
      ) {
        setError(
          "Invalid investment product."
        );

        setLoading(false);

        return;
      }

      const headers = {
        Authorization:
          `Bearer ${token}`,
      };

      try {
        const [
          productResponse,
          analyticsResponse,
          historyResponse,
          healthHistoryResponse,
          peerComparisonResponse,
        ] = await Promise.all([
          fetch(
            `${API_BASE}/investments/products/${productId}`,
            {
              headers,
            }
          ),

          fetch(
            `${API_BASE}/investments/products/${productId}/analytics`,
            {
              headers,
            }
          ),

          fetch(
            `${API_BASE}/investments/products/${productId}/nav-history`,
            {
              headers,
            }
          ),

          fetch(
            `${API_BASE}/investments/products/${productId}/health-history`,
            {
              headers,
            }
          ),

          fetch(
            `${API_BASE}/investments/products/${productId}/peer-comparison`,
            {
              headers,
            }
          ),
        ]);


        if (!productResponse.ok) {
          const data =
            await productResponse.json();

          setError(
            data.detail ||
              "Investment product not found."
          );

          return;
        }


        const productData =
          await productResponse.json();

        setProduct(productData);

        if (
          analyticsResponse.ok
        ) {
          setAnalytics(
            await analyticsResponse.json()
          );
        }


        if (
          historyResponse.ok
        ) {
          setHistory(
            await historyResponse.json()
          );
        }

        if (
          healthHistoryResponse.ok
        ) {
          setHealthHistory(
            await healthHistoryResponse.json()
          );
        }

        if (
          peerComparisonResponse.ok
        ) {
          setPeerComparison(
            await peerComparisonResponse.json()
          );
        }

      } catch {
        setError(
          "Could not connect to InvestiGenie backend."
        );
      } finally {
        setLoading(false);
      }
    }

    loadFund();
  }, [
    productId,
    router,
  ]);


  const filteredHistory =
    useMemo(() => {
      if (
        selectedRange === "ALL"
      ) {
        return history;
      }

      const rangeDays: Record<
        Exclude<Range, "ALL">,
        number
      > = {
        "1M": 30,
        "3M": 90,
        "6M": 180,
        "1Y": 365,
        "3Y": 1095,
        "5Y": 1825,
      };

      const days =
        rangeDays[selectedRange];

      if (
        history.length === 0
      ) {
        return [];
      }

      const latestDate =
        new Date(
          history[
            history.length - 1
          ].nav_date
        );

      const cutoff =
        new Date(latestDate);

      cutoff.setDate(
        cutoff.getDate() - days
      );

      return history.filter(
        (point) =>
          new Date(
            point.nav_date
          ) >= cutoff
      );
    }, [
      history,
      selectedRange,
    ]);

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#05070b] text-white">

        <div className="text-center">

          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-2 border-white/10 border-t-emerald-300" />

          <p className="mt-5 text-sm text-white/40">
            Analysing fund data...
          </p>

        </div>

      </main>
    );
  }


  if (
    error ||
    !product
  ) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#05070b] px-6 text-white">

        <div className="max-w-lg text-center">

          <p className="text-2xl font-medium">
            Fund unavailable
          </p>

          <p className="mt-3 text-sm text-white/40">
            {error ||
              "We could not load this investment."}
          </p>

          <button
            onClick={() =>
              router.push("/fund-radar")
            }
            className="mt-7 rounded-full bg-emerald-300 px-6 py-3 text-sm font-medium text-[#04100c]"
          >
            Back to Fund Radar
          </button>

        </div>

      </main>
    );
  }


  const positiveDaily =
    (
      product.daily_change_percentage ??
      analytics?.return_1d ??
      0
    ) >= 0;


  return (
    <main className="relative min-h-screen overflow-hidden bg-[#05070b] text-white">

      {/* Ambient background */}

      <div className="pointer-events-none fixed inset-0">

        <div className="absolute left-[15%] top-[-18rem] h-[34rem] w-[34rem] rounded-full bg-emerald-400/[0.055] blur-[130px]" />

        <div className="absolute right-[-12rem] top-[25rem] h-[30rem] w-[30rem] rounded-full bg-cyan-400/[0.035] blur-[130px]" />

      </div>

      <section className="relative z-10 mx-auto max-w-[1450px] px-4 pb-28 pt-5 sm:px-6 sm:py-8 md:pb-8 lg:px-10">

        {/* Breadcrumb */}

        <button
          onClick={() => router.push("/fund-radar")}
          className="inline-flex min-h-10 items-center gap-2 text-sm text-white/35 transition hover:text-white/70"
        >
          <ArrowLeft size={16} />
          Back to Fund Radar
        </button>


        {/* Fund Header */}

        <div className="mt-4 grid gap-4 sm:mt-7 sm:gap-6 xl:grid-cols-[1fr_390px]">

          <div className="rounded-[24px] border border-white/[0.08] bg-white/[0.025] p-5 sm:rounded-[30px] sm:p-9">

            <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">

              <div>

                <div className="flex flex-wrap gap-2">

                  <Badge>
                    {product.category ||
                      product.product_type}
                  </Badge>

                  {product.plan_type && (
                    <Badge>
                      {product.plan_type}
                    </Badge>
                  )}

                  {product.option_type && (
                    <Badge>
                      {product.option_type}
                    </Badge>
                  )}

                </div>


                <h1 className="mt-4 max-w-4xl text-2xl font-semibold leading-tight tracking-[-0.04em] sm:mt-5 sm:text-4xl lg:text-5xl">
                  {product.name}
                </h1>


                <p className="mt-4 text-sm text-white/38">
                  {product.provider ||
                    "Mutual Fund"}
                </p>


                <div className="mt-8">

                  <p className="text-[11px] uppercase tracking-[0.13em] text-white/25">
                    Latest NAV
                  </p>

                  <div className="mt-2 flex flex-wrap items-end gap-4">

                    <p className="text-4xl font-semibold tracking-[-0.05em] sm:text-5xl">
                      ₹
                      {formatMoney(
                        product.nav
                      )}
                    </p>


                    <div
                      className={`mb-1 rounded-full px-3 py-1.5 text-sm ${
                        positiveDaily
                          ? "bg-emerald-400/[0.08] text-emerald-300"
                          : "bg-red-400/[0.08] text-red-300"
                      }`}
                    >
                      {positiveDaily
                        ? "▲"
                        : "▼"}{" "}
                      {formatPercent(
                        product.daily_change_percentage ??
                          analytics?.return_1d
                      )}
                    </div>

                  </div>


                  <p className="mt-3 text-xs text-white/25">
                    NAV as of{" "}
                    {formatDate(
                      product.nav_date ||
                        analytics?.nav_date
                    )}
                  </p>

                </div>

              </div>


              <FundHealthSummary
                status={normalizeFundStatus(product.fund_status)}
                formScore={product.peer_percentile}
                isPremium={isPremium}
              />

              </div>

            </div>

        </div>


        {/* Fund Intelligence */}
        <FundIntelligenceStrip
          product={product}
          analytics={analytics}
          healthHistory={healthHistory}
          isPremium={isPremium}
        />


        <div className="mt-4 overflow-x-auto rounded-[18px] border border-white/[0.07] bg-white/[0.022] p-1 sm:mt-5">
          <div className="flex min-w-max items-center gap-1">
            {["Overview", "Performance", "Form Journey", "Peers", "Risk", "Portfolio", "About"].map((item, index) => (
              <button
                key={item}
                type="button"
                onClick={() => {
                  const targets = [
                    "fund-overview",
                    "fund-performance",
                    "fund-form-journey",
                    "fund-peers",
                    "fund-risk",
                    "fund-portfolio",
                    "fund-about",
                  ];
                  document.getElementById(targets[index])?.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                  });
                }}
                className={`rounded-xl px-4 py-2.5 text-xs font-medium transition ${
                  index === 0
                    ? "bg-emerald-300 text-[#04100c]"
                    : "text-white/35 hover:bg-white/[0.04] hover:text-white/70"
                }`}
              >
                {item}
              </button>
            ))}
          </div>
        </div>

        {/* NAV Chart */}

        <div id="fund-performance" className="mt-4 scroll-mt-24 rounded-[24px] border border-white/[0.08] bg-white/[0.025] p-4 sm:mt-6 sm:rounded-[30px] sm:p-8">

          <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">

            <div>

              <p className="text-[10px] uppercase tracking-[0.14em] text-white/25">
                NAV PERFORMANCE
              </p>

              <h2 className="mt-2 text-2xl font-medium">
                Historical NAV
              </h2>

              <p className="mt-2 text-xs text-white/30">
                {analytics?.history_points ??
                  history.length}{" "}
                NAV observations available
              </p>

            </div>


            <div className="flex flex-wrap gap-2">

              {ranges.map(
                (range) => (
                  <button
                    key={range}
                    onClick={() =>
                      setSelectedRange(
                        range
                      )
                    }
                    className={`rounded-full px-4 py-2 text-xs transition ${
                      selectedRange ===
                      range
                        ? "bg-emerald-300 text-[#04100c]"
                        : "border border-white/[0.07] bg-white/[0.025] text-white/40 hover:text-white"
                    }`}
                  >
                    {range}
                  </button>
                )
              )}

            </div>

          </div>


          <div className="mt-8">

            {filteredHistory.length >=
            2 ? (
              <NAVChart
                history={
                  filteredHistory
                }
              />
            ) : (
              <div className="flex h-72 items-center justify-center rounded-[20px] border border-dashed border-white/[0.08]">

                <div className="text-center">

                  <p className="text-sm text-white/40">
                    Not enough NAV history
                  </p>

                  <p className="mt-2 text-xs text-white/20">
                    Select a wider period.
                  </p>

                </div>

              </div>
            )}

          </div>

        </div>


        {/* Returns */}

        <section id="fund-overview" className="mt-6 scroll-mt-24">

          <SectionHeading
            eyebrow="PERFORMANCE"
            title="Fund returns"
            description="Returns calculated using historical NAV data."
          />

          <div className="mt-4 grid grid-cols-2 gap-2 sm:mt-5 sm:gap-3 lg:grid-cols-4 xl:grid-cols-7">

            <ReturnCard
              label="1 Day"
              value={
                analytics?.return_1d
              }
            />

            <ReturnCard
              label="1 Month"
              value={
                analytics?.return_1m
              }
            />

            <ReturnCard
              label="3 Months"
              value={
                analytics?.return_3m
              }
            />

            <ReturnCard
              label="6 Months"
              value={
                analytics?.return_6m
              }
            />

            <ReturnCard
              label="1 Year"
              value={
                analytics?.return_1y
              }
            />

            <ReturnCard
              label="3 Years"
              value={
                analytics?.return_3y
              }
            />

            <ReturnCard
              label="5 Years"
              value={
                analytics?.return_5y
              }
            />

          </div>

        </section>


        {/* Category Peer Comparison */}

        <section
          id="fund-peers"
          className="mt-6 scroll-mt-24"
        >
          <SectionHeading
            eyebrow="CATEGORY COMPARISON"
            title="How this fund stacks up"
            description="Compared only with rated underlying schemes in the same mutual-fund peer category."
          />

          {peerComparison ? (
            <div className="mt-4 overflow-hidden rounded-[26px] border border-white/[0.08] bg-white/[0.025] sm:mt-5 sm:rounded-[30px]">
              <div className="grid xl:grid-cols-[310px_1fr]">
                <div className="border-b border-white/[0.06] bg-gradient-to-br from-emerald-400/[0.07] to-transparent p-5 sm:p-7 xl:border-b-0 xl:border-r">
                  <div className="flex items-center gap-2 text-[10px] font-medium uppercase tracking-[0.14em] text-emerald-200/60">
                    <Trophy size={14} />
                    CATEGORY POSITION
                  </div>

                  <div className="mt-5 flex items-end gap-3">
                    <p className="text-5xl font-semibold tracking-[-0.055em] text-emerald-200">
                      {peerComparison.category_rank != null
                        ? `#${peerComparison.category_rank}`
                        : "—"}
                    </p>

                    <div className="pb-1">
                      <p className="text-xs text-white/28">
                        of {peerComparison.category_size}
                      </p>

                      <p className="mt-1 text-sm font-medium text-white/70">
                        {peerComparison.category_label} funds
                      </p>
                    </div>
                  </div>

                  <div className="mt-5 rounded-2xl border border-white/[0.06] bg-black/10 p-4">
                    <div className="flex items-center gap-2">
                      <UsersRound
                        size={15}
                        className="text-white/35"
                      />

                      <p className="text-xs text-white/38">
                        Peer universe
                      </p>
                    </div>

                    <p className="mt-2 text-sm leading-6 text-white/58">
                      Rank is calculated after collapsing Direct,
                      Regular, Growth and IDCW variants into one
                      underlying scheme.
                    </p>
                  </div>
                </div>

                <div className="p-4 sm:p-6 lg:p-7">
                  <div className="hidden grid-cols-[1.1fr_.8fr_.8fr_.7fr] gap-3 border-b border-white/[0.055] px-2 pb-3 text-[9px] font-medium uppercase tracking-[0.12em] text-white/22 md:grid">
                    <span>Metric</span>
                    <span>This fund</span>
                    <span>Peer median</span>
                    <span>Reading</span>
                  </div>

                  <div className="mt-1 space-y-2 md:mt-2">
                    <PeerComparisonRow
                      label="1Y Return"
                      metric={peerComparison.metrics.return_1y}
                      format="percent"
                    />

                    <PeerComparisonRow
                      label="3Y Return"
                      metric={peerComparison.metrics.return_3y}
                      format="percent"
                    />

                    <PeerComparisonRow
                      label="5Y Return"
                      metric={peerComparison.metrics.return_5y}
                      format="percent"
                    />

                    <PeerComparisonRow
                      label="Volatility"
                      metric={peerComparison.metrics.volatility}
                      format="percent"
                      lowerIsBetter
                    />

                    <PeerComparisonRow
                      label="Expense Ratio"
                      metric={peerComparison.metrics.expense_ratio}
                      format="percent"
                      lowerIsBetter
                    />

                    <PeerComparisonRow
                      label="Sharpe Ratio"
                      metric={peerComparison.metrics.sharpe_ratio}
                      format="number"
                    />
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="mt-5 rounded-[24px] border border-dashed border-white/[0.08] bg-white/[0.018] p-6 text-center">
              <p className="text-sm font-medium text-white/45">
                Peer comparison is not available for this fund yet.
              </p>

              <p className="mt-2 text-xs leading-5 text-white/22">
                The fund may be unrated or may not yet have enough comparable peer data.
              </p>
            </div>
          )}
        </section>


        {/* Risk Analytics */}

        <div id="fund-risk" className="mt-6 scroll-mt-24 grid gap-5 xl:grid-cols-[1.25fr_.75fr]">

          <div className="rounded-[30px] border border-white/[0.08] bg-white/[0.025] p-7">

            <SectionHeading
              eyebrow="RISK ANALYTICS"
              title="Understand the risk"
              description="Statistical measures derived from the fund's NAV history."
            />

            <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">

              <AnalyticsCard
                label="Volatility"
                value={formatPercent(
                  analytics?.volatility
                )}
                description="Annualised NAV variability"
              />

              <AnalyticsCard
                label="Sharpe Ratio"
                value={formatNumber(
                  analytics?.sharpe_ratio
                )}
                description="Risk-adjusted performance"
              />

              <AnalyticsCard
                label="Max Drawdown"
                value={formatPercent(
                  analytics?.max_drawdown
                )}
                description="Largest historical decline"
              />

              <AnalyticsCard
                label="CAGR"
                value={formatPercent(
                  analytics?.cagr
                )}
                description="Annualised historical growth"
              />

              <AnalyticsCard
                label="Std. Deviation"
                value={formatPercent(
                  analytics?.standard_deviation
                )}
                description="Dispersion of daily returns"
              />

              <AnalyticsCard
                label="Risk Level"
                value={
                  product.risk_level ||
                  product.riskometer ||
                  "Not available"
                }
                description="Fund risk classification"
              />

            </div>

          </div>


          {/* InvestiGenie AI placeholder */}

          <div className="relative overflow-hidden rounded-[30px] border border-emerald-400/15 bg-gradient-to-b from-emerald-400/[0.07] to-emerald-400/[0.025] p-7">

            <div className="absolute right-[-3rem] top-[-3rem] h-36 w-36 rounded-full bg-emerald-300/[0.09] blur-3xl" />


            <div className="relative">

              <div className="flex items-center gap-2">
                <LockKeyhole size={14} className="text-emerald-200/80" />
                <p className="text-[10px] uppercase tracking-[0.14em] text-emerald-200/65">
                  FOR YOU · GENIE PREMIUM
                </p>
              </div>

              <h3 className="mt-4 text-2xl font-medium leading-snug">
                Performance is not the same as suitability.
              </h3>

              <p className="mt-4 text-sm leading-6 text-white/40">
                Genie Premium will combine this fund&apos;s quality and risk
                signals with your financial profile, goals, portfolio,
                Wealth DNA and ML outlook before recommending it to you.
              </p>

              <div className="mt-7 space-y-3">
                <AIStatusRow label="Fund analytics" value="Available" />
                <AIStatusRow label="Exact Form Score" value={isPremium ? "Available" : "Premium"} />
                <AIStatusRow label="Risk compatibility" value="Premium" />
                <AIStatusRow label="Goal compatibility" value="Premium" />
                <AIStatusRow label="Portfolio overlap" value="Premium" />
                <AIStatusRow label="Genie Match" value="Premium" />
              </div>

              <button
                type="button"
                onClick={() => router.push("/invest")}
                className="mt-6 inline-flex min-h-11 items-center gap-2 rounded-xl bg-emerald-300 px-4 text-sm font-semibold text-[#04100c] transition hover:bg-emerald-200"
              >
                Analyse this fund for me
                <ArrowRight size={15} />
              </button>

            </div>

          </div>

        </div>


        {/* Fund Details */}

        <div id="fund-about" className="mt-6 scroll-mt-24 rounded-[30px] border border-white/[0.08] bg-white/[0.025] p-7">

          <SectionHeading
            eyebrow="FUND DETAILS"
            title="About this investment"
            description="Scheme information currently available in InvestiGenie."
          />


          <div className="mt-7 grid gap-x-10 gap-y-7 sm:grid-cols-2 lg:grid-cols-3">

            <DetailItem
              label="AMC / Provider"
              value={
                product.provider ||
                "—"
              }
            />

            <DetailItem
              label="Scheme Code"
              value={
                product.scheme_code ||
                "—"
              }
            />

            <DetailItem
              label="ISIN"
              value={
                product.isin ||
                "—"
              }
            />

            <DetailItem
              label="Category"
              value={
                product.category ||
                "—"
              }
            />

            <DetailItem
              label="Sub-category"
              value={
                product.sub_category ||
                "—"
              }
            />

            <DetailItem
              label="Benchmark"
              value={
                product.benchmark ||
                "Data pipeline pending"
              }
            />

            <DetailItem
              label="Expense Ratio"
              value={
                product.expense_ratio
                  ? `${product.expense_ratio.toFixed(
                      2
                    )}%`
                  : "Data pipeline pending"
              }
            />

            <DetailItem
              label="AUM"
              value={
                product.aum
                  ? `₹${formatMoney(
                      product.aum
                    )}`
                  : "Data pipeline pending"
              }
            />

            <DetailItem
              label="Fund Manager"
              value={
                product.fund_manager ||
                "Data pipeline pending"
              }
            />

            <DetailItem
              label="Launch Date"
              value={
                product.launch_date
                  ? formatDate(
                      product.launch_date
                    )
                  : "Data pipeline pending"
              }
            />

            <DetailItem
              label="Exit Load"
              value={
                product.exit_load ||
                "Data pipeline pending"
              }
            />

            <DetailItem
              label="Data Source"
              value={
                product.source
              }
            />

          </div>


          {product.investment_objective && (

            <div className="mt-8 border-t border-white/[0.06] pt-7">

              <p className="text-[10px] uppercase tracking-[0.13em] text-white/25">
                Investment Objective
              </p>

              <p className="mt-3 max-w-4xl text-sm leading-7 text-white/45">
                {
                  product.investment_objective
                }
              </p>

            </div>

          )}

        </div>


        {/* Allocation */}

        <div id="fund-portfolio" className="mt-6 scroll-mt-24 grid gap-5 lg:grid-cols-2">

          <AllocationPanel
            title="Asset Allocation"
            rows={[
              {
                name: "Equity",
                value:
                  product.equity_percentage,
              },
              {
                name: "Debt",
                value:
                  product.debt_percentage,
              },
              {
                name: "Cash",
                value:
                  product.cash_percentage,
              },
            ]}
          />

          <AllocationPanel
            title="Market Cap Allocation"
            rows={[
              {
                name: "Large Cap",
                value:
                  product.large_cap_percentage,
              },
              {
                name: "Mid Cap",
                value:
                  product.mid_cap_percentage,
              },
              {
                name: "Small Cap",
                value:
                  product.small_cap_percentage,
              },
            ]}
          />

        </div>


        <div className="mt-8 pb-8 text-center">

          <p className="text-[10px] leading-5 text-white/18">
            Mutual fund investments are subject to
            market risks. Historical returns do not
            guarantee future performance.
          </p>

        </div>

      </section>

    </main>
  );
}



type FundStatus =
  | "IN_FORM"
  | "ON_TRACK"
  | "OFF_TRACK"
  | "NOT_IN_FORM"
  | "UNRATED";

function normalizeFundStatus(value?: string | null): FundStatus {
  const raw = String(value || "")
    .trim()
    .toUpperCase()
    .replaceAll("-", "_")
    .replaceAll(" ", "_");

  if (raw === "IN_FORM") return "IN_FORM";
  if (raw === "ON_TRACK") return "ON_TRACK";
  if (raw === "OFF_TRACK") return "OFF_TRACK";
  if (raw === "NOT_IN_FORM" || raw === "OUT_OF_FORM") return "NOT_IN_FORM";
  return "UNRATED";
}

function getFundStatusMeta(status: FundStatus) {
  if (status === "IN_FORM") {
    return {
      label: "In Form",
      icon: <TrendingUp size={16} />,
      className:
        "border-emerald-400/18 bg-emerald-400/[0.07] text-emerald-100",
      description: "Strong current fund-performance signal.",
    };
  }

  if (status === "ON_TRACK") {
    return {
      label: "On Track",
      icon: <Gauge size={16} />,
      className:
        "border-teal-400/18 bg-teal-400/[0.06] text-teal-100",
      description: "Healthy and broadly stable performance signal.",
    };
  }

  if (status === "OFF_TRACK") {
    return {
      label: "Off Track",
      icon: <TrendingDown size={16} />,
      className:
        "border-amber-400/18 bg-amber-400/[0.06] text-amber-100",
      description: "Performance needs closer attention.",
    };
  }

  if (status === "NOT_IN_FORM") {
    return {
      label: "Not In Form",
      icon: <TrendingDown size={16} />,
      className:
        "border-red-400/18 bg-red-400/[0.055] text-red-100",
      description: "Weak current fund-performance signal.",
    };
  }

  return {
    label: "Unrated",
    icon: <CircleHelp size={16} />,
    className:
      "border-white/[0.08] bg-white/[0.025] text-white/55",
    description: "Not enough reliable data to classify this fund.",
  };
}

function FundHealthSummary({
  status,
  formScore,
  isPremium,
}: {
  status: FundStatus;
  formScore?: number | null;
  isPremium: boolean;
}) {
  const meta =
    getFundStatusMeta(status);

  return (
    <div
      className={`rounded-[22px] border p-5 lg:min-w-[230px] ${meta.className}`}
    >
      <p className="text-[10px] uppercase tracking-[0.13em] opacity-60">
        Current Form
      </p>

      <div className="mt-3 flex items-center gap-2">
        {meta.icon}
        <p className="text-lg font-semibold">
          {meta.label}
        </p>
      </div>

      <p className="mt-3 text-xs leading-5 opacity-55">
        {meta.description}
      </p>

      <div className="mt-4 border-t border-current/10 pt-4">
        <p className="text-[9px] uppercase tracking-[0.11em] opacity-45">
          Form Score
        </p>

        {isPremium ? (
          <p className="mt-2 text-2xl font-semibold tracking-[-0.03em]">
            {formScore != null
              ? formScore.toFixed(2)
              : "—"}
            {formScore != null && (
              <span className="ml-1 text-xs opacity-45">
                /100
              </span>
            )}
          </p>
        ) : (
          <div className="mt-2 inline-flex items-center gap-2 rounded-xl border border-current/10 bg-black/10 px-3 py-2 text-xs">
            <LockKeyhole size={13} />
            Premium
          </div>
        )}
      </div>
    </div>
  );
}


function FundIntelligenceStrip({
  product,
  analytics,
  healthHistory,
  isPremium,
}: {
  product: InvestmentProduct;
  analytics: FundAnalytics | null;
  healthHistory: FundHealthHistoryPoint[];
  isPremium: boolean;
}) {
  const status =
    normalizeFundStatus(
      product.fund_status
    );

  const meta =
    getFundStatusMeta(status);

  const windows = [
    ["1M", analytics?.return_1m],
    ["3M", analytics?.return_3m],
    ["6M", analytics?.return_6m],
    ["1Y", analytics?.return_1y],
    ["3Y", analytics?.return_3y],
    ["5Y", analytics?.return_5y],
  ] as const;

  const latestSnapshots =
    healthHistory.slice(-8);

  return (
    <section
      id="fund-form-journey"
      className="mt-4 scroll-mt-24 overflow-hidden rounded-[28px] border border-white/[0.08] bg-white/[0.025] sm:mt-6 sm:rounded-[32px]"
    >
      <div className="grid lg:grid-cols-[1.08fr_.92fr]">
        <div className="p-5 sm:p-7 lg:p-8">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-[10px] font-medium uppercase tracking-[0.16em] text-emerald-200/60">
              FUND FORM
            </p>

            <span className="rounded-full border border-white/[0.07] bg-white/[0.025] px-2.5 py-1 text-[9px] uppercase tracking-[0.11em] text-white/28">
              Category-relative signal
            </span>
          </div>

          <div className="mt-5 flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <div
                className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold ${meta.className}`}
              >
                {meta.icon}
                {meta.label}
              </div>

              <h2 className="mt-4 text-2xl font-semibold tracking-[-0.035em] sm:text-3xl">
                How this fund is performing now
              </h2>

              <p className="mt-2 max-w-xl text-sm leading-6 text-white/35">
                {meta.description} The state is based on
                category-relative performance, consistency,
                risk-adjusted results, momentum, downside
                protection, volatility and fund quality.
              </p>
            </div>

            <div className="sm:min-w-[220px]">
              <div className="rounded-2xl border border-white/[0.06] bg-black/10 p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-[9px] uppercase tracking-[0.11em] text-white/22">
                    Form Score
                  </p>

                  {!isPremium && (
                    <LockKeyhole
                      size={13}
                      className="text-amber-200/65"
                    />
                  )}
                </div>

                {isPremium ? (
                  <p className="mt-2 text-2xl font-semibold text-emerald-200">
                    {product.peer_percentile != null
                      ? product.peer_percentile.toFixed(2)
                      : "—"}
                  </p>
                ) : (
                  <>
                    <p className="mt-2 text-sm font-semibold text-amber-100/70">
                      Premium
                    </p>

                    <p className="mt-1 text-[10px] leading-4 text-white/22">
                      Exact category-relative score is hidden
                      on the Basic plan.
                    </p>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-3 gap-2 sm:grid-cols-6">
            {windows.map(
              ([label, value]) => (
                <div
                  key={label}
                  className="rounded-[17px] border border-white/[0.055] bg-black/10 p-3"
                >
                  <p className="text-[9px] uppercase tracking-[0.11em] text-white/22">
                    {label}
                  </p>

                  <p
                    className={`mt-2 text-sm font-semibold ${
                      value == null
                        ? "text-white/30"
                        : value >= 0
                          ? "text-emerald-300"
                          : "text-red-300"
                    }`}
                  >
                    {value == null
                      ? "—"
                      : `${value > 0 ? "+" : ""}${value.toFixed(2)}%`}
                  </p>
                </div>
              )
            )}
          </div>
        </div>

        <div className="border-t border-white/[0.06] bg-black/10 p-5 sm:p-7 lg:border-l lg:border-t-0">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-[10px] font-medium uppercase tracking-[0.15em] text-white/25">
                FORM JOURNEY
              </p>

              <h3 className="mt-2 text-xl font-semibold tracking-[-0.025em]">
                Status over time
              </h3>
            </div>

            <Gauge
              size={20}
              className="text-emerald-200/60"
            />
          </div>

          {latestSnapshots.length > 0 ? (
            <div className="mt-6">
              <div className="overflow-x-auto pb-1">
                <div className="relative min-w-[430px]">
                  <div className="absolute left-4 right-4 top-4 h-px bg-white/[0.08]" />

                  <div className="relative grid grid-cols-8 gap-2">
                    {latestSnapshots.map(
                      (point) => {
                        const pointStatus =
                          normalizeFundStatus(
                            point.fund_status
                          );

                        const pointMeta =
                          getFundStatusMeta(
                            pointStatus
                          );

                        return (
                          <div
                            key={point.id}
                            className="min-w-0 text-center"
                          >
                            <div
                              className={`mx-auto flex h-8 w-8 items-center justify-center rounded-full border ${pointMeta.className}`}
                            >
                              <span className="h-2 w-2 rounded-full bg-current" />
                            </div>

                            <p className="mt-2 truncate text-[9px] font-medium text-white/45">
                              {pointMeta.label}
                            </p>

                            <p className="mt-1 text-[8px] text-white/20">
                              {formatShortDate(
                                point.snapshot_date
                              )}
                            </p>
                          </div>
                        );
                      }
                    )}
                  </div>
                </div>
              </div>

              <div className="mt-5 rounded-2xl border border-white/[0.06] bg-white/[0.02] p-4">
                <p className="text-[10px] uppercase tracking-[0.12em] text-white/22">
                  Latest reading
                </p>

                <p className="mt-2 text-sm leading-6 text-white/42">
                  {latestSnapshots[
                    latestSnapshots.length - 1
                  ]?.fund_health_summary ||
                    "Historical Fund Form snapshots are now being collected."}
                </p>
              </div>
            </div>
          ) : (
            <div className="mt-6 rounded-2xl border border-dashed border-white/[0.08] p-5">
              <p className="text-sm font-medium text-white/50">
                Form history starts from the first stored snapshot.
              </p>

              <p className="mt-2 text-xs leading-5 text-white/25">
                InvestiGenie will build this journey automatically
                as the Fund Form engine is recalculated over time.
              </p>
            </div>
          )}

          <p className="mt-5 text-[10px] leading-5 text-white/20">
            Fund Form describes category-relative fund performance.
            It is not a personalized recommendation to buy, sell
            or hold.
          </p>
        </div>
      </div>
    </section>
  );
}


function NAVChart({
  history,
}: {
  history: NAVPoint[];
}) {
  const width = 1000;
  const height = 300;
  const padding = 22;

  const navValues =
    history.map(
      (point) => point.nav
    );

  const min =
    Math.min(...navValues);

  const max =
    Math.max(...navValues);

  const range =
    Math.max(
      max - min,
      0.0001
    );

  const points =
    history.map(
      (point, index) => {
        const x =
          padding +
          (
            index /
            Math.max(
              history.length - 1,
              1
            )
          ) *
            (
              width -
              padding * 2
            );

        const normalized =
          (
            point.nav -
            min
          ) / range;

        const y =
          height -
          padding -
          normalized *
            (
              height -
              padding * 2
            );

        return {
          x,
          y,
          point,
        };
      }
    );


  const polyline =
    points
      .map(
        ({ x, y }) =>
          `${x},${y}`
      )
      .join(" ");


  const start =
    history[0];

  const end =
    history[
      history.length - 1
    ];


  const periodReturn =
    start.nav > 0
      ? (
          (
            end.nav -
            start.nav
          ) /
          start.nav
        ) * 100
      : 0;


  return (
    <div>

      <div className="mb-5 flex flex-wrap items-end justify-between gap-4">

        <div>

          <p className="text-xs text-white/25">
            Period return
          </p>

          <p
            className={`mt-1 text-xl font-medium ${
              periodReturn >= 0
                ? "text-emerald-300"
                : "text-red-300"
            }`}
          >
            {periodReturn >= 0
              ? "+"
              : ""}
            {periodReturn.toFixed(
              2
            )}
            %
          </p>

        </div>


        <div className="text-right">

          <p className="text-xs text-white/25">
            ₹{formatMoney(min)} – ₹
            {formatMoney(max)}
          </p>

          <p className="mt-1 text-[10px] text-white/18">
            {formatDate(
              start.nav_date
            )}{" "}
            →{" "}
            {formatDate(
              end.nav_date
            )}
          </p>

        </div>

      </div>


      <div className="overflow-hidden rounded-[20px] border border-white/[0.06] bg-black/10 p-3">

        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="h-[210px] w-full sm:h-[280px]"
          preserveAspectRatio="none"
        >

          <defs>

            <linearGradient
              id="navArea"
              x1="0"
              x2="0"
              y1="0"
              y2="1"
            >

              <stop
                offset="0%"
                stopColor="rgb(110 231 183)"
                stopOpacity="0.18"
              />

              <stop
                offset="100%"
                stopColor="rgb(110 231 183)"
                stopOpacity="0"
              />

            </linearGradient>

          </defs>


          <line
            x1={padding}
            x2={
              width - padding
            }
            y1={
              height / 2
            }
            y2={
              height / 2
            }
            stroke="rgba(255,255,255,.05)"
          />


          <polygon
            points={`${padding},${height - padding} ${polyline} ${width - padding},${height - padding}`}
            fill="url(#navArea)"
          />


          <polyline
            points={polyline}
            fill="none"
            stroke="rgb(110 231 183)"
            strokeWidth="3"
            vectorEffect="non-scaling-stroke"
          />

        </svg>

      </div>

    </div>
  );
}


function PeerComparisonRow({
  label,
  metric,
  format,
  lowerIsBetter = false,
}: {
  label: string;
  metric: PeerMetricComparison;
  format: "percent" | "number";
  lowerIsBetter?: boolean;
}) {
  const reading =
    getPeerReading(
      metric.comparison
    );

  const differenceLabel =
    formatPeerDifference(
      metric.difference,
      format
    );

  return (
    <div className="rounded-[18px] border border-white/[0.055] bg-black/10 p-4 md:grid md:grid-cols-[1.1fr_.8fr_.8fr_.7fr] md:items-center md:gap-3 md:rounded-none md:border-x-0 md:border-t-0 md:bg-transparent md:px-2 md:py-4">
      <div>
        <p className="text-xs font-medium text-white/70">
          {label}
        </p>

        <p className="mt-1 text-[9px] text-white/20 md:hidden">
          {lowerIsBetter
            ? "Lower is generally better"
            : "Higher is generally better"}
        </p>
      </div>

      <div className="mt-3 flex items-end justify-between gap-3 md:mt-0 md:block">
        <p className="text-[9px] uppercase tracking-[0.1em] text-white/20 md:hidden">
          This fund
        </p>

        <p className="text-sm font-semibold text-white/78">
          {formatPeerValue(
            metric.fund,
            format
          )}
        </p>
      </div>

      <div className="mt-2 flex items-end justify-between gap-3 md:mt-0 md:block">
        <p className="text-[9px] uppercase tracking-[0.1em] text-white/20 md:hidden">
          Peer median
        </p>

        <p className="text-sm text-white/45">
          {formatPeerValue(
            metric.peer_median,
            format
          )}
        </p>
      </div>

      <div className="mt-3 flex items-center justify-between gap-3 border-t border-white/[0.05] pt-3 md:mt-0 md:border-0 md:pt-0">
        <span
          className={`inline-flex rounded-full border px-2.5 py-1 text-[9px] font-semibold uppercase tracking-[0.05em] ${reading.className}`}
        >
          {reading.label}
        </span>

        {differenceLabel && (
          <span className="text-[10px] text-white/28">
            {differenceLabel}
          </span>
        )}
      </div>
    </div>
  );
}


function getPeerReading(
  comparison: string
) {
  if (
    comparison === "BETTER"
  ) {
    return {
      label: "Better",
      className:
        "border-emerald-400/15 bg-emerald-400/[0.07] text-emerald-200",
    };
  }

  if (
    comparison === "WORSE"
  ) {
    return {
      label: "Behind",
      className:
        "border-amber-400/15 bg-amber-400/[0.06] text-amber-200",
    };
  }

  if (
    comparison === "IN_LINE"
  ) {
    return {
      label: "In line",
      className:
        "border-blue-400/15 bg-blue-400/[0.06] text-blue-200",
    };
  }

  return {
    label: "Unavailable",
    className:
      "border-white/[0.07] bg-white/[0.025] text-white/35",
  };
}


function formatPeerValue(
  value: number | null,
  format: "percent" | "number"
) {
  if (
    value == null ||
    Number.isNaN(value)
  ) {
    return "—";
  }

  if (
    format === "percent"
  ) {
    const sign =
      value > 0 ? "+" : "";

    return `${sign}${value.toFixed(2)}%`;
  }

  return value.toFixed(2);
}


function formatPeerDifference(
  value: number | null,
  format: "percent" | "number"
) {
  if (
    value == null ||
    Number.isNaN(value)
  ) {
    return null;
  }

  const sign =
    value > 0 ? "+" : "";

  if (
    format === "percent"
  ) {
    return `${sign}${value.toFixed(2)} pts`;
  }

  return `${sign}${value.toFixed(2)}`;
}


function SectionHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description?: string;
}) {
  return (
    <div>

      <p className="text-[10px] uppercase tracking-[0.14em] text-white/25">
        {eyebrow}
      </p>

      <h2 className="mt-2 text-2xl font-medium tracking-[-0.02em]">
        {title}
      </h2>

      {description && (
        <p className="mt-2 text-sm text-white/32">
          {description}
        </p>
      )}

    </div>
  );
}


function ReturnCard({
  label,
  value,
}: {
  label: string;
  value?: number | null;
}) {
  const positive =
    (value ?? 0) >= 0;

  return (
    <div className="rounded-[18px] border border-white/[0.07] bg-white/[0.025] p-4 sm:rounded-[20px] sm:p-5">

      <p className="text-[10px] uppercase tracking-[0.11em] text-white/23">
        {label}
      </p>

      <p
        className={`mt-3 text-xl font-medium ${
          value == null
            ? "text-white/35"
            : positive
            ? "text-emerald-300"
            : "text-red-300"
        }`}
      >
        {value == null
          ? "—"
          : `${
              positive ? "+" : ""
            }${value.toFixed(
              2
            )}%`}
      </p>

    </div>
  );
}


function AnalyticsCard({
  label,
  value,
  description,
}: {
  label: string;
  value: string;
  description: string;
}) {
  return (
    <div className="rounded-[20px] border border-white/[0.07] bg-black/10 p-5">

      <p className="text-[10px] uppercase tracking-[0.11em] text-white/23">
        {label}
      </p>

      <p className="mt-3 text-xl font-medium">
        {value}
      </p>

      <p className="mt-2 text-xs leading-5 text-white/28">
        {description}
      </p>

    </div>
  );
}


function DetailItem({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div>

      <p className="text-[10px] uppercase tracking-[0.12em] text-white/23">
        {label}
      </p>

      <p className="mt-2 text-sm leading-6 text-white/70">
        {value}
      </p>

    </div>
  );
}


function AIStatusRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between rounded-[16px] border border-white/[0.06] bg-black/10 px-4 py-3">

      <p className="text-xs text-white/35">
        {label}
      </p>

      <p className="text-xs font-medium text-emerald-200">
        {value}
      </p>

    </div>
  );
}


function AllocationPanel({
  title,
  rows,
}: {
  title: string;

  rows: {
    name: string;
    value?: number | null;
  }[];
}) {
  const available =
    rows.filter(
      (row) =>
        row.value != null
    );

  return (
    <div className="rounded-[30px] border border-white/[0.08] bg-white/[0.025] p-7">

      <p className="text-[10px] uppercase tracking-[0.14em] text-white/25">
        PORTFOLIO
      </p>

      <h3 className="mt-2 text-xl font-medium">
        {title}
      </h3>


      {available.length === 0 ? (

        <div className="mt-6 rounded-[18px] border border-dashed border-white/[0.07] p-7 text-center">

          <p className="text-sm text-white/30">
            Allocation data pipeline pending
          </p>

        </div>

      ) : (

        <div className="mt-6 space-y-5">

          {available.map(
            (row) => (
              <div
                key={
                  row.name
                }
              >

                <div className="flex justify-between text-sm">

                  <span className="text-white/45">
                    {row.name}
                  </span>

                  <span>
                    {row.value?.toFixed(
                      1
                    )}
                    %
                  </span>

                </div>


                <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/[0.06]">

                  <div
                    className="h-full rounded-full bg-emerald-300"
                    style={{
                      width:
                        `${Math.min(
                          row.value || 0,
                          100
                        )}%`,
                    }}
                  />

                </div>

              </div>
            )
          )}

        </div>

      )}

    </div>
  );
}


function Badge({
  children,
}: {
  children:
    React.ReactNode;
}) {
  return (
    <span className="rounded-full border border-white/[0.07] bg-white/[0.03] px-3 py-1.5 text-[10px] uppercase tracking-[0.1em] text-white/35">
      {children}
    </span>
  );
}


function formatMoney(
  value?: number | null
) {
  if (
    value == null ||
    Number.isNaN(value)
  ) {
    return "—";
  }

  return new Intl.NumberFormat(
    "en-IN",
    {
      maximumFractionDigits: 2,
    }
  ).format(value);
}


function formatPercent(
  value?: number | null
) {
  if (
    value == null ||
    Number.isNaN(value)
  ) {
    return "—";
  }

  const sign =
    value > 0
      ? "+"
      : "";

  return `${sign}${value.toFixed(
    2
  )}%`;
}


function formatNumber(
  value?: number | null
) {
  if (
    value == null ||
    Number.isNaN(value)
  ) {
    return "—";
  }

  return value.toFixed(2);
}


function formatShortDate(value?: string | null) {
  if (!value) {
    return "—";
  }

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
  }).format(parsed);
}


function formatDate(
  value?: string | null
) {
  if (!value) {
    return "Not available";
  }

  const parsed =
    new Date(value);

  if (
    Number.isNaN(
      parsed.getTime()
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "en-IN",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }
  ).format(parsed);
}