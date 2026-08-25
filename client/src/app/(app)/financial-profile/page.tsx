"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type FinancialProfile = {
  annual_income: number;
  monthly_income: number;
  monthly_expenses: number;
  monthly_debt_payment: number;
  total_savings: number;
  emergency_fund: number;
  total_assets: number;
  total_liabilities: number;
  existing_investments: number;
  insurance_cover: number;

  net_worth?: number;
  savings_rate?: number;
  debt_to_income_ratio?: number;
  emergency_months?: number;
  investment_ratio?: number;
};

const emptyProfile: FinancialProfile = {
  annual_income: 0,
  monthly_income: 0,
  monthly_expenses: 0,
  monthly_debt_payment: 0,
  total_savings: 0,
  emergency_fund: 0,
  total_assets: 0,
  total_liabilities: 0,
  existing_investments: 0,
  insurance_cover: 0,
};

export default function FinancialProfilePage() {
  const router = useRouter();

  const [profile, setProfile] =
    useState<FinancialProfile>(emptyProfile);

  const [existingProfile, setExistingProfile] =
    useState(false);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    async function loadProfile() {
      const token = localStorage.getItem("access_token");

      if (!token) {
        router.push("/login");
        return;
      }

      try {
        const response = await fetch(
          "/api-backend/financial-profile",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (response.status === 404) {
          setExistingProfile(false);
          setLoading(false);
          return;
        }

        if (!response.ok) {
          setMessage("Could not load financial profile.");
          setLoading(false);
          return;
        }

        const data = await response.json();

        setProfile(data);
        setExistingProfile(true);
      } catch {
        setMessage("Could not connect to backend.");
      } finally {
        setLoading(false);
      }
    }

    loadProfile();
  }, [router]);

  function updateField(
    field: keyof FinancialProfile,
    value: string
  ) {
    setProfile((current) => ({
      ...current,
      [field]: Number(value),
    }));
  }

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    const token = localStorage.getItem("access_token");

    if (!token) {
      router.push("/login");
      return;
    }

    setSaving(true);
    setMessage("");

    try {
      const response = await fetch(
        "/api-backend/financial-profile",
        {
          method: existingProfile ? "PUT" : "POST",

          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },

          body: JSON.stringify({
            annual_income: profile.annual_income,
            monthly_income: profile.monthly_income,
            monthly_expenses: profile.monthly_expenses,
            monthly_debt_payment:
              profile.monthly_debt_payment,
            total_savings: profile.total_savings,
            emergency_fund: profile.emergency_fund,
            total_assets: profile.total_assets,
            total_liabilities:
              profile.total_liabilities,
            existing_investments:
              profile.existing_investments,
            insurance_cover: profile.insurance_cover,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        setMessage(
          data.detail || "Could not save profile."
        );
        setSaving(false);
        return;
      }

      setProfile(data);
      setExistingProfile(true);

      setMessage(
        existingProfile
          ? "Financial profile updated successfully."
          : "Financial profile created successfully."
      );
    } catch {
      setMessage("Could not connect to backend.");
    }

    setSaving(false);
  }

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#05070b] text-white">
        <p className="text-white/50">
          Loading financial profile...
        </p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#05070b] text-white">
      <nav className="border-b border-white/10">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5 lg:px-10">
          <button
            onClick={() => router.push("/dashboard")}
            className="text-xl font-semibold tracking-tight"
          >
            Investi
            <span className="text-emerald-400">
              Genie
            </span>
          </button>

          <button
            onClick={() => router.push("/dashboard")}
            className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm text-white/70 transition hover:bg-white/[0.08] hover:text-white"
          >
            Back to Dashboard
          </button>
        </div>
      </nav>

      <section className="mx-auto max-w-6xl px-6 py-12 lg:px-10">
        <div className="max-w-3xl">
          <p className="text-sm font-medium text-emerald-300">
            FINANCIAL IDENTITY
          </p>

          <h1 className="mt-3 text-4xl font-semibold tracking-tight">
            Build your financial profile
          </h1>

          <p className="mt-4 text-sm leading-6 text-white/45">
            These values help InvestiGenie calculate your
            financial health, risk capacity, Wealth DNA and
            future simulations.
          </p>
        </div>

        {existingProfile && (
          <div className="mt-8 grid gap-4 md:grid-cols-5">
            <MetricCard
              label="Net Worth"
              value={`₹${formatMoney(
                profile.net_worth || 0
              )}`}
            />

            <MetricCard
              label="Savings Rate"
              value={`${(
                profile.savings_rate || 0
              ).toFixed(1)}%`}
            />

            <MetricCard
              label="Debt / Income"
              value={`${(
                profile.debt_to_income_ratio || 0
              ).toFixed(1)}%`}
            />

            <MetricCard
              label="Emergency Cover"
              value={`${(
                profile.emergency_months || 0
              ).toFixed(1)} mo`}
            />

            <MetricCard
              label="Investment Ratio"
              value={`${(
                profile.investment_ratio || 0
              ).toFixed(1)}%`}
            />
          </div>
        )}

        <form
          onSubmit={handleSubmit}
          className="mt-8 rounded-[28px] border border-white/10 bg-white/[0.03] p-7 sm:p-8"
        >
          <div className="grid gap-6 md:grid-cols-2">

            <MoneyField
              label="Annual Income"
              value={profile.annual_income}
              onChange={(value) =>
                updateField("annual_income", value)
              }
            />

            <MoneyField
              label="Monthly Income"
              value={profile.monthly_income}
              onChange={(value) =>
                updateField("monthly_income", value)
              }
            />

            <MoneyField
              label="Monthly Expenses"
              value={profile.monthly_expenses}
              onChange={(value) =>
                updateField("monthly_expenses", value)
              }
            />

            <MoneyField
              label="Monthly Debt / EMI"
              value={profile.monthly_debt_payment}
              onChange={(value) =>
                updateField(
                  "monthly_debt_payment",
                  value
                )
              }
            />

            <MoneyField
              label="Total Savings"
              value={profile.total_savings}
              onChange={(value) =>
                updateField("total_savings", value)
              }
            />

            <MoneyField
              label="Emergency Fund"
              value={profile.emergency_fund}
              onChange={(value) =>
                updateField("emergency_fund", value)
              }
            />

            <MoneyField
              label="Total Assets"
              value={profile.total_assets}
              onChange={(value) =>
                updateField("total_assets", value)
              }
            />

            <MoneyField
              label="Total Liabilities"
              value={profile.total_liabilities}
              onChange={(value) =>
                updateField(
                  "total_liabilities",
                  value
                )
              }
            />

            <MoneyField
              label="Existing Investments"
              value={profile.existing_investments}
              onChange={(value) =>
                updateField(
                  "existing_investments",
                  value
                )
              }
            />

            <MoneyField
              label="Insurance Cover"
              value={profile.insurance_cover}
              onChange={(value) =>
                updateField("insurance_cover", value)
              }
            />

          </div>

          {message && (
            <div className="mt-6 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white/70">
              {message}
            </div>
          )}

          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-xs leading-5 text-white/30">
              InvestiGenie calculates derived metrics
              automatically. You cannot manually edit them.
            </p>

            <button
              type="submit"
              disabled={saving}
              className="rounded-full bg-emerald-400 px-7 py-3 font-medium text-black transition-all duration-300 hover:scale-105 hover:bg-emerald-300 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {saving
                ? "Saving..."
                : existingProfile
                ? "Update Financial Profile"
                : "Save Financial Profile"}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}


function MoneyField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (value: string) => void;
}) {
  return (
    <div>
      <label className="mb-2 block text-sm font-medium text-white/70">
        {label}
      </label>

      <div className="relative">
        <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-white/35">
          ₹
        </span>

        <input
          type="number"
          min="0"
          step="0.01"
          value={value === 0 ? "" : value}
          placeholder="0"
          onChange={(event) => onChange(event.target.value)}
          required
          className="
            w-full
            rounded-xl
            border
            border-white/10
            bg-white/[0.035]
            py-3.5
            pl-10
            pr-4
            text-white
            placeholder:text-white/25
            outline-none
            transition-all
            duration-300
            focus:border-emerald-400/50
            focus:bg-white/[0.05]
            focus:ring-2
            focus:ring-emerald-400/20
          "
        />
      </div>
    </div>
  );
}


function MetricCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
      <p className="text-xs text-white/35">
        {label}
      </p>

      <p className="mt-2 text-lg font-medium">
        {value}
      </p>
    </div>
  );
}


function formatMoney(value: number) {
  return new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 0,
  }).format(value);
}