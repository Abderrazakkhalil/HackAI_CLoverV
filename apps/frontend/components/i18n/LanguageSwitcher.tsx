"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Globe, Check } from "lucide-react";
import { LANGS } from "@/lib/i18n";
import { useI18n } from "./LanguageProvider";

export function LanguageSwitcher() {
  const { lang, setLang } = useI18n();
  const [open, setOpen] = useState(false);
  const current = LANGS.find((l) => l.id === lang);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label="Change language"
        className="flex h-9 items-center gap-1.5 rounded-full px-3 text-gold-200 transition hover:bg-charcoal-800"
      >
        <Globe size={17} />
        <span className="text-xs font-semibold">{current?.label}</span>
      </button>

      <AnimatePresence>
        {open && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setOpen(false)}
            />
            <motion.ul
              initial={{ opacity: 0, y: -6, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -6, scale: 0.96 }}
              transition={{ duration: 0.16 }}
              className="absolute end-0 top-11 z-20 w-40 overflow-hidden rounded-2xl border border-white/[0.07] bg-charcoal-850/95 p-1 shadow-card backdrop-blur-xl"
            >
              {LANGS.map((l) => (
                <li key={l.id}>
                  <button
                    onClick={() => {
                      setLang(l.id);
                      setOpen(false);
                    }}
                    className={`flex w-full items-center justify-between rounded-xl px-3 py-2 text-sm transition ${
                      lang === l.id
                        ? "bg-gold-sheen text-gold-50"
                        : "text-charcoal-600 hover:bg-charcoal-800 hover:text-gold-200"
                    }`}
                  >
                    {l.label}
                    {lang === l.id && <Check size={14} className="text-gold" />}
                  </button>
                </li>
              ))}
            </motion.ul>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
