"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

type AllocationItem = {
  asset_type: string;
  value: number;
  percentage: number;
};

type PortfolioSummary = {
  total_invested: number;
  current_value: number;
  total_gain: number;
  total_gain_percentage: number;
  number_of_holdings: number;

  mutual_fund_value: number;
  stock_value: number;
  etf_value: number;
  gold_value: number;
  debt_value: number;
  other_value: number;

  asset_allocation: AllocationItem[];
};

type Holding = {
  id: number;
  asset_type: string;
  asset_name: string;
  symbol: string | null;
  isin: string | null;
  provider: string | null;
  folio_number_masked: string | null;
  quantity: number;
  average_buy_price: number;
  invested_amount: number;
  current_price: number;
  current_value: number;
  total_gain: number;
  total_gain_percentage: number;
  asset_class: string | null;
  category: string | null;
  sector: string | null;
  source: string;
  sync_status: string;
};

const assetTypes = [
  "MUTUAL_FUND",
  "STOCK",
  "ETF",
  "GOLD",
  "BOND",
  "PPF",
  "EPF",
  "NPS",
  "OTHER",
];

export default function PortfolioPage() {
  const router = useRouter();

  const [summary, setSummary] =
    useState<PortfolioSummary | null>(null);

  const [holdings, setHoldings] =
    useState<Holding[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [showAdd, setShowAdd] =
    useState(false);

  const [saving, setSaving] =
    useState(false);

  const [message, setMessage] =
    useState("");

  const [theme, setTheme] =
    useState<"dark" | "light">("dark");

  const [assetType, setAssetType] =
    useState("MUTUAL_FUND");

  const [assetName, setAssetName] =
    useState("");

  const [symbol, setSymbol] =
    useState("");

  const [provider, setProvider] =
    useState("");

  const [quantity, setQuantity] =
    useState("");

  const [averageBuyPrice, setAverageBuyPrice] =
    useState("");

  const [investedAmount, setInvestedAmount] =
    useState("");

  const [currentPrice, setCurrentPrice] =
    useState("");

  const [currentValue, setCurrentValue] =
    useState("");

  const [assetClass, setAssetClass] =
    useState("");

  const [category, setCategory] =
    useState("");

  const [sector, setSector] =
    useState("");

  async function loadPortfolio() {
    const token =
      localStorage.getItem("access_token");

    if (!token) {
      router.push("/login");
      return;
    }

    const headers = {
      Authorization: `Bearer ${token}`,
    };

    try {
      const [
        summaryResponse,
        holdingsResponse,
      ] = await Promise.all([
        fetch(
          "/api-backend/portfolio/summary",
          { headers }
        ),

        fetch(
          "/api-backend/portfolio/holdings",
          { headers }
        ),
      ]);

      if (summaryResponse.ok) {
        setSummary(
          await summaryResponse.json()
        );
      }

      if (holdingsResponse.ok) {
        setHoldings(
          await holdingsResponse.json()
        );
      }
    } catch {
      setMessage(
        "Could not connect to portfolio backend."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const saved =
      localStorage.getItem("investigenie-theme");

    const initial =
      saved === "light" ? "light" : "dark";

    setTheme(initial);
    document.documentElement.dataset.theme =
      initial;

    loadPortfolio();
  }, []);

  function toggleTheme() {
    const next =
      theme === "dark" ? "light" : "dark";

    setTheme(next);
    document.documentElement.dataset.theme =
      next;
    localStorage.setItem(
      "investigenie-theme",
      next
    );
  }

  async function addHolding(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    const token =
      localStorage.getItem("access_token");

    if (!token) {
      router.push("/login");
      return;
    }

    setSaving(true);
    setMessage("");

    try {
      const response = await fetch(
        "/api-backend/portfolio/holdings",
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",

            Authorization:
              `Bearer ${token}`,
          },

          body: JSON.stringify({
            asset_type: assetType,
            asset_name: assetName,
            symbol: symbol || null,
            provider: provider || null,
            quantity: Number(quantity || 0),

            average_buy_price:
              Number(
                averageBuyPrice || 0
              ),

            invested_amount:
              Number(investedAmount),

            current_price:
              Number(
                currentPrice || 0
              ),

            current_value:
              Number(currentValue),

            asset_class:
              assetClass || null,

            category:
              category || null,

            sector:
              sector || null,
          }),
        }
      );

      const data =
        await response.json();

      if (!response.ok) {
        setMessage(
          data.detail ||
            "Could not add investment."
        );

        return;
      }

      resetForm();

      setShowAdd(false);

      await loadPortfolio();

      setMessage(
        "Investment added successfully."
      );
    } catch {
      setMessage(
        "Could not connect to backend."
      );
    } finally {
      setSaving(false);
    }
  }

  async function deleteHolding(
    holdingId: number
  ) {
    const token =
      localStorage.getItem("access_token");

    if (!token) {
      router.push("/login");
      return;
    }

    const confirmed =
      window.confirm(
        "Remove this investment?"
      );

    if (!confirmed) {
      return;
    }

    try {
      const response = await fetch(
        `/api-backend/portfolio/holdings/${holdingId}`,
        {
          method: "DELETE",

          headers: {
            Authorization:
              `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        setMessage(
          "Could not remove investment."
        );
        return;
      }

      await loadPortfolio();
    } catch {
      setMessage(
        "Could not connect to backend."
      );
    }
  }

  function resetForm() {
    setAssetType("MUTUAL_FUND");
    setAssetName("");
    setSymbol("");
    setProvider("");
    setQuantity("");
    setAverageBuyPrice("");
    setInvestedAmount("");
    setCurrentPrice("");
    setCurrentValue("");
    setAssetClass("");
    setCategory("");
    setSector("");
  }

  const gainPositive =
    (summary?.total_gain || 0) >= 0;

  const allocationMax = useMemo(() => {
    return Math.max(
      ...(summary?.asset_allocation.map(
        (item) => item.percentage
      ) || [1]),
      1
    );
  }, [summary]);

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[var(--background)] text-[var(--foreground)]">
        <div className="text-center">
          <div className="mx-auto h-9 w-9 animate-spin rounded-full border-2 border-white/10 border-t-emerald-300" />

          <p className="mt-5 text-sm text-white/40">
            Loading your portfolio...
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[var(--background)] text-[var(--foreground)]">

      {/* Ambient background */}

      <div className="pointer-events-none fixed inset-0">

        <div className="absolute left-[20%] top-[-15rem] h-[30rem] w-[30rem] rounded-full bg-emerald-400/[0.06] blur-[120px]" />

        <div className="absolute right-[-10rem] top-[22rem] h-[26rem] w-[26rem] rounded-full bg-cyan-400/[0.04] blur-[120px]" />

      </div>


      {/* Navigation */}

      <nav className="relative z-20 border-b border-white/[0.06] bg-[#05070b]/70 backdrop-blur-2xl">

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
              Investi
              <span className="text-emerald-300">
                Genie
              </span>
            </span>

          </button>


          <div className="flex items-center gap-3">

            <button
              type="button"
              onClick={toggleTheme}
              className="ig-theme-toggle flex h-10 min-w-10 items-center justify-center rounded-full border px-3 text-sm"
              aria-label={
                theme === "dark"
                  ? "Switch to light mode"
                  : "Switch to dark mode"
              }
              title={
                theme === "dark"
                  ? "Switch to light mode"
                  : "Switch to dark mode"
              }
            >
              {theme === "dark" ? "☀" : "☾"}
            </button>

            <button
              onClick={() =>
                router.push("/dashboard")
              }
              className="rounded-full border border-white/[0.08] bg-white/[0.035] px-5 py-2.5 text-sm text-white/55 transition hover:bg-white/[0.06] hover:text-white"
            >
              Dashboard
            </button>

            <button
              onClick={() =>
                setShowAdd(true)
              }
              className="rounded-full bg-emerald-300 px-5 py-2.5 text-sm font-medium text-[#04100c] transition hover:scale-[1.03] hover:bg-emerald-200"
            >
              + Add Investment
            </button>

          </div>

        </div>

      </nav>


      <section className="relative z-10 mx-auto max-w-[1450px] px-6 py-10 lg:px-10">

        {/* Header */}

        <div className="flex flex-col gap-7 lg:flex-row lg:items-end lg:justify-between">

          <div>

            <p className="text-[11px] font-medium tracking-[0.17em] text-emerald-200/70">
              CONNECTED WEALTH
            </p>

            <h1 className="mt-4 text-4xl font-semibold tracking-[-0.045em] sm:text-5xl">
              Your investments,
              <span className="text-white/35">
                {" "}
                finally connected.
              </span>
            </h1>

            <p className="mt-4 max-w-2xl text-sm leading-6 text-white/40">
              Track mutual funds, stocks, ETFs, gold
              and other investments in one financial
              intelligence layer.
            </p>

          </div>


          <div className="flex flex-col gap-3 sm:flex-row">

            <button
              onClick={() =>
                setShowAdd(true)
              }
              className="rounded-full border border-white/[0.08] bg-white/[0.035] px-6 py-3 text-sm text-white/65 transition hover:bg-white/[0.06] hover:text-white"
            >
              Add Manually
            </button>

            <button
              onClick={() =>
                setMessage(
                  "Connected Investments will support consent-based CAS / broker / RTA integrations in the next integration phase."
                )
              }
              className="rounded-full bg-emerald-300 px-6 py-3 text-sm font-medium text-[#04100c] transition hover:-translate-y-0.5 hover:bg-emerald-200"
            >
              Connect Investments
            </button>

          </div>

        </div>


        {message && (
          <div className="mt-6 rounded-2xl border border-white/[0.08] bg-white/[0.03] px-5 py-4 text-sm text-white/55">
            {message}
          </div>
        )}


        {/* Portfolio Hero */}

        <div className="mt-8 overflow-hidden rounded-[30px] border border-white/[0.08] bg-white/[0.025] p-7 sm:p-8">

          <div className="grid gap-8 xl:grid-cols-[1fr_.9fr]">

            <div>

              <p className="text-xs text-white/30">
                Total portfolio value
              </p>

              <p className="mt-3 text-5xl font-semibold tracking-[-0.05em] sm:text-6xl">
                ₹
                {formatMoney(
                  summary?.current_value || 0
                )}
              </p>

              <div className="mt-5 flex flex-wrap items-center gap-4">

                <div>

                  <p className="text-xs text-white/25">
                    Total invested
                  </p>

                  <p className="mt-1 text-lg font-medium">
                    ₹
                    {formatMoney(
                      summary?.total_invested || 0
                    )}
                  </p>

                </div>


                <div className="h-9 w-px bg-white/[0.07]" />


                <div>

                  <p className="text-xs text-white/25">
                    Overall return
                  </p>

                  <p
                    className={`mt-1 text-lg font-medium ${
                      gainPositive
                        ? "text-emerald-300"
                        : "text-red-300"
                    }`}
                  >
                    {gainPositive ? "+" : ""}
                    {(
                      summary?.total_gain_percentage ||
                      0
                    ).toFixed(2)}
                    %
                  </p>

                </div>


                <div className="h-9 w-px bg-white/[0.07]" />


                <div>

                  <p className="text-xs text-white/25">
                    Gain / Loss
                  </p>

                  <p
                    className={`mt-1 text-lg font-medium ${
                      gainPositive
                        ? "text-emerald-300"
                        : "text-red-300"
                    }`}
                  >
                    {gainPositive ? "+" : ""}
                    ₹
                    {formatMoney(
                      summary?.total_gain || 0
                    )}
                  </p>

                </div>

              </div>

            </div>


            <div className="grid gap-3 sm:grid-cols-2">

              <PortfolioMetric
                label="Mutual Funds"
                value={
                  summary?.mutual_fund_value || 0
                }
              />

              <PortfolioMetric
                label="Stocks"
                value={
                  summary?.stock_value || 0
                }
              />

              <PortfolioMetric
                label="ETFs"
                value={
                  summary?.etf_value || 0
                }
              />

              <PortfolioMetric
                label="Gold"
                value={
                  summary?.gold_value || 0
                }
              />

            </div>

          </div>

        </div>


        {/* Allocation + Intelligence */}

        <div className="mt-6 grid gap-5 lg:grid-cols-[1.35fr_.65fr]">

          <div className="rounded-[28px] border border-white/[0.08] bg-white/[0.025] p-7">

            <div className="flex items-end justify-between">

              <div>

                <p className="text-[11px] font-medium tracking-[0.15em] text-white/28">
                  ASSET ALLOCATION
                </p>

                <h2 className="mt-2 text-2xl font-medium">
                  How your wealth is distributed
                </h2>

              </div>

              <p className="text-xs text-white/25">
                {summary?.number_of_holdings || 0} holdings
              </p>

            </div>


            <div className="mt-8 space-y-5">

              {(summary?.asset_allocation || [])
                .length === 0 ? (

                <div className="rounded-[22px] border border-dashed border-white/[0.08] bg-black/10 p-8 text-center">

                  <p className="text-lg font-medium">
                    No investments connected yet
                  </p>

                  <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-white/35">
                    Add a holding manually or connect
                    your investments to activate
                    portfolio intelligence.
                  </p>

                </div>

              ) : (

                summary?.asset_allocation.map(
                  (item) => (

                    <AllocationRow
                      key={item.asset_type}
                      item={item}
                      max={allocationMax}
                    />

                  )
                )

              )}

            </div>

          </div>


          <div className="relative overflow-hidden rounded-[28px] border border-emerald-400/15 bg-gradient-to-b from-emerald-400/[0.07] to-emerald-400/[0.025] p-7">

            <div className="pointer-events-none absolute right-[-3rem] top-[-3rem] h-36 w-36 rounded-full bg-emerald-300/[0.1] blur-3xl" />


            <div className="relative">

              <p className="text-[11px] tracking-[0.15em] text-emerald-200/70">
                PORTFOLIO INTELLIGENCE
              </p>


              <h3 className="mt-5 text-2xl font-medium leading-snug">
                Your portfolio analysis starts here.
              </h3>


              <p className="mt-4 text-sm leading-6 text-white/40">
                As holdings are connected,
                InvestiGenie will analyze
                diversification, concentration,
                goal alignment, risk exposure and
                future suitability.
              </p>


              <div className="mt-7 space-y-3">

                <InsightRow
                  label="Portfolio Sync"
                  value={
                    holdings.length > 0
                      ? "Active"
                      : "Not connected"
                  }
                />

                <InsightRow
                  label="Holdings"
                  value={String(
                    holdings.length
                  )}
                />

                <InsightRow
                  label="AI Analysis"
                  value={
                    holdings.length > 0
                      ? "Ready"
                      : "Waiting"
                  }
                />

              </div>

            </div>

          </div>

        </div>


        {/* Holdings */}

        <div className="mt-6 rounded-[28px] border border-white/[0.08] bg-white/[0.025] p-7">

          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">

            <div>

              <p className="text-[11px] tracking-[0.15em] text-white/28">
                HOLDINGS
              </p>

              <h2 className="mt-2 text-2xl font-medium">
                Your investment universe
              </h2>

            </div>


            <button
              onClick={() =>
                router.push("/invest")
              }
              className="rounded-full border border-emerald-400/15 bg-emerald-400/[0.055] px-5 py-2.5 text-sm text-emerald-200 transition hover:bg-emerald-400/[0.09]"
            >
              Discover Investments →
            </button>

          </div>


          {holdings.length === 0 ? (

            <div className="mt-7 rounded-[24px] border border-dashed border-white/[0.08] bg-black/10 p-10 text-center">

              <p className="text-xl font-medium">
                Your portfolio is empty
              </p>

              <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-white/35">
                Add your existing investments now.
                Later this section will sync directly
                through supported investment providers.
              </p>

              <button
                onClick={() =>
                  setShowAdd(true)
                }
                className="mt-6 rounded-full bg-emerald-300 px-6 py-3 text-sm font-medium text-[#04100c]"
              >
                Add First Investment
              </button>

            </div>

          ) : (

            <div className="mt-7 overflow-x-auto">

              <table className="w-full min-w-[900px]">

                <thead>

                  <tr className="border-b border-white/[0.07] text-left text-[10px] uppercase tracking-[0.13em] text-white/25">

                    <th className="pb-4 font-medium">
                      Investment
                    </th>

                    <th className="pb-4 font-medium">
                      Type
                    </th>

                    <th className="pb-4 font-medium">
                      Invested
                    </th>

                    <th className="pb-4 font-medium">
                      Current Value
                    </th>

                    <th className="pb-4 font-medium">
                      Return
                    </th>

                    <th className="pb-4 font-medium">
                      Source
                    </th>

                    <th className="pb-4 font-medium" />

                  </tr>

                </thead>


                <tbody>

                  {holdings.map(
                    (holding) => (

                      <HoldingRow
                        key={holding.id}
                        holding={holding}
                        onDelete={() =>
                          deleteHolding(
                            holding.id
                          )
                        }
                      />

                    )
                  )}

                </tbody>

              </table>

            </div>

          )}

        </div>

      </section>


      {/* Add Investment Modal */}

      {showAdd && (

        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-xl">

          <div className="max-h-[92vh] w-full max-w-2xl overflow-y-auto rounded-[30px] border border-white/[0.1] bg-[#090c11] p-7 shadow-2xl">

            <div className="flex items-start justify-between">

              <div>

                <p className="text-[11px] tracking-[0.15em] text-emerald-200/70">
                  ADD HOLDING
                </p>

                <h2 className="mt-2 text-2xl font-medium">
                  Add an investment
                </h2>

              </div>


              <button
                onClick={() =>
                  setShowAdd(false)
                }
                className="rounded-full border border-white/[0.08] px-3 py-1.5 text-sm text-white/40 hover:text-white"
              >
                ✕
              </button>

            </div>


            <form
              onSubmit={addHolding}
              className="mt-7 grid gap-5 sm:grid-cols-2"
            >

              <SelectField
                label="Asset Type"
                value={assetType}
                onChange={setAssetType}
                options={assetTypes}
              />

              <FormField
                label="Investment Name"
                value={assetName}
                onChange={setAssetName}
                placeholder="HDFC Index Fund"
                required
              />

              <FormField
                label="Symbol"
                value={symbol}
                onChange={setSymbol}
                placeholder="Optional"
              />

              <FormField
                label="Provider"
                value={provider}
                onChange={setProvider}
                placeholder="HDFC AMC / NSE"
              />

              <NumberField
                label="Quantity / Units"
                value={quantity}
                onChange={setQuantity}
              />

              <NumberField
                label="Average Buy Price"
                value={averageBuyPrice}
                onChange={setAverageBuyPrice}
              />

              <NumberField
                label="Invested Amount"
                value={investedAmount}
                onChange={setInvestedAmount}
                required
              />

              <NumberField
                label="Current Price / NAV"
                value={currentPrice}
                onChange={setCurrentPrice}
              />

              <NumberField
                label="Current Value"
                value={currentValue}
                onChange={setCurrentValue}
                required
              />

              <FormField
                label="Asset Class"
                value={assetClass}
                onChange={setAssetClass}
                placeholder="EQUITY"
              />

              <FormField
                label="Category"
                value={category}
                onChange={setCategory}
                placeholder="Large Cap"
              />

              <FormField
                label="Sector"
                value={sector}
                onChange={setSector}
                placeholder="Optional"
              />


              <div className="sm:col-span-2 flex flex-col gap-3 pt-2 sm:flex-row">

                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 rounded-full bg-emerald-300 px-6 py-3.5 font-medium text-[#04100c] transition hover:bg-emerald-200 disabled:opacity-50"
                >
                  {saving
                    ? "Adding..."
                    : "Add Investment"}
                </button>


                <button
                  type="button"
                  onClick={() =>
                    setShowAdd(false)
                  }
                  className="rounded-full border border-white/[0.08] bg-white/[0.03] px-6 py-3.5 text-sm text-white/60"
                >
                  Cancel
                </button>

              </div>

            </form>

          </div>

        </div>

      )}

    </main>
  );
}


function PortfolioMetric({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-[20px] border border-white/[0.07] bg-black/10 p-5">

      <p className="text-[10px] uppercase tracking-[0.12em] text-white/25">
        {label}
      </p>

      <p className="mt-3 text-xl font-medium">
        ₹{formatMoney(value)}
      </p>

    </div>
  );
}


function AllocationRow({
  item,
  max,
}: {
  item: AllocationItem;
  max: number;
}) {
  return (
    <div>

      <div className="flex items-center justify-between gap-5">

        <div>

          <p className="text-sm font-medium">
            {formatAssetType(
              item.asset_type
            )}
          </p>

          <p className="mt-1 text-xs text-white/28">
            ₹{formatMoney(item.value)}
          </p>

        </div>


        <p className="text-sm font-medium text-emerald-200">
          {item.percentage.toFixed(1)}%
        </p>

      </div>


      <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/[0.07]">

        <div
          className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-emerald-200"
          style={{
            width: `${Math.max(
              (item.percentage /
                max) *
                100,
              2
            )}%`,
          }}
        />

      </div>

    </div>
  );
}


function HoldingRow({
  holding,
  onDelete,
}: {
  holding: Holding;
  onDelete: () => void;
}) {
  const positive =
    holding.total_gain >= 0;

  return (
    <tr className="border-b border-white/[0.055] text-sm">

      <td className="py-5 pr-5">

        <p className="font-medium">
          {holding.asset_name}
        </p>

        <p className="mt-1 text-xs text-white/28">
          {holding.symbol ||
            holding.provider ||
            "Investment"}
        </p>

      </td>


      <td className="py-5 pr-5 text-white/48">
        {formatAssetType(
          holding.asset_type
        )}
      </td>


      <td className="py-5 pr-5">
        ₹
        {formatMoney(
          holding.invested_amount
        )}
      </td>


      <td className="py-5 pr-5 font-medium">
        ₹
        {formatMoney(
          holding.current_value
        )}
      </td>


      <td
        className={`py-5 pr-5 ${
          positive
            ? "text-emerald-300"
            : "text-red-300"
        }`}
      >
        {positive ? "+" : ""}
        {holding.total_gain_percentage.toFixed(
          2
        )}
        %
      </td>


      <td className="py-5 pr-5">

        <span className="rounded-full border border-white/[0.07] bg-white/[0.03] px-3 py-1 text-xs text-white/38">
          {holding.source}
        </span>

      </td>


      <td className="py-5 text-right">

        <button
          onClick={onDelete}
          className="text-xs text-white/25 transition hover:text-red-300"
        >
          Remove
        </button>

      </td>

    </tr>
  );
}


function InsightRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between rounded-[16px] border border-white/[0.06] bg-black/10 px-4 py-3">

      <p className="text-xs text-white/32">
        {label}
      </p>

      <p className="text-sm font-medium text-white/75">
        {value}
      </p>

    </div>
  );
}


function FormField({
  label,
  value,
  onChange,
  placeholder,
  required = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  required?: boolean;
}) {
  return (
    <div>

      <label className="mb-2 block text-xs text-white/40">
        {label}
      </label>

      <input
        type="text"
        value={value}
        required={required}
        onChange={(event) =>
          onChange(
            event.target.value
          )
        }
        placeholder={placeholder}
        className="w-full rounded-xl border border-white/[0.08] bg-white/[0.035] px-4 py-3.5 text-sm outline-none placeholder:text-white/18 focus:border-emerald-400/40"
      />

    </div>
  );
}


function NumberField({
  label,
  value,
  onChange,
  required = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
}) {
  return (
    <div>

      <label className="mb-2 block text-xs text-white/40">
        {label}
      </label>

      <input
        type="number"
        min="0"
        step="0.01"
        value={value}
        required={required}
        placeholder="0"
        onChange={(event) =>
          onChange(
            event.target.value
          )
        }
        className="w-full rounded-xl border border-white/[0.08] bg-white/[0.035] px-4 py-3.5 text-sm outline-none placeholder:text-white/18 focus:border-emerald-400/40"
      />

    </div>
  );
}


function SelectField({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <div>

      <label className="mb-2 block text-xs text-white/40">
        {label}
      </label>

      <select
        value={value}
        onChange={(event) =>
          onChange(
            event.target.value
          )
        }
        className="w-full rounded-xl border border-white/[0.08] bg-[#0b0e13] px-4 py-3.5 text-sm outline-none focus:border-emerald-400/40"
      >

        {options.map(
          (option) => (

            <option
              key={option}
              value={option}
            >
              {formatAssetType(option)}
            </option>

          )
        )}

      </select>

    </div>
  );
}


function formatAssetType(
  value: string
) {
  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(
      /\b\w/g,
      (char) =>
        char.toUpperCase()
    );
}


function formatMoney(
  value: number
) {
  return new Intl.NumberFormat(
    "en-IN",
    {
      maximumFractionDigits: 0,
    }
  ).format(value);
}