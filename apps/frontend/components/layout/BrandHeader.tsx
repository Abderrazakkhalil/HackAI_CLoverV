"use client";

import { ArrowLeft, HelpCircle, Share2 } from "lucide-react";
import { Logo } from "@/components/Logo";

export function BrandHeader({
  onBack,
  variant = "default",
}: {
  onBack?: () => void;
  variant?: "default" | "result";
}) {
  return (
    <header className="flex items-center justify-between px-6 pt-6">
      <button
        onClick={onBack}
        disabled={!onBack}
        aria-label="Back"
        className="flex h-9 w-9 items-center justify-center rounded-full text-gold-200 transition hover:bg-charcoal-800 disabled:opacity-0"
      >
        <ArrowLeft size={20} />
      </button>

      <div className="flex items-center gap-2">
        <Logo size={26} glow />
        <span className="text-lg font-semibold tracking-tight text-gold-gradient">
          Hirfati
        </span>
      </div>

      <button
        aria-label={variant === "result" ? "Share" : "Help"}
        className="flex h-9 w-9 items-center justify-center rounded-full text-gold-200 transition hover:bg-charcoal-800"
      >
        {variant === "result" ? (
          <Share2 size={18} />
        ) : (
          <HelpCircle size={20} />
        )}
      </button>
    </header>
  );
}
