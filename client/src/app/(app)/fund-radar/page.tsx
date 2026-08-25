"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  BarChart3,
  Building,
  Building2,
  ChevronRight,
  CircleHelp,
  Gauge,
  Grid3X3,
  House,
  Layers3,
  LineChart,
  LockKeyhole,
  Search,
  SlidersHorizontal,
  Sparkles,
  Target,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

const API_BASE = "/api-backend";

type FundStatus =
  | "IN_FORM"
  | "ON_TRACK"
  | "OFF_TRACK"
  | "NOT_IN_FORM"
  | "UNRATED";

type InvestmentProduct = {
  id: number;
  name: string;
  product_type: string;

  isin: string | null;
  symbol: string | null;
  provider: string | null;

  category: string | null;
  sub_category: string | null;
  asset_class: string | null;
  risk_level: string | null;

  nav: number;
  expense_ratio: number;

  minimum_sip: number;
  minimum_lumpsum: number;

  return_1y: number;
  return_3y: number;
  return_5y: number;

  volatility: number;

  purchase_allowed: boolean;
  sip_allowed: boolean;

  source: string;

  fund_health_score?: number | null;
  fund_status?: FundStatus | string | null;

  // This is our final category-relative Form Score.
  peer_percentile?: number | null;

  data_quality_score?: number | null;

  return_1m?: number | null;
  return_3m?: number | null;
  return_6m?: number | null;

  aum?: number | null;
  launch_date?: string | null;
};

const fundFamilies = [
  "Equity",
  "Debt",
  "Hybrid",
  "Index & ETF",
  "FoF",
  "Other",
] as const;

type FundFamily =
  (typeof fundFamilies)[number];

const subcategoriesByFamily: Record<
  FundFamily,
  string[]
> = {
  Equity: [
    "All Equity",
    "Large Cap",
    "Mid Cap",
    "Small Cap",
    "Large & Mid Cap",
    "Multi Cap",
    "Flexi Cap",
    "ELSS",
    "Focused",
    "Value",
    "Dividend Yield",
    "Sectoral / Thematic",
  ],

  Debt: [
    "All Debt",
    "Overnight",
    "Liquid",
    "Ultra Short Duration",
    "Low Duration",
    "Money Market",
    "Short Duration",
    "Medium Duration",
    "Medium to Long Duration",
    "Long Duration",
    "Dynamic Bond",
    "Corporate Bond",
    "Credit Risk",
    "Banking & PSU",
    "Floater",
    "Gilt",
    "Gilt 10Y Constant Duration",
  ],

  Hybrid: [
    "All Hybrid",
    "Aggressive Hybrid",
    "Conservative Hybrid",
    "Balanced Advantage",
    "Arbitrage",
    "Equity Savings",
    "Multi Asset",
  ],

  "Index & ETF": [
    "All Index & ETF",
    "Index Funds",
    "ETF",
    "Gold",
  ],

  FoF: [
    "All FoF",
    "FoF Domestic",
    "FoF Overseas",
  ],

  Other: [
    "All Other",
    "Retirement",
    "Children",
    "Close Ended",
    "Interval",
    "Other",
  ],
};

const statuses: FundStatus[] = [
  "IN_FORM",
  "ON_TRACK",
  "OFF_TRACK",
  "NOT_IN_FORM",
  "UNRATED",
];

