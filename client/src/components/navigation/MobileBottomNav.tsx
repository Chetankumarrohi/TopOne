"use client";

import {
  LayoutDashboard,
  WalletCards,
  Compass,
  Target,
  Gauge,
  LockKeyhole,
} from "lucide-react";
import { usePathname, useRouter } from "next/navigation";

const navigation = [
  { label: "Home", href: "/dashboard", icon: LayoutDashboard },
  { label: "Radar", href: "/fund-radar", icon: Gauge },
  { label: "Genie", href: "/invest", icon: Compass, primary: true, premium: true },
  { label: "Portfolio", href: "/portfolio", icon: WalletCards },
  { label: "Goals", href: "/goals", icon: Target },
];

export default function MobileBottomNav() {
  const pathname = usePathname();
  const router = useRouter();

  function isActive(href: string) {
    return pathname === href || (href !== "/dashboard" && pathname.startsWith(`${href}/`));
  }

  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-50 border-t border-white/[0.07] bg-[#080a0e]/95 px-2 backdrop-blur-2xl lg:hidden"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      <div className="mx-auto grid h-[70px] max-w-lg grid-cols-5">
        {navigation.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.href);

          return (
            <button
              key={item.href}
              type="button"
              onClick={() => router.push(item.href)}
              className={`relative flex min-w-0 flex-col items-center justify-center gap-1 text-[10px] transition active:scale-[0.96] ${
                active ? "text-emerald-200" : "text-white/32"
              }`}
            >
              {item.primary ? (
                <>
                  <span
                    className={`relative flex h-11 w-11 items-center justify-center rounded-2xl border transition ${
                      active
                        ? "border-emerald-300/35 bg-emerald-300 text-[#04100c] shadow-[0_10px_28px_rgba(110,231,183,.16)]"
                        : "border-emerald-400/20 bg-emerald-400/[0.11] text-emerald-200"
                    }`}
                  >
                    <Icon size={19} strokeWidth={2} />
                    {item.premium && (
                      <span
                        className={`absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full border ${
                          active
                            ? "border-[#04100c]/10 bg-[#04100c] text-emerald-200"
                            : "border-emerald-300/20 bg-[#07100c] text-emerald-200"
                        }`}
                      >
                        <LockKeyhole size={9} />
                      </span>
                    )}
                  </span>
                  <span className="text-[9px] font-medium text-emerald-200/70">
                    Genie
                  </span>
                </>
              ) : (
                <>
                  <Icon size={20} strokeWidth={active ? 2.2 : 1.7} />
                  <span className="max-w-full truncate">{item.label}</span>
                </>
              )}

              {active && !item.primary && (
                <span className="absolute top-1.5 h-0.5 w-5 rounded-full bg-emerald-300" />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
}