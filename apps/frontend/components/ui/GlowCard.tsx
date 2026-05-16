"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export function GlowCard({
  children,
  className,
  glow = false,
}: {
  children: ReactNode;
  className?: string;
  glow?: boolean;
}) {
  return (
    <div
      className={cn(
        "relative rounded-3xl border border-white/[0.06] bg-charcoal-850/70 shadow-card backdrop-blur-xl",
        glow && "shadow-gold-lg",
        className,
      )}
    >
      <div className="pointer-events-none absolute inset-x-8 -top-px h-px bg-gradient-to-r from-transparent via-gold/40 to-transparent" />
      {children}
    </div>
  );
}
