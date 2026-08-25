"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type Goal = {
  id: number;
  user_id: number;
  goal_name: string;
  goal_type: string;
  target_amount: number;
  current_amount: number;
  target_date: string;
  monthly_contribution: number;
  priority: number;
  progress_percentage: number;
  required_monthly_investment: number;
  months_remaining: number;
  status: string;
};

const goalTypes = [
  "HOUSE",
  "CAR",
  "RETIREMENT",
  "EDUCATION",
  "WEDDING",
  "TRAVEL",
  "EMERGENCY_FUND",
  "CUSTOM",
];

export default function GoalsPage() {
  const router = useRouter();

  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const [goalName, setGoalName] = useState("");
  const [goalType, setGoalType] = useState("HOUSE");
  const [targetAmount, setTargetAmount] = useState("");
  const [currentAmount, setCurrentAmount] = useState("");
  const [targetDate, setTargetDate] = useState("");
  const [monthlyContribution, setMonthlyContribution] = useState("");
  const [priority, setPriority] = useState("3");

  useEffect(() => {
    loadGoals();
  }, []);

  async function loadGoals() {
    const token = localStorage.getItem("access_token");

    if (!token) {
      router.push("/login");
      return;
    }

    try {
      const response = await fetch(
        "/api-backend/goals",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        setMessage("Could not load goals.");
        return;
      }

      const data = await response.json();
      setGoals(data);
    } catch {
      setMessage("Could not connect to backend.");
    } finally {
      setLoading(false);
    }
  }

  async function createGoal(
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
        "/api-backend/goals",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            goal_name: goalName,
            goal_type: goalType,
            target_amount: Number(targetAmount),
            current_amount: Number(currentAmount || 0),
            target_date: targetDate,
            monthly_contribution: Number(
              monthlyContribution || 0
            ),
            priority: Number(priority),
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        setMessage(
          data.detail || "Could not create goal."
        );
        setSaving(false);
        return;
      }

      setGoals((current) => [...current, data]);

      setGoalName("");
      setGoalType("HOUSE");
      setTargetAmount("");
      setCurrentAmount("");
      setTargetDate("");
      setMonthlyContribution("");
      setPriority("3");

      setMessage("Goal created successfully.");
    } catch {
      setMessage("Could not connect to backend.");
    } finally {
      setSaving(false);
    }
  }

  async function deleteGoal(goalId: number) {
    const token = localStorage.getItem("access_token");

    if (!token) {
      router.push("/login");
      return;
    }

    const confirmed = window.confirm(
      "Delete this financial goal?"
    );

    if (!confirmed) {
      return;
    }

    try {
      const response = await fetch(
        `/api-backend/goals/${goalId}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        setMessage("Could not delete goal.");
        return;
      }

      setGoals((current) =>
        current.filter((goal) => goal.id !== goalId)
      );
    } catch {
      setMessage("Could not connect to backend.");
    }
  }

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#05070b] text-white">
        <p className="text-white/50">
          Loading your financial goals...
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
            className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm text-white/70 transition-all hover:scale-105 hover:bg-white/[0.08]"
          >
            Back to Dashboard
          </button>
        </div>
      </nav>

      <section className="mx-auto max-w-7xl px-6 py-12 lg:px-10">
        <div className="max-w-3xl">
          <p className="text-sm font-medium text-emerald-300">
            GOAL PLANNING
          </p>

          <h1 className="mt-3 text-4xl font-semibold tracking-tight">
            Turn your future into a plan
          </h1>

          <p className="mt-4 text-sm leading-6 text-white/45">
            Define what you want to achieve and InvestiGenie will
            calculate progress, remaining time and the monthly amount
            needed to reach it.
          </p>
        </div>

        <div className="mt-10 grid gap-8 lg:grid-cols-[1fr_1.25fr]">
          <form
            onSubmit={createGoal}
            className="rounded-[28px] border border-white/10 bg-white/[0.03] p-7"
          >
            <h2 className="text-xl font-medium">
              Create a new goal
            </h2>

            <div className="mt-6 space-y-5">
              <Field
                label="Goal name"
                value={goalName}
                onChange={setGoalName}
                placeholder="Buy my first home"
              />

              <div>
                <label className="mb-2 block text-sm text-white/55">
                  Goal type
                </label>

                <select
                  value={goalType}
                  onChange={(e) =>
                    setGoalType(e.target.value)
                  }
                  className="w-full rounded-xl border border-white/10 bg-[#0b0e13] px-4 py-3.5 text-white outline-none focus:border-emerald-400/50"
                >
                  {goalTypes.map((type) => (
                    <option key={type} value={type}>
                      {formatGoalType(type)}
                    </option>
                  ))}
                </select>
              </div>

              <MoneyInput
                label="Target amount"
                value={targetAmount}
                onChange={setTargetAmount}
              />

              <MoneyInput
                label="Already saved"
                value={currentAmount}
                onChange={setCurrentAmount}
              />

              <div>
                <label className="mb-2 block text-sm text-white/55">
                  Target date
                </label>

                <input
                  type="date"
                  value={targetDate}
                  onChange={(e) =>
                    setTargetDate(e.target.value)
                  }
                  required
                  className="w-full rounded-xl border border-white/10 bg-white/[0.035] px-4 py-3.5 outline-none focus:border-emerald-400/50"
                />
              </div>

              <MoneyInput
                label="Current monthly contribution"
                value={monthlyContribution}
                onChange={setMonthlyContribution}
              />

              <div>
                <label className="mb-2 block text-sm text-white/55">
                  Priority
                </label>

                <select
                  value={priority}
                  onChange={(e) =>
                    setPriority(e.target.value)
                  }
                  className="w-full rounded-xl border border-white/10 bg-[#0b0e13] px-4 py-3.5 outline-none focus:border-emerald-400/50"
                >
                  <option value="1">1 — Highest</option>
                  <option value="2">2 — High</option>
                  <option value="3">3 — Medium</option>
                  <option value="4">4 — Low</option>
                  <option value="5">5 — Lowest</option>
                </select>
              </div>
            </div>

            {message && (
              <div className="mt-6 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white/65">
                {message}
              </div>
            )}

            <button
              type="submit"
              disabled={saving}
              className="mt-7 w-full rounded-full bg-emerald-400 py-3.5 font-medium text-black transition-all duration-300 hover:scale-[1.02] hover:bg-emerald-300 active:scale-[0.98] disabled:opacity-50"
            >
              {saving ? "Creating Goal..." : "Create Goal"}
            </button>
          </form>

          <div>
            <div className="flex items-end justify-between">
              <div>
                <p className="text-sm text-white/40">
                  Your goals
                </p>

                <h2 className="mt-1 text-2xl font-medium">
                  {goals.length} active plan
                  {goals.length === 1 ? "" : "s"}
                </h2>
              </div>
            </div>

            {goals.length === 0 ? (
              <div className="mt-6 rounded-[28px] border border-dashed border-white/10 bg-white/[0.02] p-10 text-center">
                <p className="text-lg font-medium">
                  No goals yet
                </p>

                <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-white/40">
                  Create your first financial goal. InvestiGenie will
                  start tracking its progress immediately.
                </p>
              </div>
            ) : (
              <div className="mt-6 space-y-4">
                {goals.map((goal) => (
                  <GoalCard
                    key={goal.id}
                    goal={goal}
                    onDelete={() =>
                      deleteGoal(goal.id)
                    }
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}

function GoalCard({
  goal,
  onDelete,
}: {
  goal: Goal;
  onDelete: () => void;
}) {
  return (
    <div className="rounded-[24px] border border-white/10 bg-white/[0.03] p-6 transition-all duration-300 hover:-translate-y-1 hover:border-emerald-400/20">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-medium text-emerald-300">
            {formatGoalType(goal.goal_type)}
          </p>

          <h3 className="mt-2 text-xl font-medium">
            {goal.goal_name}
          </h3>
        </div>

        <button
          onClick={onDelete}
          className="text-xs text-white/30 transition hover:text-red-300"
        >
          Delete
        </button>
      </div>

      <div className="mt-6 flex items-end justify-between">
        <div>
          <p className="text-xs text-white/35">
            Progress
          </p>

          <p className="mt-1 text-lg font-medium">
            ₹{formatMoney(goal.current_amount)}
            <span className="text-sm text-white/30">
              {" "}
              / ₹{formatMoney(goal.target_amount)}
            </span>
          </p>
        </div>

        <p className="text-lg font-medium text-emerald-300">
          {goal.progress_percentage.toFixed(1)}%
        </p>
      </div>

      <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-emerald-400 transition-all"
          style={{
            width: `${Math.min(
              goal.progress_percentage,
              100
            )}%`,
          }}
        />
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-3">
        <MiniMetric
          label="Months left"
          value={String(goal.months_remaining)}
        />

        <MiniMetric
          label="Required / month"
          value={`₹${formatMoney(
            goal.required_monthly_investment
          )}`}
        />

        <MiniMetric
          label="Current / month"
          value={`₹${formatMoney(
            goal.monthly_contribution
          )}`}
        />
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  return (
    <div>
      <label className="mb-2 block text-sm text-white/55">
        {label}
      </label>

      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required
        className="w-full rounded-xl border border-white/10 bg-white/[0.035] px-4 py-3.5 outline-none placeholder:text-white/20 focus:border-emerald-400/50"
      />
    </div>
  );
}

function MoneyInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div>
      <label className="mb-2 block text-sm text-white/55">
        {label}
      </label>

      <div className="relative">
        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30">
          ₹
        </span>

        <input
          type="number"
          min="0"
          step="0.01"
          value={value}
          placeholder="0"
          onChange={(e) => onChange(e.target.value)}
          required
          className="w-full rounded-xl border border-white/10 bg-white/[0.035] py-3.5 pl-9 pr-4 outline-none placeholder:text-white/20 focus:border-emerald-400/50"
        />
      </div>
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
    <div className="rounded-xl bg-white/[0.035] p-4">
      <p className="text-xs text-white/30">
        {label}
      </p>

      <p className="mt-2 text-sm font-medium">
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

function formatGoalType(type: string) {
  return type
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) =>
      char.toUpperCase()
    );
}