"use client";

import type { ReactNode } from "react";
import { BrandHeader } from "./BrandHeader";
import { BottomNav } from "./BottomNav";

/**
 * Premium mobile app frame, centered on a cinematic charcoal backdrop.
 * Mobile-first: the frame is the viewport on phones and an elegant
 * floating device on larger screens.
 */
export function AppShell({
  children,
  onBack,
  headerVariant = "default",
}: {
  children: ReactNode;
  onBack?: () => void;
  headerVariant?: "default" | "result";
}) {
  return (
    <div className="app-backdrop flex min-h-screen items-stretch justify-center sm:items-center sm:p-6">
      <div className="relative flex min-h-screen w-full max-w-[440px] flex-col overflow-hidden bg-charcoal-900 sm:min-h-[860px] sm:rounded-[2.75rem] sm:border sm:border-white/[0.06] sm:shadow-card">
        {/* Top gold aura */}
        <div className="pointer-events-none absolute -top-24 left-1/2 h-56 w-72 -translate-x-1/2 rounded-full bg-gold/20 blur-3xl" />
        <BrandHeader onBack={onBack} variant={headerVariant} />
        <div className="relative flex flex-1 flex-col px-6 pb-2 pt-2">
          {children}
        </div>
        <BottomNav />
      </div>
    </div>
  );
}
