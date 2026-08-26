"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

const API_BASE = "/api-backend";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const [message, setMessage] = useState("");
  const [messageType, setMessageType] =
    useState<"error" | "success" | "">("");

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (loading) {
      return;
    }

    setLoading(true);
    setMessage("");
    setMessageType("");

    try {
      const response = await fetch(
        `${API_BASE}/auth/login`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: email.trim(),
            password,
          }),
        }
      );

      let data: {
        access_token?: string;
        token_type?: string;
        detail?: string;
      } = {};

      try {
        data = await response.json();
      } catch {
        // Keep a clean user-facing error if the server
        // returns an empty/non-JSON response.
      }

      if (!response.ok) {
        setMessageType("error");
        setMessage(
          data.detail || "Invalid email or password."
        );
        return;
      }

      if (!data.access_token) {
        setMessageType("error");
        setMessage(
          "Login response did not include an access token."
        );
        return;
      }

      localStorage.setItem(
        "access_token",
        data.access_token
      );

      localStorage.setItem(
        "token_type",
        data.token_type || "bearer"
      );

      setMessageType("success");
      setMessage("Login successful.");

      router.replace("/dashboard");
    } catch {
      setMessageType("error");
      setMessage(
        "Unable to reach TopOne. Make sure the app server is running and try again."

      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#05070b] text-white">
      <AmbientBackground />

      {/* =====================================================
          MOBILE LOGIN
      ====================================================== */}

      <section className="relative z-10 flex min-h-screen flex-col lg:hidden">
        <div
          className="px-5 pt-5"
          style={{
            paddingTop:
              "max(1.25rem, env(safe-area-inset-top))",
          }}
        >
          <Link
            href="/"
            className="inline-flex min-h-11 items-center gap-2 rounded-xl px-1 text-sm text-white/45 transition active:scale-[0.98]"
          >
            <ArrowLeft size={17} />
            Back
          </Link>
        </div>

        <div className="flex flex-1 flex-col justify-center px-5 pb-8 pt-6">
          <div className="mx-auto w-full max-w-md">
            <BrandMark compact />

            <div className="mt-8">
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/15 bg-emerald-400/[0.055] px-3 py-2 text-[10px] font-medium tracking-[0.14em] text-emerald-200/80">
                <Sparkles size={13} />
                YOUR FINANCIAL INTELLIGENCE
              </div>

              <h1 className="mt-5 text-[2.55rem] font-semibold leading-[1.02] tracking-[-0.055em]">
                Welcome
                <br />
                <span className="text-white/35">
                  back.
                </span>
              </h1>

              <p className="mt-4 max-w-sm text-sm leading-6 text-white/38">
                Sign in to view your wealth, goals,
                portfolio and financial intelligence.
              </p>
            </div>

            <form
              onSubmit={handleSubmit}
              className="mt-8 space-y-4"
            >
              <Field
                label="Email"
                icon={Mail}
              >
                <input
                  type="email"
                  autoComplete="email"
                  inputMode="email"
                  value={email}
                  onChange={(event) =>
                    setEmail(event.target.value)
                  }
                  placeholder="you@example.com"
                  required
                  className="h-14 w-full bg-transparent pr-4 text-base text-white outline-none placeholder:text-white/18"
                />
              </Field>

              <div>
                <div className="mb-2 flex items-center justify-between">
                  <label className="text-xs font-medium text-white/45">
                    Password
                  </label>

                  <button
                    type="button"
                    className="min-h-9 px-1 text-xs text-emerald-300/80 transition active:scale-[0.98]"
                  >
                    Forgot password?
                  </button>
                </div>

                <div className="flex min-h-14 items-center rounded-2xl border border-white/[0.085] bg-white/[0.035] transition focus-within:border-emerald-400/35 focus-within:bg-white/[0.05]">
                  <div className="flex w-12 shrink-0 items-center justify-center text-white/30">
                    <LockKeyhole size={18} />
                  </div>

                  <input
                    type={
                      showPassword ? "text" : "password"
                    }
                    autoComplete="current-password"
                    value={password}
                    onChange={(event) =>
                      setPassword(event.target.value)
                    }
                    placeholder="Enter your password"
                    required
                    className="h-14 min-w-0 flex-1 bg-transparent text-base text-white outline-none placeholder:text-white/18"
                  />

                  <button
                    type="button"
                    onClick={() =>
                      setShowPassword((current) => !current)
                    }
                    aria-label={
                      showPassword
                        ? "Hide password"
                        : "Show password"
                    }
                    className="flex h-12 w-12 shrink-0 items-center justify-center text-white/30 transition active:scale-95"
                  >
                    {showPassword ? (
                      <EyeOff size={18} />
                    ) : (
                      <Eye size={18} />
                    )}
                  </button>
                </div>
              </div>

              {message && (
                <StatusMessage
                  type={messageType}
                  message={message}
                />
              )}

              <button
                type="submit"
                disabled={loading}
                className="group flex min-h-14 w-full items-center justify-center gap-2 rounded-2xl bg-emerald-300 px-5 text-sm font-semibold text-[#04100c] shadow-[0_14px_45px_rgba(16,185,129,.13)] transition active:scale-[0.985] disabled:cursor-not-allowed disabled:opacity-55"
              >
                {loading ? (
                  <>
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-[#04100c]/20 border-t-[#04100c]" />
                    Signing in...
                  </>
                ) : (
                  <>
                    Sign in
                    <ArrowRight
                      size={16}
                      className="transition group-active:translate-x-0.5"
                    />
                  </>
                )}
              </button>
            </form>

            <div className="mt-6 flex items-center gap-2 rounded-2xl border border-white/[0.055] bg-white/[0.02] px-4 py-3">
              <ShieldCheck
                size={17}
                className="shrink-0 text-emerald-300/70"
              />
              <p className="text-[11px] leading-5 text-white/28">
                Your financial data is protected and used
                only for your TopOne experience.
              </p>
            </div>

            <p className="mt-7 text-center text-sm text-white/35">
              New to TopOne?{" "}
              <Link
                href="/register"
                className="font-medium text-emerald-300"
              >
                Create account
              </Link>
            </p>
          </div>
        </div>
      </section>

      {/* =====================================================
          DESKTOP / LAPTOP LOGIN
      ====================================================== */}

      <section className="relative z-10 hidden min-h-screen lg:grid lg:grid-cols-[1.05fr_.95fr]">
        <div className="relative flex min-h-screen flex-col border-r border-white/[0.055] px-10 py-9 xl:px-14 2xl:px-20">
          <div className="flex items-center justify-between">
            <BrandMark />

            <Link
              href="/"
              className="inline-flex items-center gap-2 rounded-full border border-white/[0.07] bg-white/[0.025] px-4 py-2.5 text-sm text-white/45 transition hover:border-white/[0.12] hover:bg-white/[0.04] hover:text-white/75"
            >
              <ArrowLeft size={15} />
              Back home
            </Link>
          </div>

          <div className="my-auto max-w-2xl py-16">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/15 bg-emerald-400/[0.055] px-4 py-2 text-[10px] font-medium tracking-[0.16em] text-emerald-200/80">
              <Sparkles size={13} />
              AI-NATIVE WEALTH OPERATING SYSTEM
            </div>

            <h1 className="mt-7 text-6xl font-semibold leading-[0.98] tracking-[-0.06em] xl:text-7xl">
              Your financial life,
              <br />
              <span className="bg-gradient-to-r from-emerald-200 via-teal-200 to-cyan-200 bg-clip-text text-transparent">
                connected.
              </span>
            </h1>

            <p className="mt-7 max-w-xl text-base leading-7 text-white/38 xl:text-lg">
              One secure workspace for your portfolio,
              goals, risk profile, Wealth DNA and
              forward-looking financial intelligence.
            </p>

            <div className="mt-10 grid max-w-xl grid-cols-3 gap-3">
              <FeatureTile
                value="1"
                label="Financial identity"
              />
              <FeatureTile
                value="24/7"
                label="Intelligence layer"
              />
              <FeatureTile
                value="You"
                label="In control"
              />
            </div>
          </div>

          <p className="text-xs text-white/18">
            TopOne · Private financial intelligence
          </p>

        </div>

        <div className="flex min-h-screen items-center justify-center px-8 py-12 xl:px-14">
          <div className="w-full max-w-[480px]">
            <p className="text-[10px] font-medium tracking-[0.16em] text-emerald-200/65">
              SECURE SIGN IN
            </p>

            <h2 className="mt-4 text-4xl font-semibold tracking-[-0.045em]">
              Welcome back.
            </h2>

            <p className="mt-3 text-sm leading-6 text-white/35">
              Continue to your private financial
              workspace.
            </p>

            <form
              onSubmit={handleSubmit}
              className="mt-8 space-y-5"
            >
              <Field
                label="Email"
                icon={Mail}
              >
                <input
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(event) =>
                    setEmail(event.target.value)
                  }
                  placeholder="you@example.com"
                  required
                  className="h-14 w-full bg-transparent pr-4 text-base text-white outline-none placeholder:text-white/18"
                />
              </Field>

              <div>
                <div className="mb-2 flex items-center justify-between">
                  <label className="text-xs font-medium text-white/45">
                    Password
                  </label>

                  <button
                    type="button"
                    className="text-xs text-emerald-300/75 transition hover:text-emerald-200"
                  >
                    Forgot password?
                  </button>
                </div>

                <div className="flex min-h-14 items-center rounded-2xl border border-white/[0.085] bg-white/[0.035] transition focus-within:border-emerald-400/35 focus-within:bg-white/[0.05]">
                  <div className="flex w-12 shrink-0 items-center justify-center text-white/30">
                    <LockKeyhole size={18} />
                  </div>

                  <input
                    type={
                      showPassword ? "text" : "password"
                    }
                    autoComplete="current-password"
                    value={password}
                    onChange={(event) =>
                      setPassword(event.target.value)
                    }
                    placeholder="Enter your password"
                    required
                    className="h-14 min-w-0 flex-1 bg-transparent text-base text-white outline-none placeholder:text-white/18"
                  />

                  <button
                    type="button"
                    onClick={() =>
                      setShowPassword((current) => !current)
                    }
                    aria-label={
                      showPassword
                        ? "Hide password"
                        : "Show password"
                    }
                    className="flex h-12 w-12 shrink-0 items-center justify-center text-white/30 transition hover:text-white/55"
                  >
                    {showPassword ? (
                      <EyeOff size={18} />
                    ) : (
                      <Eye size={18} />
                    )}
                  </button>
                </div>
              </div>

              {message && (
                <StatusMessage
                  type={messageType}
                  message={message}
                />
              )}

              <button
                type="submit"
                disabled={loading}
                className="group flex min-h-14 w-full items-center justify-center gap-2 rounded-2xl bg-emerald-300 px-5 text-sm font-semibold text-[#04100c] shadow-[0_18px_55px_rgba(16,185,129,.13)] transition hover:-translate-y-0.5 hover:bg-emerald-200 active:translate-y-0 disabled:cursor-not-allowed disabled:opacity-55"
              >
                {loading ? (
                  <>
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-[#04100c]/20 border-t-[#04100c]" />
                    Signing in...
                  </>
                ) : (
                  <>
                    Sign in
                    <ArrowRight
                      size={16}
                      className="transition group-hover:translate-x-1"
                    />
                  </>
                )}
              </button>
            </form>

            <div className="mt-6 flex items-start gap-3 rounded-2xl border border-white/[0.06] bg-white/[0.02] px-4 py-4">
              <ShieldCheck
                size={18}
                className="mt-0.5 shrink-0 text-emerald-300/70"
              />
              <div>
                <p className="text-xs font-medium text-white/55">
                  Private by design
                </p>
                <p className="mt-1 text-xs leading-5 text-white/25">
                  Sensitive financial information should
                  never be exposed in browser logs or
                  shared without your consent.
                </p>
              </div>
            </div>

            <p className="mt-8 text-center text-sm text-white/35">
              New to TopOne?{" "}
              <Link

                href="/register"
                className="font-medium text-emerald-300 transition hover:text-emerald-200"
              >
                Create account
              </Link>
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}

function AmbientBackground() {
  return (
    <div className="pointer-events-none fixed inset-0">
      <div className="absolute left-[12%] top-[-12rem] h-[28rem] w-[28rem] rounded-full bg-emerald-400/[0.065] blur-[120px]" />
      <div className="absolute right-[-8rem] top-[24%] h-[26rem] w-[26rem] rounded-full bg-cyan-400/[0.04] blur-[120px]" />
      <div className="absolute bottom-[-12rem] left-[25%] h-[28rem] w-[28rem] rounded-full bg-teal-400/[0.035] blur-[120px]" />

      <div
        className="absolute inset-0 opacity-[0.08]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px)",
          backgroundSize: "70px 70px",
          maskImage:
            "linear-gradient(to bottom, black, transparent 90%)",
        }}
      />
    </div>
  );
}

