"use client";

import { ArrowLeft, UserRound } from "lucide-react";
import { Logo } from "@/components/Logo";
import { LanguageSwitcher } from "@/components/i18n/LanguageSwitcher";

export function BrandHeader({
  onBack,
  onEditProfile,
}: {
  onBack?: () => void;
  onEditProfile?: () => void;
}) {
  return (
    <header className="flex items-center justify-between px-5 pt-6">
      <button
        onClick={onBack}
        disabled={!onBack}
        aria-label="Back"
        className="flex h-9 w-9 items-center justify-center rounded-full text-gold-200 transition hover:bg-charcoal-800 disabled:opacity-0 rtl:rotate-180"
      >
        <ArrowLeft size={20} />
      </button>

      <div className="flex items-center gap-2">
        <Logo size={26} glow />
        <span className="text-lg font-semibold tracking-tight text-gold-gradient">
          Hirfati
        </span>
      </div>

      <div className="flex items-center gap-1">
        <LanguageSwitcher />
        {onEditProfile && (
          <button
            onClick={onEditProfile}
            aria-label="Edit profile"
            className="flex h-9 w-9 items-center justify-center rounded-full text-gold-200 transition hover:bg-charcoal-800"
          >
            <UserRound size={18} />
          </button>
        )}
      </div>
    </header>
  );
}
