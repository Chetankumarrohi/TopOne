"use client";

import {
  LayoutDashboard,
  WalletCards,
  Compass,
  Target,
  Dna,
  UserRound,
  ShieldCheck,
  LogOut,
  Gauge,
  LockKeyhole,
} from "lucide-react";
import { usePathname, useRouter } from "next/navigation";

const primaryNavigation = [
  { label: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { label: "Fund Radar", href: "/fund-radar", icon: Gauge },
  { label: "Genie Invest", href: "/invest", icon: Compass, premium: true },
  { label: "Portfolio", href: "/portfolio", icon: WalletCards },
  { label: "Goals", href: "/goals", icon: Target },
  { label: "Financial Twin", href: "/financial-twin", icon: Dna },
];

const secondaryNavigation = [
  { label: "Financial Profile", href: "/financial-profile", icon: UserRound },
  { label: "Risk Profile", href: "/risk-assessment", icon: ShieldCheck },
];

export default function DesktopSidebar() {
  const pathname = usePathname();
  const router = useRouter();

  function isActive(href: string) {
    return pathname === href || (href !== "/dashboard" && pathname.startsWith(`${href}/`));
  }

  function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("token_type");
    router.replace("/login");
  }

  return (
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-[270px] border-r border-white/[0.06] bg-[#07090d]/95 backdrop-blur-2xl lg:flex lg:flex-col">
      <div className="flex h-[76px] items-center px-6">
        <button type="button" onClick={() => router.push("/dashboard")} className="group flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-emerald-400/20 bg-emerald-400/[0.07]">
            <div className="h-3 w-3 rounded-full bg-emerald-300 shadow-[0_0_16px_rgba(110,231,183,.75)]" />
          </div>
          <span className="text-xl font-semibold tracking-[-0.04em]">
            Investi<span className="text-emerald-300">Genie</span>
          </span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-5">
        <p className="mb-3 px-3 text-[10px] font-medium uppercase tracking-[0.18em] text-white/20">
          Wealth workspace
        </p>

        <nav className="space-y-1">
          {primaryNavigation.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);

            return (
              <button
                key={item.href}
                type="button"
                onClick={() => router.push(item.href)}
                className={`group flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm transition ${
                  active
                    ? item.premium
                      ? "border border-emerald-400/15 bg-emerald-400/[0.10] text-emerald-100"
                      : "bg-emerald-400/[0.09] text-emerald-200"
                    : "text-white/42 hover:bg-white/[0.04] hover:text-white/80"
                }`}
              >
                <Icon
                  size={18}
                  strokeWidth={1.8}
                  className={active || item.premium ? "text-emerald-300" : "text-white/30 group-hover:text-white/60"}
                />
                <span>{item.label}</span>

                {item.premium ? (
                  <span className="ml-auto inline-flex items-center gap-1 rounded-full border border-emerald-400/15 bg-emerald-400/[0.07] px-2 py-1 text-[9px] font-medium uppercase tracking-[0.10em] text-emerald-200/80">
                    <LockKeyhole size={10} />
                    Premium
                  </span>
                ) : active ? (
                  <span className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald-300 shadow-[0_0_10px_rgba(110,231,183,.7)]" />
                ) : null}
              </button>
            );
          })}
        </nav>

        <div className="my-6 border-t border-white/[0.05]" />

        <p className="mb-3 px-3 text-[10px] font-medium uppercase tracking-[0.18em] text-white/20">
          Financial identity
        </p>

        <nav className="space-y-1">
          {secondaryNavigation.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);

            return (
              <button
                key={item.href}
                type="button"
                onClick={() => router.push(item.href)}
                className={`group flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm transition ${
                  active
                    ? "bg-emerald-400/[0.09] text-emerald-200"
                    : "text-white/42 hover:bg-white/[0.04] hover:text-white/80"
                }`}
              >
                <Icon size={18} strokeWidth={1.8} className={active ? "text-emerald-300" : "text-white/30 group-hover:text-white/60"} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="mt-6 rounded-[18px] border border-emerald-400/10 bg-emerald-400/[0.035] p-4">
          <div className="flex items-center gap-2 text-[10px] font-medium uppercase tracking-[0.13em] text-emerald-200/65">
            <Gauge size={13} />
            Fund intelligence
          </div>
          <p className="mt-2 text-xs leading-5 text-white/30">
            Fund Radar shows how funds are performing. Genie Invest will decide what fits the user.
          </p>
        </div>
      </div>

      <div className="border-t border-white/[0.05] p-3">
        <button
          type="button"
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm text-white/35 transition hover:bg-white/[0.04] hover:text-white/70"
        >
          <LogOut size={18} strokeWidth={1.8} />
          Sign out
        </button>
      </div>
    </aside>
  );
}