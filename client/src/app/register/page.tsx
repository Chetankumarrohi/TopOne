"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  ShieldCheck,
  Sparkles,
  UserRound,
} from "lucide-react";

const API_BASE = "/api-backend";

export default function RegisterPage() {
  const router = useRouter();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] =
    useState("");

  const [showPassword, setShowPassword] =
    useState(false);
  const [showConfirmPassword, setShowConfirmPassword] =
    useState(false);

  const [acceptedTerms, setAcceptedTerms] =
    useState(false);

  const [loading, setLoading] = useState(false);

  const [message, setMessage] = useState("");
  const [messageType, setMessageType] =
    useState<"error" | "success" | "">("");

  const passwordChecks = useMemo(
    () => ({
      length: password.length >= 8,
      upper: /[A-Z]/.test(password),
      lower: /[a-z]/.test(password),
      number: /\d/.test(password),
    }),
    [password]
  );

  const passwordStrength = useMemo(() => {
    return Object.values(passwordChecks).filter(Boolean)
      .length;
  }, [passwordChecks]);

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (loading) {
      return;
    }

    setMessage("");
    setMessageType("");

    if (!fullName.trim()) {
      setMessageType("error");
      setMessage("Please enter your full name.");
      return;
    }

    if (!email.trim()) {
      setMessageType("error");
      setMessage("Please enter your email address.");
      return;
    }

    if (password.length < 8) {
      setMessageType("error");
      setMessage(
        "Password must be at least 8 characters long."
      );
      return;
    }

    if (password !== confirmPassword) {
      setMessageType("error");
      setMessage("Passwords do not match.");
      return;
    }

    if (!acceptedTerms) {
      setMessageType("error");
      setMessage(
        "Please accept the Terms and Privacy Policy to continue."
      );
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(
        `${API_BASE}/auth/register`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            full_name: fullName.trim(),
            email: email.trim().toLowerCase(),
            password,
          }),
        }
      );

      let data: {
        detail?: string;
      } = {};

      try {
        data = await response.json();
      } catch {
        // Keep a clean message if backend returns
        // an empty/non-JSON response.
      }

      if (!response.ok) {
        setMessageType("error");
        setMessage(
          data.detail || "Registration failed."
        );
        return;
      }

      setMessageType("success");
      setMessage(
        "Account created successfully. Redirecting to sign in..."
      );

      setFullName("");
      setEmail("");
      setPassword("");
      setConfirmPassword("");
      setAcceptedTerms(false);

      window.setTimeout(() => {
        router.replace("/login");
      }, 900);
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
          MOBILE REGISTER
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

        <div className="flex flex-1 flex-col px-5 pb-10 pt-5">
          <div className="mx-auto w-full max-w-md">
            <BrandMark compact />

            <div className="mt-7">
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/15 bg-emerald-400/[0.055] px-3 py-2 text-[10px] font-medium tracking-[0.14em] text-emerald-200/80">
                <Sparkles size={13} />
                BUILD YOUR WEALTH IDENTITY
              </div>

              <h1 className="mt-5 text-[2.35rem] font-semibold leading-[1.03] tracking-[-0.055em]">
                Start your
                <br />
                <span className="text-white/35">
                  financial journey.
                </span>
              </h1>

              <p className="mt-4 max-w-sm text-sm leading-6 text-white/38">
                Create your private TopOne account
                and start building your financial profile,
                risk identity and Wealth DNA.
              </p>
            </div>

            <form
              onSubmit={handleSubmit}
              className="mt-8 space-y-4"
            >
              <Field
                label="Full name"
                icon={UserRound}
              >
                <input
                  type="text"
                  autoComplete="name"
                  value={fullName}
                  onChange={(event) =>
                    setFullName(event.target.value)
                  }
                  placeholder="Your full name"
                  required
                  className="h-14 w-full bg-transparent pr-4 text-base text-white outline-none placeholder:text-white/18"
                />
              </Field>

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

              <PasswordField
                label="Password"
                value={password}
                onChange={setPassword}
                show={showPassword}
                onToggle={() =>
                  setShowPassword((current) => !current)
                }
                autoComplete="new-password"
                placeholder="Create a secure password"
              />

              {password.length > 0 && (
                <PasswordStrength
                  score={passwordStrength}
                  checks={passwordChecks}
                />
              )}

              <PasswordField
                label="Confirm password"
                value={confirmPassword}
                onChange={setConfirmPassword}
                show={showConfirmPassword}
                onToggle={() =>
                  setShowConfirmPassword(
                    (current) => !current
                  )
                }
                autoComplete="new-password"
                placeholder="Re-enter your password"
              />

              <ConsentBox
                checked={acceptedTerms}
                onChange={setAcceptedTerms}
              />

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
                    Creating account...
                  </>
                ) : (
                  <>
                    Create account
                    <ArrowRight
                      size={16}
                      className="transition group-active:translate-x-0.5"
                    />
                  </>
                )}
              </button>
            </form>

            <div className="mt-6 flex items-start gap-3 rounded-2xl border border-white/[0.055] bg-white/[0.02] px-4 py-3.5">
              <ShieldCheck
                size={17}
                className="mt-0.5 shrink-0 text-emerald-300/70"
              />
              <p className="text-[11px] leading-5 text-white/28">
                Your financial information stays tied to
                your account and should only be used with
                your permission.
              </p>
            </div>

            <p className="mt-7 text-center text-sm text-white/35">
              Already have an account?{" "}
              <Link
                href="/login"
                className="font-medium text-emerald-300"
              >
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </section>

      {/* =====================================================
          DESKTOP / LAPTOP REGISTER
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
              YOUR PRIVATE WEALTH WORKSPACE
            </div>

            <h1 className="mt-7 text-6xl font-semibold leading-[0.98] tracking-[-0.06em] xl:text-7xl">
              Build your
              <br />
              <span className="bg-gradient-to-r from-emerald-200 via-teal-200 to-cyan-200 bg-clip-text text-transparent">
                financial identity.
              </span>
            </h1>

            <p className="mt-7 max-w-xl text-base leading-7 text-white/38 xl:text-lg">
              Connect your financial profile, risk,
              goals and investments into one intelligent
              workspace built around you.
            </p>

            <div className="mt-10 grid max-w-xl grid-cols-3 gap-3">
              <FeatureTile
                value="1"
                label="Secure account"
              />
              <FeatureTile
                value="360°"
                label="Financial view"
              />
              <FeatureTile
                value="You"
                label="Own the data"
              />
            </div>
          </div>

          <p className="text-xs text-white/18">
            TopOne · Private financial intelligence
          </p>

        </div>

        <div className="flex min-h-screen items-center justify-center px-8 py-12 xl:px-14">
          <div className="w-full max-w-[500px]">
            <p className="text-[10px] font-medium tracking-[0.16em] text-emerald-200/65">
              CREATE YOUR ACCOUNT
            </p>

            <h2 className="mt-4 text-4xl font-semibold tracking-[-0.045em]">
              Start with your identity.
            </h2>

            <p className="mt-3 text-sm leading-6 text-white/35">
              Your financial intelligence starts with a
              secure account.
            </p>

            <form
              onSubmit={handleSubmit}
              className="mt-8 space-y-5"
            >
              <Field
                label="Full name"
                icon={UserRound}
              >
                <input
                  type="text"
                  autoComplete="name"
                  value={fullName}
                  onChange={(event) =>
                    setFullName(event.target.value)
                  }
                  placeholder="Your full name"
                  required
                  className="h-14 w-full bg-transparent pr-4 text-base text-white outline-none placeholder:text-white/18"
                />
              </Field>

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

              <PasswordField
                label="Password"
                value={password}
                onChange={setPassword}
                show={showPassword}
                onToggle={() =>
                  setShowPassword((current) => !current)
                }
                autoComplete="new-password"
                placeholder="Create a secure password"
              />

              {password.length > 0 && (
                <PasswordStrength
                  score={passwordStrength}
                  checks={passwordChecks}
                />
              )}

              <PasswordField
                label="Confirm password"
                value={confirmPassword}
                onChange={setConfirmPassword}
                show={showConfirmPassword}
                onToggle={() =>
                  setShowConfirmPassword(
                    (current) => !current
                  )
                }
                autoComplete="new-password"
                placeholder="Re-enter your password"
              />

              <ConsentBox
                checked={acceptedTerms}
                onChange={setAcceptedTerms}
              />

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
                    Creating account...
                  </>
                ) : (
                  <>
                    Create account
                    <ArrowRight
                      size={16}
                      className="transition group-hover:translate-x-1"
                    />
                  </>
                )}
              </button>
            </form>

            <p className="mt-8 text-center text-sm text-white/35">
              Already have an account?{" "}
              <Link
                href="/login"
                className="font-medium text-emerald-300 transition hover:text-emerald-200"
              >
                Sign in
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

function PasswordField({
  label,
  value,
  onChange,
  show,
  onToggle,
  autoComplete,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  show: boolean;
  onToggle: () => void;
  autoComplete: string;
  placeholder: string;
}) {
  return (
    <div>
      <label className="mb-2 block text-xs font-medium text-white/45">
        {label}
      </label>

      <div className="flex min-h-14 items-center rounded-2xl border border-white/[0.085] bg-white/[0.035] transition focus-within:border-emerald-400/35 focus-within:bg-white/[0.05]">
        <div className="flex w-12 shrink-0 items-center justify-center text-white/30">
          <LockKeyhole size={18} />
        </div>

        <input
          type={show ? "text" : "password"}
          autoComplete={autoComplete}
          value={value}
          onChange={(event) =>
            onChange(event.target.value)
          }
          placeholder={placeholder}
          required
          minLength={8}
          className="h-14 min-w-0 flex-1 bg-transparent text-base text-white outline-none placeholder:text-white/18"
        />

        <button
          type="button"
          onClick={onToggle}
          aria-label={
            show ? "Hide password" : "Show password"
          }
          className="flex h-12 w-12 shrink-0 items-center justify-center text-white/30 transition hover:text-white/55 active:scale-95"
        >
          {show ? (
            <EyeOff size={18} />
          ) : (
            <Eye size={18} />
          )}
        </button>
      </div>
    </div>
  );
}

function PasswordStrength({
  score,
  checks,
}: {
  score: number;
  checks: {
    length: boolean;
    upper: boolean;
    lower: boolean;
    number: boolean;
  };
}) {
  const label =
    score <= 1
      ? "Weak"
      : score === 2
        ? "Fair"
        : score === 3
          ? "Good"
          : "Strong";

  return (
    <div className="rounded-2xl border border-white/[0.055] bg-white/[0.02] p-3.5">
      <div className="flex items-center justify-between">
        <p className="text-[10px] uppercase tracking-[0.12em] text-white/25">
          Password strength
        </p>
        <p className="text-xs font-medium text-emerald-200/80">
          {label}
        </p>
      </div>

      <div className="mt-3 grid grid-cols-4 gap-1.5">
        {Array.from({ length: 4 }).map((_, index) => (
          <div
            key={index}
            className={`h-1 rounded-full ${
              index < score
                ? "bg-emerald-300"
                : "bg-white/[0.07]"
            }`}
          />
        ))}
      </div>

      <p className="mt-3 text-[10px] leading-5 text-white/25">
        Use 8+ characters with uppercase, lowercase
        and a number.
      </p>
    </div>
  );
}

function ConsentBox({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex cursor-pointer items-start gap-3 rounded-2xl border border-white/[0.055] bg-white/[0.02] p-3.5">
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) =>
          onChange(event.target.checked)
        }
        className="mt-1 h-4 w-4 shrink-0 accent-emerald-300"
      />

      <span className="text-[11px] leading-5 text-white/32">
        I agree to TopOne&apos;s{" "}

        <Link
          href="/terms"
          className="text-emerald-200/75"
        >
          Terms
        </Link>{" "}
        and{" "}
        <Link
          href="/privacy"
          className="text-emerald-200/75"
        >
          Privacy Policy
        </Link>
        .
      </span>
    </label>
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