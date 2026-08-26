"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

const API_BASE = "/api-backend";

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
};

function getMainCategory(
product: InvestmentProduct
) {
  const category = (
    product.category || ""
  ).toLowerCase();

  const name =
    product.name.toLowerCase();

  if (
    category.includes("gold") ||
    name.includes("gold")
  ) {
    return "Gold";
  }

  if (
    category.includes("etf") ||
    name.includes("etf")
  ) {
    return "ETF";
  }

  if (
    category.includes("index")
  ) {
    return "Index";
  }

  if (
    category.includes("hybrid")
  ) {
    return "Hybrid";
  }

  if (
    category.includes("debt") ||
    category.includes("income") ||
    category.includes("liquid") ||
    category.includes("gilt") ||
    category.includes("money market")
  ) {
    return "Debt";
  }

  if (
    category.includes("equity")
  ) {
    return "Equity";
  }

  return "Other";
}

export default function InvestPage() {
  const router = useRouter();

  const [products, setProducts] =
    useState<InvestmentProduct[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [selectedCategory, setSelectedCategory] =
    useState("All");

  const [searchQuery, setSearchQuery] =
    useState("");

  const [sortBy, setSortBy] =
    useState<"NAME" | "NAV_HIGH" | "RETURN_1Y">("NAME");

  const [visibleCount, setVisibleCount] =
    useState(20);

  const [selectedProduct, setSelectedProduct] =
    useState<InvestmentProduct | null>(null);

  const [investmentMode, setInvestmentMode] =
    useState<"SIP" | "LUMPSUM">("SIP");

  const [amount, setAmount] =
    useState("");

  const [placingOrder, setPlacingOrder] =
    useState(false);

  const [orderMessage, setOrderMessage] =
    useState("");

  useEffect(() => {
    async function loadProducts() {
      const token =
        localStorage.getItem("access_token");

      if (!token) {
        router.push("/login");
        return;
      }

      try {
        const response = await fetch(
          `${API_BASE}/investments/products`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        const data =
          await response.json();

        if (!response.ok) {
          if (response.status === 401) {
            localStorage.removeItem("access_token");
            router.push("/login");
            return;
          }

          setError(
            data.detail ||
              "Could not load investments."
          );
          return;
        }

        setProducts(data);
      } catch {
        setError(
          "Could not connect to TopOne backend."
        );

      } finally {
        setLoading(false);
      }
    }

    loadProducts();
  }, [router]);

  const categories = [
    "All",
    "Equity",
    "Debt",
    "Hybrid",
    "Index",
    "ETF",
    "Gold",
  ];


  const filteredProducts =
    useMemo(() => {
      let result =
        [...products];

      if (
        selectedCategory !== "All"
      ) {
        result =
          result.filter(
            (product) =>
              getMainCategory(
                product
              ) ===
              selectedCategory
          );
      }

      if (
        searchQuery.trim()
      ) {
        const query =
          searchQuery
            .trim()
            .toLowerCase();

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

      if (
        sortBy === "NAV_HIGH"
      ) {
        result.sort(
          (a, b) =>
            (b.nav || 0) -
            (a.nav || 0)
        );
      } else if (
        sortBy === "RETURN_1Y"
      ) {
        result.sort(
          (a, b) =>
            (b.return_1y || 0) -
            (a.return_1y || 0)
        );
      } else {
        result.sort(
          (a, b) =>
            a.name.localeCompare(
              b.name
            )
        );
      }

      return result;
    }, [
      products,
      selectedCategory,
      searchQuery,
      sortBy,
    ]);

  const visibleProducts =
    filteredProducts.slice(
      0,
      visibleCount
    );

  useEffect(() => {
    setVisibleCount(20);
  }, [
    selectedCategory,
    searchQuery,
    sortBy,
  ]);

  function openInvestModal(
    product: InvestmentProduct
  ) {
    setSelectedProduct(product);

    if (product.sip_allowed) {
      setInvestmentMode("SIP");

      setAmount(
        String(
          product.minimum_sip || 500
        )
      );
    } else {
      setInvestmentMode("LUMPSUM");

      setAmount(
        String(
          product.minimum_lumpsum ||
            1000
        )
      );
    }

    setOrderMessage("");
  }

  async function placeOrder() {
    if (!selectedProduct) {
      return;
    }

    const token =
      localStorage.getItem("access_token");

    if (!token) {
      router.push("/login");
      return;
    }

    setPlacingOrder(true);
    setOrderMessage("");

    try {
      const response = await fetch(
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
              selectedProduct.id,

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
        `Order #${data.id} created successfully. Status: ${data.status}`
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

          <div className="mx-auto h-9 w-9 animate-spin rounded-full border-2 border-white/10 border-t-emerald-300" />

          <p className="mt-5 text-sm text-white/40">
            Preparing investment opportunities...
          </p>

        </div>
      </main>
    );
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#05070b] text-white">

      {/* Background */}

      <div className="pointer-events-none fixed inset-0">

        <div className="absolute left-[18%] top-[-15rem] h-[30rem] w-[30rem] rounded-full bg-emerald-400/[0.06] blur-[120px]" />

        <div className="absolute right-[-10rem] top-[24rem] h-[26rem] w-[26rem] rounded-full bg-cyan-400/[0.04] blur-[120px]" />

      </div>


      {/* Navigation */}

      <nav className="relative z-20 hidden border-b border-white/[0.06] bg-[#05070b]/70 backdrop-blur-2xl md:block">

        <div className="mx-auto flex max-w-[1450px] items-center justify-between px-6 py-5 lg:px-10">

          <button
            onClick={() =>
              router.push("/dashboard")
            }
            className="flex items-center gap-3"
          >

            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-emerald-400/20 bg-emerald-400/[0.07]">

              <div className="h-3 w-3 rounded-full bg-emerald-300 shadow-[0_0_16px_rgba(110,231,183,.75)]" />

            </div>

            <span className="text-xl font-semibold tracking-[-0.03em]">
              <span className="text-emerald-300">Top</span>One
            </span>

          </button>


          <div className="flex items-center gap-3">

            <button
              onClick={() =>
                router.push("/portfolio")
              }
              className="rounded-full border border-white/[0.08] bg-white/[0.035] px-5 py-2.5 text-sm text-white/55 transition hover:bg-white/[0.06] hover:text-white"
            >
              Portfolio
            </button>

            <button
              onClick={() =>
                router.push(
                  "/invest/orders"
                )
              }
              className="hidden rounded-full border border-white/[0.08] bg-white/[0.035] px-5 py-2.5 text-sm text-white/55 transition hover:bg-white/[0.06] hover:text-white sm:block"
            >
              Orders
            </button>

            <button
              onClick={() =>
                router.push("/dashboard")
              }
              className="rounded-full border border-white/[0.08] bg-white/[0.035] px-5 py-2.5 text-sm text-white/55 transition hover:bg-white/[0.06] hover:text-white"
            >
              Dashboard
            </button>

          </div>

        </div>

      </nav>


      <section className="relative z-10 mx-auto max-w-[1450px] px-4 pb-28 pt-5 sm:px-6 sm:py-10 md:pb-10 lg:px-10">

        {/* Hero */}

        <div className="flex flex-col gap-7 lg:flex-row lg:items-end lg:justify-between">

          <div>

            <p className="text-[11px] font-medium tracking-[0.17em] text-emerald-200/70">
              INVESTMENT DISCOVERY
            </p>

            <h1 className="mt-3 text-3xl font-semibold tracking-[-0.045em] sm:mt-4 sm:text-5xl">

              Discover investments

              <span className="text-white/35">
                {" "}
                built around you.
              </span>

            </h1>

            <p className="mt-4 max-w-2xl text-sm leading-6 text-white/40">
              Explore investment products from the
              TopOne catalog. Suitability

              intelligence will progressively combine
              your risk profile, goals, portfolio,
              Wealth DNA and market signals.
            </p>

          </div>


          <div className="hidden rounded-[22px] border border-emerald-400/15 bg-emerald-400/[0.05] px-6 py-4 md:block">

            <p className="text-xs text-white/30">
              Product Catalog
            </p>

            <p className="mt-2 text-sm font-medium text-emerald-200">
              {products.length} products available
            </p>

          </div>

        </div>


        {error && (
          <div className="mt-6 rounded-2xl border border-red-400/15 bg-red-400/[0.04] px-5 py-4 text-sm text-red-200/80">
            {error}
          </div>
        )}


        {/* Search + Filters */}

        <div className="mt-6 rounded-[22px] border border-white/[0.07] bg-white/[0.025] p-3 sm:mt-9 sm:rounded-[26px] sm:p-5">

          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">

            <div className="relative w-full lg:max-w-2xl">

              <div className="pointer-events-none absolute inset-y-0 left-4 flex items-center text-white/25">
                ⌕
              </div>

              <input
                type="text"
                value={searchQuery}
                onChange={(event) =>
                  setSearchQuery(
                    event.target.value
                  )
                }
                placeholder="Search funds, AMC or symbol..."
                className="w-full rounded-[18px] border border-white/[0.08] bg-black/15 py-3.5 pl-10 pr-4 text-sm text-white outline-none placeholder:text-white/20 transition focus:border-emerald-400/30 focus:bg-black/20"
              />

            </div>


            <select
              value={sortBy}
              onChange={(event) =>
                setSortBy(
                  event.target.value as
                    | "NAME"
                    | "NAV_HIGH"
                    | "RETURN_1Y"
                )
              }
              className="rounded-[16px] border border-white/[0.08] bg-[#0b0e13] px-4 py-3 text-sm text-white/60 outline-none"
            >
              <option value="NAME">
                Sort: Name
              </option>

              <option value="NAV_HIGH">
                NAV: High to Low
              </option>

              <option value="RETURN_1Y">
                1Y Return: High to Low
              </option>
            </select>

          </div>


          <div className="mt-4 flex gap-2 overflow-x-auto pb-1">

            {categories.map(
              (category) => (

                <button
                  key={category}
                  onClick={() =>
                    setSelectedCategory(
                      category
                    )
                  }
                  className={`shrink-0 rounded-full px-4 py-2 text-sm transition ${
                    selectedCategory ===
                    category
                      ? "bg-emerald-300 text-[#04100c]"
                      : "border border-white/[0.08] bg-white/[0.025] text-white/45 hover:bg-white/[0.05] hover:text-white"
                  }`}
                >
                  {category}
                </button>

              )
            )}

          </div>

        </div>


        <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">

          <div>

            <p className="text-sm font-medium text-white/75">
              {selectedCategory ===
              "All"
                ? "All Funds"
                : `${selectedCategory} Funds`}
            </p>

            <p className="mt-1 text-xs text-white/25">
              {
                filteredProducts.length
              }{" "}
              matching products
            </p>

          </div>

          <p className="text-xs text-white/20">
            Showing{" "}
            {Math.min(
              visibleProducts.length,
              filteredProducts.length
            )}{" "}
            of{" "}
            {
              filteredProducts.length
            }
          </p>

        </div>


        {/* Product Grid */}

        {filteredProducts.length === 0 ? (

          <div className="mt-8 rounded-[28px] border border-dashed border-white/[0.08] bg-white/[0.02] p-12 text-center">

            <p className="text-xl font-medium">
              No products available
            </p>

            <p className="mt-3 text-sm text-white/35">
              Seed the product catalog or select
              another category.
            </p>

          </div>

        ) : (

          <div className="mt-8 grid gap-5 lg:grid-cols-2">

            {visibleProducts.map(
              (product) => (

                <ProductCard
                  key={product.id}
                  product={product}
                  onInvest={() =>
                    openInvestModal(
                      product
                    )
                  }
                  onView={() =>
                    router.push(
                      `/invest/${product.id}`
                    )
                  }
                />

              )
            )}

          </div>

        )}


        {visibleProducts.length <
          filteredProducts.length && (

          <div className="mt-8 flex justify-center">

            <button
              onClick={() =>
                setVisibleCount(
                  (count) =>
                    count + 20
                )
              }
              className="rounded-full border border-white/[0.09] bg-white/[0.035] px-6 py-3 text-sm text-white/60 transition hover:border-emerald-400/20 hover:bg-emerald-400/[0.05] hover:text-emerald-200"
            >
              Load More Funds
            </button>

          </div>

        )}

      </section>


      {/* Investment Modal */}

      {selectedProduct && (

        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/75 backdrop-blur-xl sm:items-center sm:p-4">

          <div className="max-h-[92dvh] w-full max-w-xl overflow-y-auto rounded-t-[30px] border border-white/[0.1] bg-[#090c11] p-5 shadow-2xl sm:rounded-[30px] sm:p-7">

            <div className="flex items-start justify-between gap-5">

              <div>

                <p className="text-[10px] uppercase tracking-[0.14em] text-emerald-200/60">
                  INVESTMENT ORDER
                </p>

                <h2 className="mt-3 text-2xl font-medium">
                  {selectedProduct.name}
                </h2>

                <p className="mt-2 text-sm text-white/35">
                  {selectedProduct.provider ||
                    "Investment Product"}
                </p>

              </div>


              <button
                onClick={() =>
                  setSelectedProduct(
                    null
                  )
                }
                className="rounded-full border border-white/[0.08] px-3 py-1.5 text-sm text-white/35 transition hover:text-white"
              >
                ✕
              </button>

            </div>


            {/* Mode */}

            <div className="mt-7">

              <p className="text-xs text-white/35">
                Investment type
              </p>

              <div className="mt-3 grid grid-cols-2 gap-3">

                <button
                  type="button"
                  disabled={
                    !selectedProduct.sip_allowed
                  }
                  onClick={() => {
                    setInvestmentMode(
                      "SIP"
                    );

                    setAmount(
                      String(
                        selectedProduct.minimum_sip ||
                          500
                      )
                    );
                  }}
                  className={`rounded-[18px] border p-4 text-left transition ${
                    investmentMode === "SIP"

                      ? "border-emerald-400/30 bg-emerald-400/[0.08]"

                      : "border-white/[0.07] bg-white/[0.025]"
                  } disabled:cursor-not-allowed disabled:opacity-30`}
                >

                  <p className="text-sm font-medium">
                    SIP
                  </p>

                  <p className="mt-2 text-xs text-white/30">
                    From ₹
                    {formatMoney(
                      selectedProduct.minimum_sip
                    )}{" "}
                    / month
                  </p>

                </button>


                <button
                  type="button"
                  disabled={
                    !selectedProduct.purchase_allowed
                  }
                  onClick={() => {
                    setInvestmentMode(
                      "LUMPSUM"
                    );

                    setAmount(
                      String(
                        selectedProduct.minimum_lumpsum ||
                          1000
                      )
                    );
                  }}
                  className={`rounded-[18px] border p-4 text-left transition ${
                    investmentMode ===
                    "LUMPSUM"

                      ? "border-emerald-400/30 bg-emerald-400/[0.08]"

                      : "border-white/[0.07] bg-white/[0.025]"
                  } disabled:cursor-not-allowed disabled:opacity-30`}
                >

                  <p className="text-sm font-medium">
                    One-time
                  </p>

                  <p className="mt-2 text-xs text-white/30">
                    From ₹
                    {formatMoney(
                      selectedProduct.minimum_lumpsum
                    )}
                  </p>

                </button>

              </div>

            </div>


            {/* Amount */}

            <div className="mt-6">

              <label className="text-xs text-white/35">
                Amount
              </label>

              <div className="relative mt-2">

                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30">
                  ₹
                </span>

                <input
                  type="number"
                  min="1"
                  step="1"
                  value={amount}
                  onChange={(event) =>
                    setAmount(
                      event.target.value
                    )
                  }
                  className="w-full rounded-[16px] border border-white/[0.08] bg-white/[0.035] py-4 pl-9 pr-4 text-lg outline-none focus:border-emerald-400/40"
                />

              </div>

            </div>


            {/* Product Summary */}

            <div className="mt-6 grid gap-3 sm:grid-cols-3">

              <MiniMetric
                label="Current NAV"
                value={`₹${formatMoney(
                  selectedProduct.nav
                )}`}
              />

              <MiniMetric
                label="Risk"
                value={
                  selectedProduct.risk_level ||
                  "—"
                }
              />

              <MiniMetric
                label="Expense Ratio"
                value={`${selectedProduct.expense_ratio.toFixed(
                  2
                )}%`}
              />

            </div>


            {orderMessage && (

              <div className="mt-5 rounded-[16px] border border-white/[0.08] bg-white/[0.03] px-4 py-3 text-sm text-white/55">
                {orderMessage}
              </div>

            )}


            <button
              onClick={placeOrder}
              disabled={
                placingOrder ||
                Number(amount) <= 0
              }
              className="mt-6 w-full rounded-full bg-emerald-300 px-6 py-3.5 font-medium text-[#04100c] transition hover:bg-emerald-200 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {placingOrder
                ? "Creating Order..."
                : investmentMode ===
                  "SIP"
                ? "Start SIP"
                : "Invest Now"}
            </button>


            <p className="mt-4 text-center text-[11px] leading-5 text-white/20">
              Development flow only. This currently
              creates an internal TopOne order.

              Real KYC, mandate, payment and regulated
              execution will be connected through an
              authorized execution provider.
            </p>

          </div>

        </div>

      )}

    </main>
  );
}


function ProductCard({
  product,
  onInvest,
  onView,
}: {
  product: InvestmentProduct;
  onInvest: () => void;
  onView: () => void;
}) {
  return (
    <div className="group rounded-[22px] border border-white/[0.08] bg-white/[0.025] p-4 transition duration-300 hover:border-emerald-400/20 hover:bg-white/[0.04] sm:rounded-[28px] sm:p-7 md:hover:-translate-y-1">

      <div className="flex items-start justify-between gap-5">

        <div>

          <p className="text-[10px] uppercase tracking-[0.13em] text-emerald-200/60">
            {getMainCategory(product)}
          </p>

          <h2 className="mt-2 text-lg font-medium leading-snug tracking-[-0.03em] sm:mt-3 sm:text-2xl">
            {product.name}
          </h2>

          <p className="mt-2 text-sm text-white/35">
            {product.provider ||
              "Investment Provider"}
          </p>

        </div>


        <div className="rounded-[18px] border border-emerald-400/15 bg-emerald-400/[0.06] px-4 py-3 text-center">

          <p className="text-[10px] uppercase tracking-[0.12em] text-white/25">
            Risk
          </p>

          <p className="mt-1 text-sm font-medium text-emerald-200">
            {product.risk_level ||
              "—"}
          </p>

        </div>

      </div>


      <div className="mt-5 grid grid-cols-2 gap-2 sm:mt-7 sm:grid-cols-4 sm:gap-3">

        <ProductMetric
          label="NAV"
          value={`₹${formatMoney(
            product.nav
          )}`}
        />

        <ProductMetric
          label="1Y Return"
          value={`${(product.return_1y || 0).toFixed(
            1
          )}%`}
        />

        <ProductMetric
          label="Volatility"
          value={`${(product.volatility || 0).toFixed(
            1
          )}%`}
        />

        <ProductMetric
          label="Expense"
          value={`${product.expense_ratio.toFixed(
            2
          )}%`}
        />

      </div>


      <div className="mt-6 rounded-[20px] border border-white/[0.06] bg-black/10 p-5">

        <div className="flex items-center justify-between gap-4">

          <div>

            <p className="text-[10px] uppercase tracking-[0.11em] text-white/23">
              Minimum SIP
            </p>

            <p className="mt-2 text-sm font-medium">
              ₹
              {formatMoney(
                product.minimum_sip
              )}
            </p>

          </div>


          <div className="text-right">

            <p className="text-[10px] uppercase tracking-[0.11em] text-white/23">
              Minimum One-time
            </p>

            <p className="mt-2 text-sm font-medium">
              ₹
              {formatMoney(
                product.minimum_lumpsum
              )}
            </p>

          </div>

        </div>

      </div>


      <div className="mt-7 flex flex-col gap-3 sm:flex-row">

        <button
          onClick={onView}
          className="flex-1 rounded-full border border-white/[0.08] bg-white/[0.035] px-5 py-3 text-sm text-white/65 transition hover:bg-white/[0.06] hover:text-white"
        >
          View Analysis
        </button>

        <button
          onClick={onInvest}
          className="flex-1 rounded-full bg-emerald-300 px-5 py-3 text-sm font-medium text-[#04100c] transition hover:bg-emerald-200"
        >
          Invest
        </button>

      </div>

    </div>
  );
}


function ProductMetric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-[16px] border border-white/[0.06] bg-black/10 p-4">

      <p className="text-[10px] uppercase tracking-[0.1em] text-white/22">
        {label}
      </p>

      <p className="mt-2 text-sm font-medium">
        {value}
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
    <div className="rounded-[16px] border border-white/[0.06] bg-white/[0.025] p-4">

      <p className="text-[10px] uppercase tracking-[0.1em] text-white/23">
        {label}
      </p>

      <p className="mt-2 text-sm font-medium">
        {value}
      </p>

    </div>
  );
}


function formatMoney(
  value: number
) {
  return new Intl.NumberFormat(
    "en-IN",
    {
      maximumFractionDigits: 2,
    }
  ).format(value);
}