export default function FundRadarPage() {
  const router = useRouter();

  const [products, setProducts] =
    useState<InvestmentProduct[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [searchQuery, setSearchQuery] =
    useState("");

  const [
    selectedFamily,
    setSelectedFamily,
  ] =
    useState<FundFamily>("Equity");

  const [
    selectedSubcategory,
    setSelectedSubcategory,
  ] =
    useState("Large Cap");

  const [
    selectedStatus,
    setSelectedStatus,
  ] =
    useState<FundStatus | "ALL">(
      "ALL"
    );

  const [
    showAllVariants,
    setShowAllVariants,
  ] =
    useState(false);

  const [
    visibleCount,
    setVisibleCount,
  ] =
    useState(25);

  const [
    isPremium,
    setIsPremium,
  ] =
    useState(false);

  useEffect(() => {
    // Temporary client-side hook until subscription
    // entitlement comes from the backend.
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
    let cancelled = false;

    async function loadFunds() {
      const token =
        localStorage.getItem(
          "access_token"
        );

      if (!token) {
        router.replace("/login");
        return;
      }

      try {
        const response =
          await fetch(
            `${API_BASE}/investments/products`,
            {
              headers: {
                Authorization:
                  `Bearer ${token}`,
              },
            }
          );

        const data =
          await response.json();

        if (!response.ok) {
          if (
            response.status === 401
          ) {
            localStorage.removeItem(
              "access_token"
            );

            localStorage.removeItem(
              "token_type"
            );

            router.replace("/login");
            return;
          }

          if (!cancelled) {
            setError(
              data.detail ||
                "Could not load the fund universe."
            );
          }

          return;
        }

        if (!cancelled) {
          setProducts(data);
        }
      } catch {
        if (!cancelled) {
          setError(
            "Could not connect to InvestiGenie."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadFunds();

    return () => {
      cancelled = true;
    };
  }, [router]);

  const familyProducts =
    useMemo(() => {
      return products.filter(
        (product) =>
          getFundFamily(product) ===
          selectedFamily
      );
    }, [
      products,
      selectedFamily,
    ]);

  const categoryProducts =
    useMemo(() => {
      const familyAllLabel =
        subcategoriesByFamily[
          selectedFamily
        ][0];

      if (
        selectedSubcategory ===
        familyAllLabel
      ) {
        return familyProducts;
      }

      return familyProducts.filter(
        (product) =>
          getFundSubcategory(
            product
          ) ===
          selectedSubcategory
      );
    }, [
      familyProducts,
      selectedFamily,
      selectedSubcategory,
    ]);

  const displayCategoryProducts =
    useMemo(() => {
      if (showAllVariants) {
        return categoryProducts;
      }

      return collapseToBestSchemes(
        categoryProducts
      );
    }, [
      categoryProducts,
      showAllVariants,
    ]);

  const categoryStatusCounts =
    useMemo(() => {
      const result: Record<
        FundStatus,
        number
      > = {
        IN_FORM: 0,
        ON_TRACK: 0,
        OFF_TRACK: 0,
        NOT_IN_FORM: 0,
        UNRATED: 0,
      };

      for (
        const product of
          displayCategoryProducts
      ) {
        result[
          normalizeFundStatus(
            product
          )
        ] += 1;
      }

      return result;
    }, [
      displayCategoryProducts,
    ]);

  const rankedProducts =
    useMemo(() => {
      let result = [
        ...displayCategoryProducts,
      ];

      if (
        selectedStatus !== "ALL"
      ) {
        result =
          result.filter(
            (product) =>
              normalizeFundStatus(
                product
              ) === selectedStatus
          );
      }

      const query =
        searchQuery
          .trim()
          .toLowerCase();

      if (query) {
        result =
          result.filter(
            (product) =>
              product.name
                .toLowerCase()
                .includes(query) ||
              (
                product.provider ||
                ""
              )
                .toLowerCase()
                .includes(query) ||
              (
                product.symbol ||
                ""
              )
                .toLowerCase()
                .includes(query)
          );
      }

      // IMPORTANT:
      // Fund Radar always ranks by Form Score
      // descending. Unrated / null scores stay last.
      result.sort(
        compareByFormScore
      );

      return result;
    }, [
      displayCategoryProducts,
      selectedStatus,
      searchQuery,
    ]);

  const visibleProducts =
    rankedProducts.slice(
      0,
      visibleCount
    );

  const topPerformer =
    rankedProducts.find(
      (product) =>
        product.peer_percentile !=
        null
    ) || rankedProducts[0];

  const averageFormScore =
    useMemo(() => {
      const scores =
        displayCategoryProducts
          .map(
            (product) =>
              product.peer_percentile
          )
          .filter(
            (
              value
            ): value is number =>
              value != null &&
              !Number.isNaN(
                value
              )
          );

      if (!scores.length) {
        return null;
      }

      return (
        scores.reduce(
          (sum, value) =>
            sum + value,
          0
        ) / scores.length
      );
    }, [
      displayCategoryProducts,
    ]);

  useEffect(() => {
    setVisibleCount(25);
  }, [
    selectedFamily,
    selectedSubcategory,
    selectedStatus,
    searchQuery,
    showAllVariants,
  ]);

  function chooseFamily(
    family: FundFamily
  ) {
    setSelectedFamily(
      family
    );

    const defaultCategory =
      family === "Equity"
        ? "Large Cap"
        : subcategoriesByFamily[
            family
          ][0];

    setSelectedSubcategory(
      defaultCategory
    );

    setSelectedStatus(
      "ALL"
    );
  }

  if (loading) {
    return (
      <FundRadarSkeleton />
    );
  }

  return (
    <main className="relative min-h-screen overflow-x-hidden bg-[#05070b] text-white">
      <AmbientBackground />

      <div className="relative z-10 mx-auto w-full max-w-[1550px] px-3 pb-28 pt-4 sm:px-6 md:pb-10 lg:px-8 lg:pt-7 xl:px-10">
        {/* Header */}

        <section className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-2xl border border-emerald-400/15 bg-emerald-400/[0.06] text-emerald-200">
                <Gauge
                  size={18}
                />
              </div>

              <p className="text-[10px] font-medium tracking-[0.17em] text-emerald-200/65">
                FUND RADAR
              </p>
            </div>

            <h1 className="mt-3 text-2xl font-semibold tracking-[-0.04em] sm:text-4xl lg:text-5xl">
              {selectedFamily}
              <span className="mx-2 text-white/22">
                ›
              </span>
              <span className="text-emerald-300">
                {
                  selectedSubcategory
                }
              </span>
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-white/35">
              Ranked mutual-fund
              performance inside the
              selected peer category.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() =>
                setShowAllVariants(
                  (value) =>
                    !value
                )
              }
              className="min-h-11 rounded-2xl border border-white/[0.08] bg-white/[0.025] px-4 text-xs font-medium text-white/55 transition hover:border-emerald-400/20 hover:text-white"
            >
              {showAllVariants
                ? "All plans & options"
                : "Best scheme view"}
            </button>

            {!isPremium && (
              <button
                type="button"
                onClick={() =>
                  router.push(
                    "/invest"
                  )
                }
                className="hidden min-h-11 items-center gap-2 rounded-2xl border border-amber-300/20 bg-amber-300/[0.07] px-4 text-xs font-semibold text-amber-200 sm:flex"
              >
                <LockKeyhole
                  size={14}
                />
                Premium
              </button>
            )}
          </div>
        </section>

        {error && (
          <div className="mt-5 rounded-2xl border border-red-400/15 bg-red-400/[0.05] px-4 py-3 text-sm text-red-200/80">
            {error}
          </div>
        )}

        {/* Broad family selector */}

        <section className="mt-5 overflow-x-auto pb-1">
          <div className="flex min-w-max gap-2">
            {fundFamilies.map(
              (family) => (
                <button
                  key={family}
                  type="button"
                  onClick={() =>
                    chooseFamily(
                      family
                    )
                  }
                  className={`rounded-full border px-4 py-2.5 text-xs font-medium transition ${
                    selectedFamily ===
                    family
                      ? "border-emerald-400/25 bg-emerald-400/[0.09] text-emerald-200"
                      : "border-white/[0.07] bg-white/[0.02] text-white/38 hover:text-white/65"
                  }`}
                >
                  {family}
                </button>
              )
            )}
          </div>
        </section>

        {/* Reference-style category icon strip */}

        <section className="mt-4 rounded-[24px] border border-white/[0.07] bg-white/[0.022] px-2 py-3 sm:px-4">
          <div className="overflow-x-auto">
            <div className="flex min-w-max items-stretch gap-1 sm:gap-2">
              {subcategoriesByFamily[
                selectedFamily
              ].map(
                (
                  subcategory,
                  index
                ) => {
                  const Icon =
                    getCategoryIcon(
                      subcategory,
                      index
                    );

                  const active =
                    selectedSubcategory ===
                    subcategory;

                  return (
                    <button
                      key={
                        subcategory
                      }
                      type="button"
                      onClick={() => {
                        setSelectedSubcategory(
                          subcategory
                        );

                        setSelectedStatus(
                          "ALL"
                        );
                      }}
                      className={`group relative flex min-w-[88px] shrink-0 flex-col items-center justify-center rounded-2xl px-3 py-3 text-center transition sm:min-w-[105px] sm:px-4 ${
                        active
                          ? "bg-emerald-400/[0.07] text-emerald-200"
                          : "text-white/40 hover:bg-white/[0.025] hover:text-white/65"
                      }`}
                    >
                      <Icon
                        size={25}
                        strokeWidth={
                          active
                            ? 2.1
                            : 1.7
                        }
                      />

                      <span className="mt-2 max-w-[96px] text-[11px] font-medium leading-4 sm:text-xs">
                        {subcategory.replace(
                          "All ",
                          ""
                        )}
                      </span>

                      {active && (
                        <span className="absolute inset-x-3 bottom-0 h-0.5 rounded-full bg-emerald-300" />
                      )}
                    </button>
                  );
                }
              )}
            </div>
          </div>
        </section>

        {/* Status filters */}

        <section className="mt-4 overflow-x-auto pb-1">
          <div className="flex min-w-max items-center gap-2">
            <StatusChip
              label={`All (${displayCategoryProducts.length})`}
              active={
                selectedStatus ===
                "ALL"
              }
              tone="neutral"
              onClick={() =>
                setSelectedStatus(
                  "ALL"
                )
              }
            />

            {statuses.map(
              (status) => (
                <StatusChip
                  key={status}
                  label={`${getStatusMeta(status).label} (${categoryStatusCounts[status]})`}
                  active={
                    selectedStatus ===
                    status
                  }
                  tone={status}
                  onClick={() =>
                    setSelectedStatus(
                      status
                    )
                  }
                />
              )
            )}
          </div>
        </section>

        {/* Category snapshot */}

        <section className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          <SnapshotCard
            eyebrow="Top ranked"
            value={
              topPerformer
                ? compactFundName(
                    topPerformer.name
                  )
                : "—"
            }
            icon={
              <TrendingUp
                size={18}
              />
            }
            accent="emerald"
          />

          <SnapshotCard
            eyebrow="Schemes"
            value={
              displayCategoryProducts.length.toLocaleString(
                "en-IN"
              )
            }
            icon={
              <Grid3X3
                size={18}
              />
            }
          />

          <SnapshotCard
            eyebrow="In Form"
            value={`${categoryStatusCounts.IN_FORM.toLocaleString(
              "en-IN"
            )}`}
            note={
              percentageText(
                categoryStatusCounts.IN_FORM,
                displayCategoryProducts.length
              )
            }
            icon={
              <Gauge
                size={18}
              />
            }
            accent="emerald"
          />

          <SnapshotCard
            eyebrow="Not In Form"
            value={`${categoryStatusCounts.NOT_IN_FORM.toLocaleString(
              "en-IN"
            )}`}
            note={
              percentageText(
                categoryStatusCounts.NOT_IN_FORM,
                displayCategoryProducts.length
              )
            }
            icon={
              <TrendingDown
                size={18}
              />
            }
            accent="red"
          />
        </section>

        {/* Form Score explainer */}

        <section className="mt-4 rounded-[22px] border border-emerald-400/12 bg-emerald-400/[0.035] p-4 sm:p-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex max-w-3xl items-start gap-3">
              <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-400/[0.1] text-emerald-200">
                <CircleHelp
                  size={17}
                />
              </div>

              <div>
                <h2 className="text-sm font-semibold text-white/85">
                  What is Form Score?
                </h2>

                <p className="mt-1.5 text-xs leading-5 text-white/35 sm:text-sm sm:leading-6">
                  Form Score is a
                  0–100 category-relative
                  ranking. It combines
                  long-term performance,
                  consistency,
                  risk-adjusted performance,
                  recent momentum, downside
                  protection, volatility and
                  fund quality. Higher is
                  better.
                </p>
              </div>
            </div>

            <div className="flex shrink-0 items-center gap-2 rounded-2xl border border-amber-300/12 bg-amber-300/[0.04] px-4 py-3 text-xs text-amber-100/70">
              <LockKeyhole
                size={14}
              />

              {isPremium
                ? `Category average: ${
                    averageFormScore !=
                    null
                      ? averageFormScore.toFixed(
                          1
                        )
                      : "—"
                  }`
                : "Exact Form Scores are a Premium feature"}
            </div>
          </div>
        </section>

        {/* Search */}

        <section className="mt-4">
          <div className="relative">
            <Search
              size={17}
              className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-white/25"
            />

            <input
              type="search"
              value={
                searchQuery
              }
              onChange={(
                event
              ) =>
                setSearchQuery(
                  event.target
                    .value
                )
              }
              placeholder="Search fund or AMC..."
              className="h-12 w-full rounded-2xl border border-white/[0.07] bg-white/[0.02] pl-11 pr-4 text-sm text-white outline-none placeholder:text-white/18 transition focus:border-emerald-400/25"
            />
          </div>
        </section>

        {/* Results title */}

        <section className="mt-5">
          <div className="flex items-end justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold tracking-[-0.025em]">
                {
                  selectedSubcategory
                }
                {" "}
                funds
              </h2>

              <p className="mt-1 text-xs text-white/25">
                Ranked by Form
                Score, highest to
                lowest
              </p>
            </div>

            <p className="hidden text-xs text-white/20 sm:block">
              {
                rankedProducts.length
              }{" "}
              matching schemes
            </p>
          </div>

          {rankedProducts.length ===
          0 ? (
            <EmptyState />
          ) : (
            <>
              {/* Desktop table */}

              <div className="mt-4 hidden overflow-hidden rounded-[24px] border border-white/[0.07] bg-white/[0.018] lg:block">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="border-b border-white/[0.065] text-left">
                      <th className="w-[90px] px-5 py-4 text-[10px] font-medium uppercase tracking-[0.12em] text-white/28">
                        Rank
                      </th>

                      <th className="px-4 py-4 text-[10px] font-medium uppercase tracking-[0.12em] text-white/28">
                        Scheme
                      </th>

                      <th className="w-[180px] px-4 py-4 text-[10px] font-medium uppercase tracking-[0.12em] text-white/28">
                        Category
                      </th>

                      <th className="w-[190px] px-4 py-4 text-[10px] font-medium uppercase tracking-[0.12em] text-white/28">
                        Form Score
                      </th>

                      <th className="w-[160px] px-4 py-4 text-[10px] font-medium uppercase tracking-[0.12em] text-white/28">
                        Status
                      </th>

                      <th className="w-[60px] px-3 py-4" />
                    </tr>
                  </thead>

                  <tbody>
                    {visibleProducts.map(
                      (
                        product,
                        index
                      ) => (
                        <DesktopFundRow
                          key={
                            product.id
                          }
                          product={
                            product
                          }
                          rank={
                            index +
                            1
                          }
                          isPremium={
                            isPremium
                          }
                          onOpen={() =>
                            router.push(
                              `/fund-radar/${product.id}`
                            )
                          }
                        />
                      )
                    )}
                  </tbody>
                </table>
              </div>

              {/* Mobile / tablet cards */}

              <div className="mt-4 space-y-2.5 lg:hidden">
                {visibleProducts.map(
                  (
                    product,
                    index
                  ) => (
                    <MobileFundCard
                      key={
                        product.id
                      }
                      product={
                        product
                      }
                      rank={
                        index + 1
                      }
                      isPremium={
                        isPremium
                      }
                      onOpen={() =>
                        router.push(
                          `/fund-radar/${product.id}`
                        )
                      }
                    />
                  )
                )}
              </div>

              {visibleProducts.length <
                rankedProducts.length && (
                <div className="mt-6 flex justify-center">
                  <button
                    type="button"
                    onClick={() =>
                      setVisibleCount(
                        (
                          count
                        ) =>
                          count +
                          25
                      )
                    }
                    className="rounded-full border border-white/[0.08] bg-white/[0.025] px-6 py-3 text-sm text-white/55 transition hover:border-emerald-400/20 hover:text-emerald-200"
                  >
                    Load more
                  </button>
                </div>
              )}
            </>
          )}
        </section>

        {/* Premium CTA */}

        <section className="mt-7 rounded-[26px] border border-emerald-400/15 bg-gradient-to-r from-emerald-400/[0.055] to-cyan-400/[0.03] p-5 sm:p-7">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
            <div className="max-w-2xl">
              <div className="flex items-center gap-2 text-[10px] font-medium tracking-[0.14em] text-emerald-200/65">
                <Sparkles
                  size={13}
                />
                GENIE PREMIUM
              </div>

              <h2 className="mt-3 text-xl font-semibold tracking-[-0.035em] sm:text-2xl">
                Form tells you
                what is performing.
                Genie tells you
                what fits you.
              </h2>

              <p className="mt-3 text-sm leading-6 text-white/35">
                Premium combines
                Fund Radar with
                your risk profile,
                goals, portfolio
                and financial
                identity.
              </p>
            </div>

            <button
              type="button"
              onClick={() =>
                router.push(
                  "/invest"
                )
              }
              className="inline-flex min-h-12 items-center justify-center gap-2 rounded-2xl bg-emerald-300 px-5 text-sm font-semibold text-[#04100c] transition hover:bg-emerald-200"
            >
              Open Genie Invest
              <ArrowRight
                size={16}
              />
            </button>
          </div>
        </section>
      </div>
    </main>
  );
}

function DesktopFundRow({
  product,
  rank,
  isPremium,
  onOpen,
}: {
  product: InvestmentProduct;
  rank: number;
  isPremium: boolean;
  onOpen: () => void;
}) {
  const status =
    normalizeFundStatus(
      product
    );

  const meta =
    getStatusMeta(status);

  return (
    <tr
      onClick={onOpen}
      className="group cursor-pointer border-b border-white/[0.045] transition last:border-b-0 hover:bg-white/[0.025]"
    >
      <td className="px-5 py-4">
        <RankBadge
          rank={rank}
        />
      </td>

      <td className="px-4 py-4">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-white/[0.08] bg-white/[0.035] text-xs font-semibold text-white/55">
            {getInitials(
              product.provider
            )}
          </div>

          <div className="min-w-0">
            <p className="max-w-[440px] truncate text-sm font-semibold tracking-[-0.015em] text-white/82">
              {product.name}
            </p>

            <p className="mt-1 truncate text-[10px] text-white/25">
              {product.provider ||
                "Mutual fund"}
            </p>
          </div>
        </div>
      </td>

      <td className="px-4 py-4">
        <div className="flex items-center gap-2 text-xs text-white/45">
          <Building2
            size={14}
          />
          {getFundSubcategory(
            product
          )}
        </div>
      </td>

      <td className="px-4 py-4">
        <PremiumFormScore
          score={
            product.peer_percentile
          }
          isPremium={
            isPremium
          }
        />
      </td>

      <td className="px-4 py-4">
        <span
          className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.05em] ${meta.pillClass}`}
        >
          {meta.icon}
          {meta.label}
        </span>
      </td>

      <td className="px-3 py-4 text-right">
        <ChevronRight
          size={17}
          className="ml-auto text-white/18 transition group-hover:translate-x-0.5 group-hover:text-emerald-200/70"
        />
      </td>
    </tr>
  );
}

function MobileFundCard({
  product,
  rank,
  isPremium,
  onOpen,
}: {
  product: InvestmentProduct;
  rank: number;
  isPremium: boolean;
  onOpen: () => void;
}) {
  const status =
    normalizeFundStatus(
      product
    );

  const meta =
    getStatusMeta(status);

  return (
    <button
      type="button"
      onClick={onOpen}
      className="w-full rounded-[22px] border border-white/[0.07] bg-white/[0.024] p-4 text-left transition active:scale-[0.99]"
    >
      <div className="flex items-start gap-3">
        <RankBadge
          rank={rank}
          compact
        />

        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-white/[0.08] bg-white/[0.035] text-xs font-semibold text-white/55">
          {getInitials(
            product.provider
          )}
        </div>

        <div className="min-w-0 flex-1">
          <p className="line-clamp-2 text-sm font-semibold leading-5 tracking-[-0.015em] text-white/85">
            {product.name}
          </p>

          <p className="mt-1 truncate text-[10px] text-white/25">
            {getFundSubcategory(
              product
            )}
            {product.provider
              ? ` • ${product.provider}`
              : ""}
          </p>
        </div>

        <ChevronRight
          size={17}
          className="mt-1 shrink-0 text-white/18"
        />
      </div>

      <div className="mt-3 flex items-center justify-between gap-3 border-t border-white/[0.05] pt-3">
        <span
          className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1.5 text-[10px] font-semibold uppercase tracking-[0.04em] ${meta.pillClass}`}
        >
          {meta.icon}
          {meta.label}
        </span>

        <PremiumFormScore
          score={
            product.peer_percentile
          }
          isPremium={
            isPremium
          }
          compact
        />
      </div>

      <div className="mt-3 grid grid-cols-3 gap-2">
        <SmallMetric
          label="1Y"
          value={formatReturn(
            product.return_1y
          )}
        />

        <SmallMetric
          label="3Y"
          value={formatReturn(
            product.return_3y
          )}
        />

        <SmallMetric
          label="5Y"
          value={formatReturn(
            product.return_5y
          )}
        />
      </div>
    </button>
  );
}

function PremiumFormScore({
  score,
  isPremium,
  compact = false,
}: {
  score:
    | number
    | null
    | undefined;
  isPremium: boolean;
  compact?: boolean;
}) {
  if (!isPremium) {
    return (
      <div
        className={`inline-flex items-center gap-2 rounded-xl border border-amber-300/12 bg-amber-300/[0.04] text-amber-100/55 ${
          compact
            ? "px-2.5 py-1.5 text-[10px]"
            : "px-3 py-2 text-[10px]"
        }`}
      >
        <LockKeyhole
          size={
            compact
              ? 11
              : 13
          }
        />

        <span>
          Premium
        </span>
      </div>
    );
  }

  if (
    score == null ||
    Number.isNaN(score)
  ) {
    return (
      <span className="text-xs text-white/25">
        —
      </span>
    );
  }

  return (
    <span className="inline-flex min-w-[74px] items-center justify-center rounded-full border border-emerald-400/18 bg-emerald-400/[0.07] px-3 py-1.5 text-xs font-semibold text-emerald-200">
      {score.toFixed(2)}
    </span>
  );
}

function RankBadge({
  rank,
  compact = false,
}: {
  rank: number;
  compact?: boolean;
}) {
  const topClass =
    rank === 1
      ? "border-amber-300/20 bg-amber-300/[0.1] text-amber-200"
      : rank === 2
        ? "border-slate-300/15 bg-slate-300/[0.06] text-slate-200"
        : rank === 3
          ? "border-orange-300/15 bg-orange-300/[0.07] text-orange-200"
          : "border-white/[0.07] bg-white/[0.03] text-white/48";

  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center rounded-full border font-semibold ${topClass} ${
        compact
          ? "h-8 min-w-8 px-1.5 text-[11px]"
          : "h-9 min-w-9 px-2 text-xs"
      }`}
    >
      {rank}
    </span>
  );
}

function StatusChip({
  label,
  active,
  tone,
  onClick,
}: {
  label: string;
  active: boolean;
  tone:
    | FundStatus
    | "neutral";
  onClick: () => void;
}) {
  const base =
    "shrink-0 rounded-full border px-4 py-2 text-xs font-medium transition";

  if (tone === "neutral") {
    return (
      <button
        type="button"
        onClick={onClick}
        className={`${base} ${
          active
            ? "border-white/20 bg-white/[0.1] text-white"
            : "border-white/[0.07] bg-white/[0.02] text-white/40"
        }`}
      >
        {label}
      </button>
    );
  }

  const meta =
    getStatusMeta(tone);

  return (
    <button
      type="button"
      onClick={onClick}
      className={`${base} ${
        active
          ? meta.activeClass
          : meta.pillClass
      }`}
    >
      {label}
    </button>
  );
}

function SnapshotCard({
  eyebrow,
  value,
  note,
  icon,
  accent = "neutral",
}: {
  eyebrow: string;
  value: string;
  note?: string;
  icon:
    React.ReactNode;
  accent?:
    | "neutral"
    | "emerald"
    | "red";
}) {
  const accentClass =
    accent === "emerald"
      ? "text-emerald-200"
      : accent === "red"
        ? "text-red-200"
        : "text-white/55";

  return (
    <div className="rounded-[20px] border border-white/[0.07] bg-white/[0.022] p-4">
      <div
        className={`flex h-9 w-9 items-center justify-center rounded-xl border border-white/[0.06] bg-black/10 ${accentClass}`}
      >
        {icon}
      </div>

      <p className="mt-3 text-[9px] font-medium uppercase tracking-[0.12em] text-white/22">
        {eyebrow}
      </p>

      <div className="mt-1 flex items-end gap-2">
        <p className={`truncate text-lg font-semibold tracking-[-0.025em] ${accentClass}`}>
          {value}
        </p>

        {note && (
          <span className="pb-0.5 text-[10px] text-white/25">
            {note}
          </span>
        )}
      </div>
    </div>
  );
}

function SmallMetric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl border border-white/[0.055] bg-black/10 px-2.5 py-2.5">
      <p className="text-[8px] uppercase tracking-[0.1em] text-white/20">
        {label}
      </p>

      <p className="mt-1 text-xs font-medium text-white/62">
        {value}
      </p>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="mt-6 rounded-[24px] border border-dashed border-white/[0.08] bg-white/[0.02] px-6 py-14 text-center">
      <SlidersHorizontal
        size={24}
        className="mx-auto text-white/25"
      />

      <p className="mt-4 text-lg font-medium">
        No funds match these filters
      </p>

      <p className="mt-2 text-sm text-white/28">
        Change the category,
        status or search.
      </p>
    </div>
  );
}

function FundRadarSkeleton() {
  return (
    <main className="min-h-screen bg-[#05070b] px-4 py-5 text-white sm:px-6 lg:px-8">
      <div className="mx-auto max-w-[1550px] animate-pulse">
        <div className="h-9 w-52 rounded-xl bg-white/[0.04]" />

        <div className="mt-5 h-28 rounded-[24px] border border-white/[0.06] bg-white/[0.02]" />

        <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {Array.from({
            length: 4,
          }).map(
            (_, index) => (
              <div
                key={index}
                className="h-24 rounded-[20px] border border-white/[0.06] bg-white/[0.02]"
              />
            )
          )}
        </div>

        <div className="mt-5 h-[420px] rounded-[24px] border border-white/[0.06] bg-white/[0.02]" />
      </div>
    </main>
  );
}

function AmbientBackground() {
  return (
    <div className="pointer-events-none fixed inset-0">
      <div className="absolute left-[12%] top-[-14rem] h-[30rem] w-[30rem] rounded-full bg-emerald-400/[0.05] blur-[125px]" />

      <div className="absolute right-[-10rem] top-[26rem] h-[28rem] w-[28rem] rounded-full bg-cyan-400/[0.03] blur-[125px]" />
    </div>
  );
}

function compareByFormScore(
  a: InvestmentProduct,
  b: InvestmentProduct
) {
  const aScore =
    a.peer_percentile;

  const bScore =
    b.peer_percentile;

  if (
    aScore == null &&
    bScore == null
  ) {
    return a.name.localeCompare(
      b.name
    );
  }

  if (aScore == null) {
    return 1;
  }

  if (bScore == null) {
    return -1;
  }

  if (bScore !== aScore) {
    return bScore - aScore;
  }

  return a.name.localeCompare(
    b.name
  );
}

function collapseToBestSchemes(
  products: InvestmentProduct[]
) {
  const groups =
    new Map<
      string,
      InvestmentProduct[]
    >();

  for (
    const product of products
  ) {
    const key =
      getUnderlyingSchemeKey(
        product
      );

    const bucket =
      groups.get(key) || [];

    bucket.push(product);

    groups.set(
      key,
      bucket
    );
  }

  return Array.from(
    groups.values()
  ).map(
    chooseDisplayVariant
  );
}

function getUnderlyingSchemeKey(
  product: InvestmentProduct
) {
  return [
    product.provider || "",
    normalizeUnderlyingSchemeName(
      product.name
    ),
    getFundSubcategory(
      product
    ),
  ]
    .join("|")
    .toLowerCase();
}

function chooseDisplayVariant(
  variants: InvestmentProduct[]
) {
  return [
    ...variants,
  ].sort(
    (a, b) =>
      displayVariantScore(b) -
      displayVariantScore(a)
  )[0];
}

function displayVariantScore(
  product: InvestmentProduct
) {
  const name =
    product.name.toLowerCase();

  const direct =
    name.includes("direct");

  const growth =
    name.includes("growth");

  const idcw =
    name.includes("idcw") ||
    name.includes(
      "dividend"
    );

  return (
    (direct ? 10000 : 0) +
    (growth ? 5000 : 0) -
    (idcw ? 1000 : 0) +
    (product.data_quality_score ||
      0)
  );
}

function normalizeUnderlyingSchemeName(
  name: string
) {
  return name
    .toLowerCase()
    .replace(
      /\b(direct|regular|institutional|wealth)\b/g,
      " "
    )
    .replace(
      /\b(plan|option)\b/g,
      " "
    )
    .replace(
      /\b(growth|idcw|dividend|bonus)\b/g,
      " "
    )
    .replace(
      /income distribution cum capital withdrawal/g,
      " "
    )
    .replace(
      /[^a-z0-9]+/g,
      " "
    )
    .replace(
      /\s+/g,
      " "
    )
    .trim();
}

function normalizeFundStatus(
  product: InvestmentProduct
): FundStatus {
  const raw =
    String(
      product.fund_status ||
        ""
    )
      .trim()
      .toUpperCase()
      .replaceAll(
        "-",
        "_"
      )
      .replaceAll(
        " ",
        "_"
      );

  if (
    raw === "IN_FORM"
  ) {
    return "IN_FORM";
  }

  if (
    raw === "ON_TRACK"
  ) {
    return "ON_TRACK";
  }

  if (
    raw === "OFF_TRACK"
  ) {
    return "OFF_TRACK";
  }

  if (
    raw ===
      "NOT_IN_FORM" ||
    raw ===
      "OUT_OF_FORM"
  ) {
    return "NOT_IN_FORM";
  }

  return "UNRATED";
}

function getStatusMeta(
  status: FundStatus
) {
  if (
    status === "IN_FORM"
  ) {
    return {
      label: "In Form",
      icon: (
        <TrendingUp
          size={13}
        />
      ),
      pillClass:
        "border-emerald-400/15 bg-emerald-400/[0.07] text-emerald-200",
      activeClass:
        "border-emerald-400/30 bg-emerald-400/[0.11] text-emerald-100",
    };
  }

  if (
    status === "ON_TRACK"
  ) {
    return {
      label: "On Track",
      icon: (
        <LineChart
          size={13}
        />
      ),
      pillClass:
        "border-blue-400/15 bg-blue-400/[0.06] text-blue-200",
      activeClass:
        "border-blue-400/30 bg-blue-400/[0.1] text-blue-100",
    };
  }

  if (
    status === "OFF_TRACK"
  ) {
    return {
      label: "Off Track",
      icon: (
        <TrendingDown
          size={13}
        />
      ),
      pillClass:
        "border-amber-400/15 bg-amber-400/[0.06] text-amber-200",
      activeClass:
        "border-amber-400/30 bg-amber-400/[0.1] text-amber-100",
    };
  }

  if (
    status ===
    "NOT_IN_FORM"
  ) {
    return {
      label:
        "Not In Form",
      icon: (
        <TrendingDown
          size={13}
        />
      ),
      pillClass:
        "border-red-400/15 bg-red-400/[0.06] text-red-200",
      activeClass:
        "border-red-400/30 bg-red-400/[0.1] text-red-100",
    };
  }

  return {
    label: "Unrated",
    icon: (
      <CircleHelp
        size={13}
      />
    ),
    pillClass:
      "border-white/[0.08] bg-white/[0.03] text-white/42",
    activeClass:
      "border-white/[0.15] bg-white/[0.07] text-white/75",
  };
}

function getCategoryIcon(
  subcategory: string,
  index: number
) {
  const text =
    subcategory.toLowerCase();

  if (
    text.includes(
      "large & mid"
    ) ||
    text.includes(
      "large and mid"
    )
  ) {
    return Layers3;
  }

  if (
    text.includes(
      "large cap"
    )
  ) {
    return Building2;
  }

  if (
    text.includes("mid cap")
  ) {
    return Building;
  }

  if (
    text.includes(
      "small cap"
    )
  ) {
    return House;
  }

  if (
    text.includes(
      "multi cap"
    ) ||
    text.includes(
      "multi asset"
    )
  ) {
    return Grid3X3;
  }

  if (
    text.includes(
      "focused"
    )
  ) {
    return Target;
  }

  if (
    text.includes(
      "sectoral"
    ) ||
    text.includes(
      "thematic"
    )
  ) {
    return BarChart3;
  }

  const fallback = [
    Gauge,
    Building2,
    Building,
    House,
    Layers3,
    Grid3X3,
    Target,
    BarChart3,
  ];

  return fallback[
    index %
      fallback.length
  ];
}

function normalizedCategoryText(
  product: InvestmentProduct
) {
  return [
    product.category,
    product.sub_category,
    product.asset_class,
    product.name,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase()
    .replaceAll(
      "âs",
      "'s"
    )
    .replace(
      /\s+/g,
      " "
    );
}

function getFundFamily(
  product: InvestmentProduct
): FundFamily {
  const text =
    normalizedCategoryText(
      product
    );

  if (
    text.includes(
      "equity scheme"
    ) ||
    text.includes(
      "equity schemes"
    ) ||
    text.includes("elss") ||
    text.includes(
      "large cap"
    ) ||
    text.includes(
      "mid cap"
    ) ||
    text.includes(
      "small cap"
    ) ||
    text.includes(
      "flexi cap"
    ) ||
    text.includes(
      "multi cap"
    ) ||
    text.includes(
      "focused fund"
    ) ||
    text.includes(
      "value fund"
    ) ||
    text.includes(
      "dividend yield"
    ) ||
    text.includes(
      "sectoral"
    ) ||
    text.includes(
      "thematic"
    )
  ) {
    return "Equity";
  }

  if (
    text.includes(
      "debt scheme"
    ) ||
    text.includes(
      "income/debt"
    ) ||
    text.includes(
      "liquid fund"
    ) ||
    text.includes(
      "overnight fund"
    ) ||
    text.includes(
      "duration fund"
    ) ||
    text.includes(
      "money market"
    ) ||
    text.includes(
      "corporate bond"
    ) ||
    text.includes(
      "credit risk"
    ) ||
    text.includes(
      "banking and psu"
    ) ||
    text.includes(
      "gilt fund"
    ) ||
    text.includes(
      "floater fund"
    ) ||
    text.includes(
      "dynamic bond"
    )
  ) {
    return "Debt";
  }

  if (
    text.includes(
      "hybrid scheme"
    ) ||
    text.includes(
      "aggressive hybrid"
    ) ||
    text.includes(
      "conservative hybrid"
    ) ||
    text.includes(
      "balanced advantage"
    ) ||
    text.includes(
      "dynamic asset allocation"
    ) ||
    text.includes(
      "arbitrage fund"
    ) ||
    text.includes(
      "equity savings"
    ) ||
    text.includes(
      "multi asset allocation"
    )
  ) {
    return "Hybrid";
  }

  if (
    text.includes(
      "index fund"
    ) ||
    text.includes(
      "index funds"
    ) ||
    text.includes("etf") ||
    text.includes(
      "exchange traded"
    ) ||
    text.includes("gold")
  ) {
    return "Index & ETF";
  }

  if (
    text.includes("fof") ||
    text.includes(
      "fund of funds"
    )
  ) {
    return "FoF";
  }

  return "Other";
}

function getFundSubcategory(
  product: InvestmentProduct
) {
  const text =
    normalizedCategoryText(
      product
    );

  const family =
    getFundFamily(product);

  if (
    family === "Equity"
  ) {
    if (
      text.includes(
        "large & mid cap"
      ) ||
      text.includes(
        "large and mid cap"
      )
    ) {
      return "Large & Mid Cap";
    }

    if (
      text.includes(
        "large cap"
      )
    ) {
      return "Large Cap";
    }

    if (
      text.includes(
        "mid cap"
      )
    ) {
      return "Mid Cap";
    }

    if (
      text.includes(
        "small cap"
      )
    ) {
      return "Small Cap";
    }

    if (
      text.includes(
        "multi cap"
      )
    ) {
      return "Multi Cap";
    }

    if (
      text.includes(
        "flexi cap"
      )
    ) {
      return "Flexi Cap";
    }

    if (
      text.includes("elss")
    ) {
      return "ELSS";
    }

    if (
      text.includes(
        "focused fund"
      )
    ) {
      return "Focused";
    }

    if (
      text.includes(
        "value fund"
      )
    ) {
      return "Value";
    }

    if (
      text.includes(
        "dividend yield"
      )
    ) {
      return "Dividend Yield";
    }

    if (
      text.includes(
        "sectoral"
      ) ||
      text.includes(
        "thematic"
      )
    ) {
      return "Sectoral / Thematic";
    }

    return "All Equity";
  }

  if (
    family === "Debt"
  ) {
    if (
      text.includes(
        "overnight"
      )
    ) {
      return "Overnight";
    }

    if (
      text.includes("liquid")
    ) {
      return "Liquid";
    }

    if (
      text.includes(
        "ultra short"
      )
    ) {
      return "Ultra Short Duration";
    }

    if (
      text.includes(
        "low duration"
      )
    ) {
      return "Low Duration";
    }

    if (
      text.includes(
        "money market"
      )
    ) {
      return "Money Market";
    }

    if (
      text.includes(
        "medium to long"
      )
    ) {
      return "Medium to Long Duration";
    }

    if (
      text.includes(
        "medium duration"
      )
    ) {
      return "Medium Duration";
    }

    if (
      text.includes(
        "short duration"
      )
    ) {
      return "Short Duration";
    }

    if (
      text.includes(
        "long duration"
      )
    ) {
      return "Long Duration";
    }

    if (
      text.includes(
        "dynamic bond"
      )
    ) {
      return "Dynamic Bond";
    }

    if (
      text.includes(
        "corporate bond"
      )
    ) {
      return "Corporate Bond";
    }

    if (
      text.includes(
        "credit risk"
      )
    ) {
      return "Credit Risk";
    }

    if (
      text.includes(
        "banking and psu"
      ) ||
      text.includes(
        "banking & psu"
      )
    ) {
      return "Banking & PSU";
    }

    if (
      text.includes(
        "floater"
      )
    ) {
      return "Floater";
    }

    if (
      text.includes(
        "10 year constant"
      )
    ) {
      return "Gilt 10Y Constant Duration";
    }

    if (
      text.includes("gilt")
    ) {
      return "Gilt";
    }

    return "All Debt";
  }

  if (
    family === "Hybrid"
  ) {
    if (
      text.includes(
        "aggressive hybrid"
      )
    ) {
      return "Aggressive Hybrid";
    }

    if (
      text.includes(
        "conservative hybrid"
      )
    ) {
      return "Conservative Hybrid";
    }

    if (
      text.includes(
        "balanced advantage"
      ) ||
      text.includes(
        "dynamic asset allocation"
      )
    ) {
      return "Balanced Advantage";
    }

    if (
      text.includes(
        "arbitrage"
      )
    ) {
      return "Arbitrage";
    }

    if (
      text.includes(
        "equity savings"
      )
    ) {
      return "Equity Savings";
    }

    if (
      text.includes(
        "multi asset"
      )
    ) {
      return "Multi Asset";
    }

    return "All Hybrid";
  }

  if (
    family ===
    "Index & ETF"
  ) {
    if (
      text.includes("gold")
    ) {
      return "Gold";
    }

    if (
      text.includes("etf") ||
      text.includes(
        "exchange traded"
      )
    ) {
      return "ETF";
    }

    if (
      text.includes("index")
    ) {
      return "Index Funds";
    }

    return "All Index & ETF";
  }

  if (family === "FoF") {
    if (
      text.includes(
        "overseas"
      )
    ) {
      return "FoF Overseas";
    }

    if (
      text.includes(
        "domestic"
      ) ||
      text.includes(
        "fund of funds"
      )
    ) {
      return "FoF Domestic";
    }

    return "All FoF";
  }

  if (
    text.includes(
      "retirement"
    )
  ) {
    return "Retirement";
  }

  if (
    text.includes(
      "children"
    )
  ) {
    return "Children";
  }

  if (
    text.includes(
      "close ended"
    )
  ) {
    return "Close Ended";
  }

  if (
    text.includes(
      "interval"
    )
  ) {
    return "Interval";
  }

  return "Other";
}

function getInitials(
  provider: string | null
) {
  if (!provider) {
    return "MF";
  }

  return provider
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map(
      (part) =>
        part[0]
    )
    .join("")
    .toUpperCase();
}

function compactFundName(
  name: string
) {
  return name
    .replace(
      /\s*-\s*/g,
      " "
    )
    .replace(
      /\bDirect Plan\b/gi,
      ""
    )
    .replace(
      /\bRegular Plan\b/gi,
      ""
    )
    .replace(
      /\bGrowth Option\b/gi,
      ""
    )
    .replace(
      /\bGrowth\b/gi,
      ""
    )
    .replace(
      /\s+/g,
      " "
    )
    .trim();
}

function percentageText(
  value: number,
  total: number
) {
  if (!total) {
    return "0%";
  }

  return `${Math.round(
    (value / total) * 100
  )}%`;
}

function formatReturn(
  value?: number | null
) {
  if (
    value == null ||
    Number.isNaN(value)
  ) {
    return "—";
  }

  const sign =
    value > 0 ? "+" : "";

  return `${sign}${value.toFixed(
    1
  )}%`;
}
