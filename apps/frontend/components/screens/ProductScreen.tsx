"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  ChevronDown,
  ChevronUp,
  Download,
  Heart,
  MapPin,
  PartyPopper,
  Phone,
  Plus,
  Ruler,
  Truck,
  UserRound,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { fadeUp, staggerContainer } from "@/lib/motion";
import type { ProcessResponse } from "@/lib/types";

export function ProductScreen({
  data,
  onRestart,
}: {
  data: ProcessResponse;
  onRestart: () => void;
}) {
  const { t, lang, rtl } = useI18n();
  const { product, image_data_url, meta, transcription, artisan } = data;

  const isAiPrice = meta.price_source === "ai_recommended";
  const rec = meta.price_recommendation;

  const [editedPrice, setEditedPrice] = useState<string>(
    String(product.price.amount || ""),
  );
  const [showReasoning, setShowReasoning] = useState(false);

  const dims = product.dimensions;
  const dimText = [
    dims.length_cm && `L ${dims.length_cm}cm`,
    dims.width_cm && `W ${dims.width_cm}cm`,
    dims.height_cm && `H ${dims.height_cm}cm`,
    dims.weight_kg && `${dims.weight_kg}kg`,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <motion.div
      variants={staggerContainer}
      initial="initial"
      animate="animate"
      className="flex flex-1 flex-col"
    >
      <motion.div
        variants={fadeUp}
        className="mb-4 mt-1 flex items-center justify-center gap-2 text-center"
      >
        <h2 className="text-xl font-bold tracking-tight text-gold-50">
          {t("result.ready")}
        </h2>
        <PartyPopper size={20} className="text-gold" />
      </motion.div>

      <motion.div
        variants={fadeUp}
        className="overflow-hidden rounded-3xl border border-white/[0.06] bg-charcoal-850/70 shadow-card backdrop-blur-xl"
      >
        <div className="relative">
          {image_data_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={image_data_url}
              alt={product.title[lang]}
              className="aspect-[4/3] w-full object-cover"
            />
          ) : (
            <div className="flex aspect-[4/3] w-full items-center justify-center bg-charcoal-800 text-charcoal-600">
              —
            </div>
          )}
          <span className="absolute start-3 top-3 rounded-full bg-charcoal-950/70 px-3 py-1 text-[11px] font-medium text-gold-100 backdrop-blur">
            {product.category}
          </span>
          <button
            aria-label="Save to favourites"
            className="absolute end-3 top-3 flex h-9 w-9 items-center justify-center rounded-full bg-charcoal-950/70 text-gold-100 backdrop-blur transition hover:text-gold"
          >
            <Heart size={17} />
          </button>
        </div>

        <div className="space-y-5 p-6">
          <div className="flex items-start justify-between gap-4">
            <h3 className="text-lg font-semibold leading-snug text-gold-50">
              {product.title[lang]}
            </h3>

            {/* Price block */}
            <div className="shrink-0 text-end">
              {isAiPrice && (
                <div className="mb-1.5 flex items-center justify-end gap-1.5">
                  <Bot size={13} className="text-gold" />
                  <span className="text-[11px] font-medium text-gold">
                    AI suggested
                  </span>
                  {rec && (
                    <button
                      onClick={() => setShowReasoning((v) => !v)}
                      className="rounded-full p-0.5 text-charcoal-600 hover:text-gold transition"
                      aria-label="Toggle reasoning"
                    >
                      {showReasoning ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                    </button>
                  )}
                </div>
              )}

              {/* Editable price input */}
              <div className="flex items-center gap-1.5 justify-end">
                <input
                  type="number"
                  min={0}
                  value={editedPrice}
                  onChange={(e) => setEditedPrice(e.target.value)}
                  className="w-24 rounded-full bg-charcoal-800 border border-gold/30 px-3 py-1.5 text-sm font-semibold text-gold shadow-gold-sm text-center outline-none focus:ring-2 focus:ring-gold/40 focus:border-gold/60 [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
                  aria-label="Price in MAD"
                />
                <span className="text-sm font-semibold text-gold">
                  {product.price.currency}
                </span>
              </div>

              {rec && (
                <p className="mt-1 text-[11px] text-charcoal-600">
                  {rec.min}–{rec.max} MAD ·{" "}
                  {Math.round(rec.confidence * 100)}% confidence
                </p>
              )}
              {!isAiPrice && (
                <p className="mt-1 text-[11px] text-charcoal-600">
                  ≈ ${product.price.price_usd_estimate}
                  {product.price.negotiable
                    ? ` · ${t("result.negotiable")}`
                    : ""}
                </p>
              )}
            </div>
          </div>

          {/* AI reasoning panel */}
          <AnimatePresence>
            {isAiPrice && showReasoning && rec && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden"
              >
                <div className="rounded-2xl border border-gold/20 bg-charcoal-800/60 p-4 text-sm text-charcoal-600">
                  <div className="mb-2 flex items-center gap-2">
                    <Bot size={14} className="text-gold" />
                    <span className="font-semibold text-gold-200">
                      Why this price?
                    </span>
                  </div>
                  <p className="leading-relaxed">{rec.reasoning}</p>
                  {rec.comparable_ids.length > 0 && (
                    <p className="mt-2 text-[11px] text-charcoal-700">
                      Based on {rec.comparable_ids.length} comparable listing
                      {rec.comparable_ids.length !== 1 ? "s" : ""} in our
                      catalog.
                    </p>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <p className="text-sm leading-relaxed text-charcoal-600">
            {product.description[lang]}
          </p>

          <div className="divider-gold" />

          {/* Artisan — collected at sign-up, part of every post */}
          {artisan && (
            <div className="rounded-2xl border border-gold/15 bg-charcoal-800/50 p-4">
              <h4 className="mb-2.5 text-sm font-semibold text-gold-200">
                {t("result.artisan")}
              </h4>
              <div className="space-y-1.5 text-sm text-charcoal-600">
                <div className="flex items-center gap-2.5">
                  <UserRound size={15} className="shrink-0 text-gold" />
                  <span className="text-gold-50">{artisan.full_name}</span>
                </div>
                <div className="flex items-center gap-2.5">
                  <MapPin size={15} className="shrink-0 text-gold" />
                  <span>{artisan.city_region}</span>
                </div>
                <a
                  href={`https://wa.me/${artisan.phone.replace(/[^\d]/g, "")}`}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-2.5 text-gold-200 hover:text-gold"
                >
                  <Phone size={15} className="shrink-0 text-gold" />
                  <span dir="ltr">{artisan.phone}</span>
                </a>
              </div>
            </div>
          )}

          {/* Quick facts */}
          <div className="grid grid-cols-1 gap-2.5 text-sm text-charcoal-600">
            {(product.origin.region || product.origin.technique) && (
              <div className="flex items-center gap-2.5">
                <MapPin size={15} className="shrink-0 text-gold" />
                <span>
                  {[
                    product.origin.region,
                    product.origin.technique,
                    product.origin.country,
                  ]
                    .filter(Boolean)
                    .join(" · ")}
                </span>
              </div>
            )}
            {dimText && (
              <div className="flex items-center gap-2.5">
                <Ruler size={15} className="shrink-0 text-gold" />
                <span dir="ltr">{dimText}</span>
              </div>
            )}
            <div className="flex items-center gap-2.5">
              <Truck size={15} className="shrink-0 text-gold" />
              <span>
                {product.shipping.international_available
                  ? t("result.shipWorldwide")
                  : t("result.shipLocal")}
                {product.lead_time_days
                  ? ` · ${product.lead_time_days} ${t("result.leadTime")}`
                  : ""}
              </span>
            </div>
          </div>

          {product.materials.length > 0 && (
            <Facts label={t("result.materials")} items={product.materials} />
          )}
          {product.colors.length > 0 && (
            <Facts label={t("result.colors")} items={product.colors} />
          )}

          {product.tags.length > 0 && (
            <div>
              <h4 className="mb-2.5 text-sm font-semibold text-gold-200">
                {t("result.seoTags")}
              </h4>
              <div className="flex flex-wrap gap-2">
                {product.tags.map((tag) => (
                  <span
                    key={tag}
                    dir="ltr"
                    className="rounded-full border border-gold/15 bg-charcoal-800 px-3 py-1 text-xs text-gold-200"
                  >
                    #{tag.replace(/\s+/g, "")}
                  </span>
                ))}
              </div>
            </div>
          )}

          {product.artisan_notes && (
            <p className="rounded-2xl border border-gold/10 bg-charcoal-800/60 p-4 text-sm italic leading-relaxed text-charcoal-600">
              “{product.artisan_notes}”
            </p>
          )}

          <details className="text-xs text-charcoal-600">
            <summary className="cursor-pointer select-none text-gold-200">
              {t("result.transcript")} · {transcription.source} ·{" "}
              {Math.round(product.confidence_score * 100)}%{" "}
              {t("result.confidence")}
            </summary>
            <p dir="rtl" className="mt-2 leading-relaxed">
              {product.raw_transcript}
            </p>
            <p dir="ltr" className="mt-2 text-[11px] text-charcoal-700">
              {meta.llm_model} · {meta.asr_model} · {meta.inference_ms}ms
            </p>
          </details>
        </div>
      </motion.div>

      <motion.div variants={fadeUp} className="mt-5 grid grid-cols-2 gap-3">
        <Button onClick={onRestart} variant="primary">
          <Download size={17} />
          Publish
        </Button>
        <Button onClick={onRestart} variant="outline">
          <Plus size={17} />
          {t("btn.createAnother")}
        </Button>
      </motion.div>
    </motion.div>
  );
}

function Facts({ label, items }: { label: string; items: string[] }) {
  return (
    <div>
      <h4 className="mb-2 text-sm font-semibold text-gold-200">{label}</h4>
      <div className="flex flex-wrap gap-2">
        {items.map((it) => (
          <span
            key={it}
            className="rounded-lg bg-charcoal-800 px-2.5 py-1 text-xs capitalize text-charcoal-600"
          >
            {it}
          </span>
        ))}
      </div>
    </div>
  );
}
