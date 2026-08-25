import DesktopSidebar from "../navigation/DesktopSidebar";
import MobileBottomNav from "../navigation/MobileBottomNav";
import MobileHeader from "../navigation/MobileHeader";

export default function AppShell({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[#05070b] text-white">
      <DesktopSidebar />
      <MobileHeader />

      <div className="lg:pl-[260px]">
        <div className="min-h-screen pb-[calc(84px+env(safe-area-inset-bottom))] lg:pb-0">
          {children}
        </div>
      </div>

      <MobileBottomNav />
    </div>
  );
}