function BrandMark({
  compact = false,
}: {
  compact?: boolean;
}) {
  return (
    <Link
      href="/"
      className="inline-flex w-fit items-center gap-3"
    >
      <div
        className={`flex items-center justify-center rounded-2xl border border-emerald-400/20 bg-emerald-400/[0.07] ${
          compact
            ? "h-10 w-10"
            : "h-11 w-11"
        }`}
      >
        <div className="h-3 w-3 rounded-full bg-emerald-300 shadow-[0_0_18px_rgba(110,231,183,.75)]" />
      </div>

      <span
        className={`font-semibold tracking-[-0.045em] ${
          compact ? "text-xl" : "text-2xl"
        }`}
      >
        <span className="text-emerald-300">Top</span>One
      </span>
    </Link>
  );
}

function Field({
  label,
  icon: Icon,
  children,
}: {
  label: string;
  icon: typeof Mail;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="mb-2 block text-xs font-medium text-white/45">
        {label}
      </label>

      <div className="flex min-h-14 items-center rounded-2xl border border-white/[0.085] bg-white/[0.035] transition focus-within:border-emerald-400/35 focus-within:bg-white/[0.05]">
        <div className="flex w-12 shrink-0 items-center justify-center text-white/30">
          <Icon size={18} />
        </div>

        <div className="min-w-0 flex-1">
          {children}
        </div>
      </div>
    </div>
  );
}

function StatusMessage({
  type,
  message,
}: {
  type: "error" | "success" | "";
  message: string;
}) {
  const success = type === "success";

  return (
    <div
      role="status"
      className={`rounded-2xl border px-4 py-3 text-sm leading-5 ${
        success
          ? "border-emerald-400/15 bg-emerald-400/[0.055] text-emerald-100/80"
          : "border-red-400/15 bg-red-400/[0.05] text-red-200/80"
      }`}
    >
      {message}
    </div>
  );
}

function FeatureTile({
  value,
  label,
}: {
  value: string;
  label: string;
}) {
  return (
    <div className="rounded-[20px] border border-white/[0.06] bg-white/[0.025] p-4">
      <p className="text-xl font-semibold tracking-[-0.03em] text-emerald-200">
        {value}
      </p>
      <p className="mt-1 text-[11px] text-white/25">
        {label}
      </p>
    </div>
  );
}