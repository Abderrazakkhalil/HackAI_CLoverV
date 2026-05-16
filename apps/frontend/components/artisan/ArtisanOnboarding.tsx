"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { UserRound } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Logo } from "@/components/Logo";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { fadeUp, staggerContainer } from "@/lib/motion";
import type { ArtisanProfile } from "@/lib/artisan";

function Field({
  label,
  placeholder,
  value,
  onChange,
  type = "text",
  rtl,
}: {
  label: string;
  placeholder: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  rtl: boolean;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-gold-200">
        {label}
      </span>
      <input
        type={type}
        dir={rtl ? "rtl" : "ltr"}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-2xl border border-white/[0.07] bg-charcoal-850/70 px-4 py-3 text-gold-50 outline-none transition placeholder:text-charcoal-600 focus:border-gold/50"
      />
    </label>
  );
}

export function ArtisanOnboarding({
  initial,
  onDone,
}: {
  initial?: ArtisanProfile | null;
  onDone: (p: ArtisanProfile) => void;
}) {
  const { t, rtl } = useI18n();
  const [fullName, setFullName] = useState(initial?.full_name ?? "");
  const [city, setCity] = useState(initial?.city_region ?? "");
  const [phone, setPhone] = useState(initial?.phone ?? "");
  const [error, setError] = useState(false);

  function submit() {
    if (!fullName.trim() || !city.trim() || !phone.trim()) {
      setError(true);
      return;
    }
    onDone({
      full_name: fullName.trim(),
      city_region: city.trim(),
      phone: phone.trim(),
    });
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="initial"
      animate="animate"
      className="flex flex-1 flex-col justify-center"
    >
      <motion.div variants={fadeUp} className="mb-7 text-center">
        <div className="mb-4 flex justify-center">
          <Logo size={56} glow />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-gold-50">
          {t("onb.title")}
        </h1>
        <p className="mx-auto mt-2 max-w-[20rem] text-sm text-charcoal-600">
          {t("onb.subtitle")}
        </p>
      </motion.div>

      <motion.div variants={fadeUp} className="flex flex-col gap-4">
        <Field
          label={t("onb.fullName")}
          placeholder={t("onb.fullName.ph")}
          value={fullName}
          onChange={setFullName}
          rtl={rtl}
        />
        <Field
          label={t("onb.city")}
          placeholder={t("onb.city.ph")}
          value={city}
          onChange={setCity}
          rtl={rtl}
        />
        <Field
          label={t("onb.phone")}
          placeholder={t("onb.phone.ph")}
          value={phone}
          onChange={setPhone}
          type="tel"
          rtl={rtl}
        />

        {error && (
          <p className="text-center text-sm text-red-300">
            {t("onb.required")}
          </p>
        )}

        <Button onClick={submit} className="mt-2 w-full py-4 text-base">
          <UserRound size={18} />
          {t("onb.submit")}
        </Button>
      </motion.div>
    </motion.div>
  );
}
