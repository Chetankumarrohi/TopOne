"use client";

import { Dna, UserRound } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";

function getPageLabel(pathname: string) {
  if (pathname.startsWith("/fund-radar")) return "Fund Radar";
  if (pathname.startsWith("/invest")) return "Genie Invest";
  if (pathname.startsWith("/portfolio")) return "Portfolio";
  if (pathname.startsWith("/goals")) return "Goals";
  if (pathname.startsWith("/financial-twin")) return "Financial Twin";
  if (pathname.startsWith("/risk-assessment")) return "Risk Profile";
  if (pathname.startsWith("/financial-profile")) return "Financial Profile";
  return "";
}

export default function MobileHeader() {
  const router = useRouter();
  const pathname = usePathname();
  const pageLabel = getPageLabel(pathname);

  return (
    <header className="sticky top-0 z-40 border-b border-white/[0.055] bg-[#05070b]/90 backdrop-blur-2xl lg:hidden">
      <div
        className="flex min-h-[62px] items-center justify-between gap-3 px-4"
        style={{ paddingTop: "env(safe-area-inset-top)" }}
      >
        <button
          type="button"
          onClick={() => router.push("/dashboard")}
          className="flex min-w-0 items-center gap-2.5"
        >
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-emerald-400/20 bg-emerald-400/[0.07]">
            <div className="h-2.5 w-2.5 rounded-full bg-emerald-300 shadow-[0_0_12px_rgba(110,231,183,.7)]" />
          </div>

          <div className="min-w-0 text-left">
            <span className="block text-lg font-semibold tracking-[-0.04em]">
              Investi<span className="text-emerald-300">Genie</span>
            </span>

            {pageLabel && (
              <span className="block truncate text-[9px] uppercase tracking-[0.12em] text-white/20">
                {pageLabel}
              </span>
            )}
          </div>
        </button>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => router.push("/financial-twin")}
            aria-label="Financial Twin"
            className="flex h-9 w-9 items-center justify-center rounded-full border border-white/[0.08] bg-white/[0.03] text-white/42 transition active:scale-95"
          >
            <Dna size={17} strokeWidth={1.8} />
          </button>

          <button
            type="button"
            onClick={() => router.push("/financial-profile")}
            aria-label="Financial profile"
            className="flex h-9 w-9 items-center justify-center rounded-full border border-white/[0.08] bg-white/[0.035] text-white/55 transition active:scale-95"
          >
            <UserRound size={17} strokeWidth={1.8} />
          </button>
        </div>
      </div>
    </header>
  );
}