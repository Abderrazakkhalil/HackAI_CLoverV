"use client";

import { motion } from "framer-motion";
import { MapPin, Pencil, Phone, UserRound } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Logo } from "@/components/Logo";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { fadeUp, staggerContainer } from "@/lib/motion";
import type { ArtisanProfile } from "@/lib/artisan";

function Row({
  icon: Icon,
  label,
  value,
  href,
}: {
  icon: typeof UserRound;
  label: string;
  value: string;
  href?: string;
}) {
  const body = (
    <>
      <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gold-sheen text-gold shadow-gold-sm">
        <Icon size={18} />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-charcoal-600">{label}</p>
        <p dir="ltr" className="truncate font-medium text-gold-50">
          {value}
        </p>
      </div>
    </>
  );
  const cls =
    "flex items-center gap-3.5 rounded-2xl border border-white/[0.05] bg-charcoal-850/60 p-4";
  return href ? (
    <a href={href} target="_blank" rel="noreferrer" className={`${cls} transition hover:border-gold/30`}>
      {body}
    </a>
  ) : (
    <div className={cls}>{body}</div>
  );
}

export function ProfileScreen({
  artisan,
  onEdit,
  onBack,
}: {
  artisan: ArtisanProfile;
  onEdit: () => void;
  onBack: () => void;
}) {
  const { t } = useI18n();

  return (
    <motion.div
      variants={staggerContainer}
      initial="initial"
      animate="animate"
      className="flex flex-1 flex-col"
    >
      <motion.div variants={fadeUp} className="mb-7 mt-2 text-center">
        <div className="mb-4 flex justify-center">
          <div className="relative">
            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-charcoal-850 shadow-gold">
              <UserRound size={34} className="text-gold" />
            </div>
            <span className="absolute -bottom-1 -end-1">
              <Logo size={26} glow />
            </span>
          </div>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-gold-50">
          {t("profile.title")}
        </h1>
        <p className="mx-auto mt-2 max-w-[20rem] text-sm text-charcoal-600">
          {t("profile.subtitle")}
        </p>
      </motion.div>

      <motion.div variants={fadeUp} className="flex flex-col gap-3">
        <Row
          icon={UserRound}
          label={t("onb.fullName")}
          value={artisan.full_name}
        />
        <Row
          icon={MapPin}
          label={t("onb.city")}
          value={artisan.city_region}
        />
        <Row
          icon={Phone}
          label={t("onb.phone")}
          value={artisan.phone}
          href={`https://wa.me/${artisan.phone.replace(/[^\d]/g, "")}`}
        />
      </motion.div>

      <motion.div
        variants={fadeUp}
        className="mt-auto flex flex-col gap-3 pt-8"
      >
        <Button onClick={onEdit} className="w-full py-4">
          <Pencil size={17} />
          {t("onb.edit")}
        </Button>
        <Button onClick={onBack} variant="ghost" className="w-full">
          {t("profile.back")}
        </Button>
      </motion.div>
    </motion.div>
  );
}
