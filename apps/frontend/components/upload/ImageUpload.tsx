"use client";

import { useCallback, useRef, useState } from "react";
import { motion } from "framer-motion";
import { UploadCloud, X } from "lucide-react";
import { useI18n } from "@/components/i18n/LanguageProvider";

export function ImageUpload({
  file,
  onSelect,
}: {
  file: File | null;
  onSelect: (file: File | null) => void;
}) {
  const { t } = useI18n();
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  const handle = useCallback(
    (f: File | null) => {
      if (!f || !f.type.startsWith("image/")) return;
      setPreview(URL.createObjectURL(f));
      onSelect(f);
    },
    [onSelect],
  );

  const clear = (e: React.MouseEvent) => {
    e.stopPropagation();
    setPreview(null);
    onSelect(null);
  };

  if (preview && file) {
    return (
      <motion.div
        layout
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        className="relative overflow-hidden rounded-3xl border border-gold/20 shadow-gold"
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={preview}
          alt="Product"
          className="aspect-[4/3] w-full object-cover"
        />
        <button
          onClick={clear}
          aria-label="Remove image"
          className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-full bg-charcoal-950/70 text-gold-100 backdrop-blur transition hover:bg-charcoal-950"
        >
          <X size={16} />
        </button>
      </motion.div>
    );
  }

  return (
    <motion.div
      whileHover={{ scale: 1.008 }}
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        handle(e.dataTransfer.files?.[0] ?? null);
      }}
      className={`group relative flex aspect-[5/3] cursor-pointer flex-col items-center justify-center gap-3 rounded-3xl border-2 border-dashed transition-colors ${
        dragging
          ? "border-gold bg-gold/10"
          : "border-gold/25 bg-charcoal-850/50 hover:border-gold/50"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        capture="environment"
        className="hidden"
        onChange={(e) => handle(e.target.files?.[0] ?? null)}
      />
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gold-sheen text-gold shadow-gold-sm transition group-hover:scale-105">
        <UploadCloud size={24} />
      </div>
      <div className="text-center">
        <p className="font-semibold text-gold-50">{t("upload.title")}</p>
        <p className="text-sm text-charcoal-600">{t("upload.hint")}</p>
        <p className="mt-1 text-xs text-charcoal-600">
          {t("upload.formats")}
        </p>
      </div>
    </motion.div>
  );
}
