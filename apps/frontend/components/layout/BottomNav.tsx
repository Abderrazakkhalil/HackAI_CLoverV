"use client";

import { Home, History, User } from "lucide-react";
import { cn } from "@/lib/cn";

const items = [
  { icon: Home, label: "Home", active: true },
  { icon: History, label: "History", active: false },
  { icon: User, label: "Profile", active: false },
];

export function BottomNav() {
  return (
    <nav className="mt-auto border-t border-white/[0.05] px-6 py-4">
      <div className="flex items-center justify-around">
        {items.map(({ icon: Icon, label, active }) => (
          <button
            key={label}
            className={cn(
              "flex flex-col items-center gap-1 text-[11px] font-medium transition",
              active
                ? "text-gold"
                : "text-charcoal-600 hover:text-gold-200",
            )}
          >
            <Icon size={20} strokeWidth={active ? 2.4 : 1.8} />
            {label}
          </button>
        ))}
      </div>
    </nav>
  );
}
