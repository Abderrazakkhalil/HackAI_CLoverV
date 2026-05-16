"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Check,
  Download,
  Heart,
  MapPin,
  PartyPopper,
  Plus,
  Ruler,
  Truck,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { fadeUp, staggerContainer } from "@/lib/motion";
import type { ProcessResponse } from "@/lib/types";

type Lang = "en" | "fr" | "ar";
const LANGS: { id: Lang; label: string }[] = [
  { id: "en", label: "EN" },
  { id: "fr", label: "FR" },
  { id: "ar", label: "AR" },
];

export function ProductScreen({
  data,
  onRestart,
}: {
  data: ProcessResponse;
  onRestart: () => void;
}) {
  const { product, image_data_url, meta, transcription } = data;
  const [lang, setLang] = useState<Lang>("en");
  const rtl = lang === "ar";

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
          Your product listing is ready!
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
              alt={product.title.en}
              className="aspect-[4/3] w-full object-cover"
            />
          ) : (
            <div className="flex aspect-[4/3] w-full items-center justify-center bg-charcoal-800 text-charcoal-600">
              No image
            </div>
          )}
          <span className="absolute left-3 top-3 rounded-full bg-charcoal-950/70 px-3 py-1 text-[11px] font-medium text-gold-100 backdrop-blur">
            {product.category}
          </span>
          <button
            aria-label="Save to favourites"
            className="absolute right-3 top-3 flex h-9 w-9 items-center justify-center rounded-full bg-charcoal-950/70 text-gold-100 backdrop-blur transition hover:text-gold"
          >
            <Heart size={17} />
          </button>
        </div>

        <div className="space-y-5 p-6">
          {/* Language switcher */}
          <div className="flex justify-end gap-1">
            {LANGS.map((l) => (
              <button
                key={l.id}
                onClick={() => setLang(l.id)}
                className={`rounded-full px-2.5 py-1 text-[11px] font-semibold transition ${
                  lang === l.id
                    ? "bg-gold text-charcoal-950"
                    : "text-charcoal-600 hover:text-gold-200"
                }`}
              >
                {l.label}
              </button>
            ))}
          </div>

          <div
            className="flex items-start justify-between gap-4"
            dir={rtl ? "rtl" : "ltr"}
          >
            <h3 className="text-lg font-semibold leading-snug text-gold-50">
              {product.title[lang]}
            </h3>
            <div className="shrink-0 text-right">
              <div className="rounded-full bg-gold-sheen px-3 py-1.5 text-sm font-semibold text-gold shadow-gold-sm">
                {product.price.amount} {product.price.currency}
              </div>
              <p className="mt-1 text-[11px] text-charcoal-600">
                ≈ ${product.price.price_usd_estimate}
                {product.price.negotiable ? " · negotiable" : ""}
              </p>
            </div>
          </div>

          <p
            dir={rtl ? "rtl" : "ltr"}
            className="text-sm leading-relaxed text-charcoal-600"
          >
            {product.description[lang]}
          </p>

          <div className="divider-gold" />

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
                <span>{dimText}</span>
              </div>
            )}
            <div className="flex items-center gap-2.5">
              <Truck size={15} className="shrink-0 text-gold" />
              <span>
                {product.shipping.international_available
                  ? "Ships locally & worldwide"
                  : "Local delivery"}
                {product.lead_time_days
                  ? ` · ${product.lead_time_days}d lead time`
                  : ""}
              </span>
            </div>
          </div>

          {product.materials.length > 0 && (
            <Facts label="Materials" items={product.materials} />
          )}
          {product.colors.length > 0 && (
            <Facts label="Colors" items={product.colors} />
          )}

          {product.tags.length > 0 && (
            <div>
              <h4 className="mb-2.5 text-sm font-semibold text-gold-200">
                SEO Tags
              </h4>
              <div className="flex flex-wrap gap-2">
                {product.tags.map((t) => (
                  <span
                    key={t}
                    className="rounded-full border border-gold/15 bg-charcoal-800 px-3 py-1 text-xs text-gold-200"
                  >
                    #{t.replace(/\s+/g, "")}
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
              Darija transcript · {transcription.source} ·{" "}
              {Math.round(product.confidence_score * 100)}% confidence
            </summary>
            <p dir="rtl" className="mt-2 leading-relaxed">
              {product.raw_transcript}
            </p>
            <p className="mt-2 text-[11px] text-charcoal-700">
              {meta.llm_model} · {meta.asr_model} · {meta.inference_ms}ms
            </p>
          </details>
        </div>
      </motion.div>

      <motion.div variants={fadeUp} className="mt-5 grid grid-cols-2 gap-3">
        <Button onClick={onRestart} variant="primary">
          <Download size={17} />
          Save Listing
        </Button>
        <Button onClick={onRestart} variant="outline">
          <Plus size={17} />
          Create Another
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
