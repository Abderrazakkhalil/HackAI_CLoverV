"use client";

import { motion } from "framer-motion";
import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

type Variant = "primary" | "ghost" | "outline";

export function Button({
  children,
  onClick,
  disabled,
  variant = "primary",
  className,
  type = "button",
}: {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: Variant;
  className?: string;
  type?: "button" | "submit";
}) {
  const base =
    "relative inline-flex items-center justify-center gap-2 rounded-2xl px-6 py-3.5 text-[15px] font-semibold tracking-tight transition-colors duration-300 select-none";

  const styles: Record<Variant, string> = {
    primary:
      "text-charcoal-950 bg-gold-gradient shadow-gold hover:brightness-105 disabled:bg-none disabled:bg-charcoal-700 disabled:text-charcoal-600 disabled:shadow-none",
    outline:
      "text-gold-200 border border-gold/30 bg-charcoal-850/60 hover:border-gold/60 hover:text-gold-50",
    ghost: "text-gold-200 hover:text-gold-50 hover:bg-charcoal-800/60",
  };

  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled}
      whileHover={disabled ? undefined : { scale: 1.015 }}
      whileTap={disabled ? undefined : { scale: 0.975 }}
      transition={{ type: "spring", stiffness: 400, damping: 22 }}
      className={cn(
        base,
        styles[variant],
        disabled && "cursor-not-allowed",
        className,
      )}
    >
      {variant === "primary" && !disabled && (
        <span className="pointer-events-none absolute inset-0 overflow-hidden rounded-2xl">
          <span className="absolute -inset-y-2 -left-1/3 w-1/3 -skew-x-12 bg-white/25 blur-md animate-shimmer" />
        </span>
      )}
      <span className="relative z-10 inline-flex items-center gap-2">
        {children}
      </span>
    </motion.button>
  );
}
