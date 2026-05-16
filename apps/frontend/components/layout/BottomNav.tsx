"use client";

import { Home, History, User } from "lucide-react";
import { cn } from "@/lib/cn";
import { useI18n } from "@/components/i18n/LanguageProvider";

export type NavTab = "home" | "profile";

export function BottomNav({
  active = "home",
  onHome,
  onProfile,
}: {
  active?: NavTab;
  onHome?: () => void;
  onProfile?: () => void;
}) {
  const { t } = useI18n();
  const items = [
    { id: "home", icon: Home, label: t("nav.home"), onClick: onHome },
    { id: "history", icon: History, label: t("nav.history"), onClick: undefined },
    { id: "profile", icon: User, label: t("nav.profile"), onClick: onProfile },
  ] as const;

  return (
    <nav className="mt-auto border-t border-white/[0.05] px-6 py-4">
      <div className="flex items-center justify-around">
        {items.map(({ id, icon: Icon, label, onClick }) => {
          const isActive = id === active;
          return (
            <button
              key={id}
              onClick={onClick}
              disabled={!onClick}
              className={cn(
                "flex flex-col items-center gap-1 text-[11px] font-medium transition",
                isActive
                  ? "text-gold"
                  : onClick
                    ? "text-charcoal-600 hover:text-gold-200"
                    : "cursor-default text-charcoal-700",
              )}
            >
              <Icon size={20} strokeWidth={isActive ? 2.4 : 1.8} />
              {label}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
