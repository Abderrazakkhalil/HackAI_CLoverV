"use client";

import { motion } from "framer-motion";
import { Languages } from "lucide-react";
import { SPEECH_LANGS, type SpeechLang } from "@/lib/speechLang";
import { useI18n } from "@/components/i18n/LanguageProvider";

export function SpeechLangPicker({
  value,
  onChange,
  disabled = false,
}: {
  value: SpeechLang;
  onChange: (l: SpeechLang) => void;
  disabled?: boolean;
}) {
  const { t } = useI18n();

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-charcoal-600">
        <Languages size={12} />
        <span>{t("speechLang.label")}</span>
      </div>
      <div
        role="radiogroup"
        aria-label={t("speechLang.label")}
        className={`flex items-center gap-1 rounded-full border border-white/[0.07] bg-charcoal-900/60 p-1 ${
          disabled ? "opacity-50" : ""
        }`}
      >
        {SPEECH_LANGS.map((l) => {
          const active = l.id === value;
          return (
            <motion.button
              key={l.id}
              type="button"
              role="radio"
              aria-checked={active}
              disabled={disabled}
              onClick={() => !disabled && onChange(l.id)}
              whileTap={{ scale: 0.96 }}
              className={`rounded-full px-3.5 py-1 text-xs font-semibold transition ${
                active
                  ? "bg-gold-sheen text-gold-50 shadow-gold-lg"
                  : "text-charcoal-600 hover:text-gold-200"
              }`}
            >
              <span className="me-1">{t(`speechLang.${l.id}`)}</span>
              <span className="text-[10px] text-charcoal-600">
                {l.nativeLabel}
              </span>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}
