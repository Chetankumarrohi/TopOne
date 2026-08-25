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


type Range =
  | "1M"
  | "3M"
  | "6M"
  | "1Y"
  | "ALL";


const ranges: Range[] = [
  "1M",
  "3M",
  "6M",
  "1Y",
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

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [selectedRange, setSelectedRange] =
    useState<Range>("1Y");

  const [investmentMode, setInvestmentMode] =
    useState<"SIP" | "LUMPSUM">("SIP");

  const [amount, setAmount] =
    useState("");

  const [placingOrder, setPlacingOrder] =
    useState(false);

  const [orderMessage, setOrderMessage] =
    useState("");


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
          productData.sip_allowed
        ) {
          setInvestmentMode("SIP");

          setAmount(
            String(
              productData.minimum_sip ||
                500
            )
          );
        } else {
          setInvestmentMode(
            "LUMPSUM"
          );

          setAmount(
            String(
              productData.minimum_lumpsum ||
                1000
            )
          );
        }


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


  async function placeOrder() {
    if (!product) {
      return;
    }

    const token =
      localStorage.getItem(
        "access_token"
      );

    if (!token) {
      router.push("/login");
      return;
    }

    setPlacingOrder(true);
    setOrderMessage("");

    try {
      const response =
        await fetch(
          `${API_BASE}/investments/orders`,
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",

              Authorization:
                `Bearer ${token}`,
            },

            body: JSON.stringify({
              product_id:
                product.id,

              investment_mode:
                investmentMode,

              amount:
                Number(amount),
            }),
          }
        );

      const data =
        await response.json();

      if (!response.ok) {
        setOrderMessage(
          data.detail ||
            "Could not create investment order."
        );

        return;
      }

      setOrderMessage(
        `Order #${data.id} created successfully. Current status: ${data.status}`
      );

    } catch {
      setOrderMessage(
        "Could not connect to backend."
      );
    } finally {
      setPlacingOrder(false);
    }
  }


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
              router.push("/invest")
            }
            className="mt-7 rounded-full bg-emerald-300 px-6 py-3 text-sm font-medium text-[#04100c]"
          >
            Back to Investments
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


      {/* Navigation */}

      <nav className="relative z-20 hidden border-b border-white/[0.06] bg-[#05070b]/75 backdrop-blur-2xl md:block">

        <div className="mx-auto flex max-w-[1450px] items-center justify-between px-6 py-5 lg:px-10">

          <button
            onClick={() =>
              router.push(
                "/dashboard"
              )
            }
            className="flex items-center gap-3"
          >

            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-emerald-400/20 bg-emerald-400/[0.07]">

              <div className="h-3 w-3 rounded-full bg-emerald-300 shadow-[0_0_16px_rgba(110,231,183,.75)]" />

            </div>

            <span className="text-xl font-semibold tracking-[-0.03em]">
              Investi
              <span className="text-emerald-300">
                Genie
              </span>
            </span>

          </button>


          <div className="flex items-center gap-2">

            <button
              onClick={() =>
                router.push(
                  "/invest"
                )
              }
              className="rounded-full border border-white/[0.08] bg-white/[0.03] px-5 py-2.5 text-sm text-white/55 transition hover:bg-white/[0.06] hover:text-white"
            >
              Investments
            </button>

            <button
              onClick={() =>
                router.push(
                  "/portfolio"
                )
              }
              className="hidden rounded-full border border-white/[0.08] bg-white/[0.03] px-5 py-2.5 text-sm text-white/55 transition hover:bg-white/[0.06] hover:text-white sm:block"
            >
              Portfolio
            </button>

          </div>

        </div>

      </nav>


      <section className="relative z-10 mx-auto max-w-[1450px] px-4 pb-28 pt-5 sm:px-6 sm:py-8 md:pb-8 lg:px-10">

        {/* Breadcrumb */}

        <button
          onClick={() =>
            router.push("/invest")
          }
          className="text-sm text-white/30 transition hover:text-white/70"
        >
          ← Back to investments
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


              <div className="rounded-[22px] border border-emerald-400/15 bg-emerald-400/[0.055] p-5 lg:min-w-[180px]">

                <p className="text-[10px] uppercase tracking-[0.13em] text-emerald-200/60">
                  Fund Score
                </p>

                <p className="mt-3 text-4xl font-semibold text-emerald-200">
                  {analytics?.performance_score ??
                    "—"}
                </p>

                <p className="mt-2 text-xs leading-5 text-white/30">
                  Historical performance score.
                  Personalized AI Fit comes next.
                </p>

              </div>

            </div>

          </div>


          {/* Investment Panel */}

          <div className="rounded-[24px] border border-emerald-400/15 bg-gradient-to-b from-emerald-400/[0.07] to-white/[0.025] p-5 sm:rounded-[30px] sm:p-7">

            <p className="text-[10px] uppercase tracking-[0.14em] text-emerald-200/65">
              INVEST
            </p>

            <h2 className="mt-3 text-2xl font-medium">
              Invest in this fund
            </h2>


            <div className="mt-6 grid grid-cols-2 gap-3">

              <button
                disabled={
                  !product.sip_allowed
                }
                onClick={() => {
                  setInvestmentMode(
                    "SIP"
                  );

                  setAmount(
                    String(
                      product.minimum_sip ||
                        500
                    )
                  );
                }}
                className={`rounded-[18px] border p-4 text-left transition ${
                  investmentMode === "SIP"
                    ? "border-emerald-400/30 bg-emerald-400/[0.09]"
                    : "border-white/[0.07] bg-black/10"
                } disabled:opacity-30`}
              >
                <p className="text-sm font-medium">
                  SIP
                </p>

                <p className="mt-2 text-xs text-white/30">
                  ₹
                  {formatMoney(
                    product.minimum_sip
                  )}
                  /month
                </p>
              </button>


              <button
                disabled={
                  !product.purchase_allowed
                }
                onClick={() => {
                  setInvestmentMode(
                    "LUMPSUM"
                  );

                  setAmount(
                    String(
                      product.minimum_lumpsum ||
                        1000
                    )
                  );
                }}
                className={`rounded-[18px] border p-4 text-left transition ${
                  investmentMode ===
                  "LUMPSUM"
                    ? "border-emerald-400/30 bg-emerald-400/[0.09]"
                    : "border-white/[0.07] bg-black/10"
                } disabled:opacity-30`}
              >
                <p className="text-sm font-medium">
                  One-time
                </p>

                <p className="mt-2 text-xs text-white/30">
                  ₹
                  {formatMoney(
                    product.minimum_lumpsum
                  )}
                </p>
              </button>

            </div>


            <div className="mt-5">

              <label className="text-xs text-white/35">
                Investment amount
              </label>

              <div className="relative mt-2">

                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30">
                  ₹
                </span>

                <input
                  type="number"
                  value={amount}
                  min="1"
                  onChange={(event) =>
                    setAmount(
                      event.target.value
                    )
                  }
                  className="w-full rounded-[16px] border border-white/[0.08] bg-black/15 py-4 pl-9 pr-4 text-lg outline-none focus:border-emerald-400/40"
                />

              </div>

            </div>


            {orderMessage && (
              <div className="mt-4 rounded-[15px] border border-white/[0.07] bg-black/10 px-4 py-3 text-xs leading-5 text-white/50">
                {orderMessage}
              </div>
            )}


            <button
              onClick={placeOrder}
              disabled={
                placingOrder ||
                Number(amount) <= 0
              }
              className="mt-5 w-full rounded-full bg-emerald-300 px-6 py-3.5 font-medium text-[#04100c] transition hover:bg-emerald-200 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {placingOrder
                ? "Creating order..."
                : investmentMode ===
                  "SIP"
                ? "Start SIP"
                : "Invest Now"}
            </button>


            <p className="mt-4 text-center text-[10px] leading-4 text-white/20">
              Current development flow creates an
              internal order. Regulated KYC,
              mandate/payment and execution will
              connect through the execution layer.
            </p>

          </div>

        </div>


        {/* NAV Chart */}

        <div className="mt-4 rounded-[24px] border border-white/[0.08] bg-white/[0.025] p-4 sm:mt-6 sm:rounded-[30px] sm:p-8">

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

        <section className="mt-6">

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


        {/* Risk Analytics */}

        <div className="mt-6 grid gap-5 xl:grid-cols-[1.25fr_.75fr]">

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

              <p className="text-[10px] uppercase tracking-[0.14em] text-emerald-200/65">
                INVESTIGENIE INTELLIGENCE
              </p>

              <h3 className="mt-4 text-2xl font-medium leading-snug">
                Personalized intelligence is coming next.
              </h3>

              <p className="mt-4 text-sm leading-6 text-white/40">
                This layer will combine this fund's
                analytics with your risk profile,
                Wealth DNA, goals, portfolio,
                ML predictions and financial-news
                signals.
              </p>


              <div className="mt-7 space-y-3">

                <AIStatusRow
                  label="Fund analytics"
                  value="Active"
                />

                <AIStatusRow
                  label="Personalized Fit"
                  value="Next phase"
                />

                <AIStatusRow
                  label="ML Outlook"
                  value="Next phase"
                />

                <AIStatusRow
                  label="News Sentiment"
                  value="Next phase"
                />

              </div>

            </div>

          </div>

        </div>


        {/* Fund Details */}

        <div className="mt-6 rounded-[30px] border border-white/[0.08] bg-white/[0.025] p-7">

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

        <div className="mt-6 grid gap-5 lg:grid-cols-2">

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