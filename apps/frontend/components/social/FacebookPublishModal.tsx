"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  CheckCircle2,
  ExternalLink,
  Facebook,
  ImageOff,
  Loader2,
  ShieldCheck,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { publishFacebookPost } from "@/lib/api";

type Status = "idle" | "publishing" | "success" | "error";

export function FacebookPublishModal({
  open,
  onClose,
  defaultCaption,
  imageDataUrl,
}: {
  open: boolean;
  onClose: () => void;
  defaultCaption: string;
  /** The photo the artisan uploaded at the start (data URL), or null. */
  imageDataUrl: string | null;
}) {
  const { t, rtl } = useI18n();
  const [caption, setCaption] = useState(defaultCaption);
  const [status, setStatus] = useState<Status>("idle");
  const [postId, setPostId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Reset to a clean state every time the modal is (re)opened.
  useEffect(() => {
    if (open) {
      setCaption(defaultCaption);
      setStatus("idle");
      setPostId(null);
      setErrorMsg(null);
    }
  }, [open, defaultCaption]);

  async function handlePublish() {
    const cap = caption.trim();
    if (!cap) {
      setErrorMsg(t("fb.captionRequired"));
      setStatus("error");
      return;
    }
    setStatus("publishing");
    setErrorMsg(null);
    try {
      const res = await publishFacebookPost(cap, imageDataUrl);
      setPostId(res.post_id);
      setStatus("success");
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : t("fb.error"));
      setStatus("error");
    }
  }

  const busy = status === "publishing";

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-end justify-center sm:items-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div
            className="absolute inset-0 bg-charcoal-950/80 backdrop-blur-sm"
            onClick={busy ? undefined : onClose}
          />

          <motion.div
            dir={rtl ? "rtl" : "ltr"}
            initial={{ y: 32, opacity: 0, scale: 0.98 }}
            animate={{ y: 0, opacity: 1, scale: 1 }}
            exit={{ y: 24, opacity: 0, scale: 0.98 }}
            transition={{ type: "spring", stiffness: 320, damping: 28 }}
            className="relative z-10 m-3 w-full max-w-md overflow-hidden rounded-3xl border border-white/[0.07] bg-charcoal-900 shadow-card"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-white/[0.05] px-5 py-4">
              <div className="flex items-center gap-2.5">
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#1877F2]/15 text-[#3b82f6]">
                  <Facebook size={18} />
                </span>
                <h3 className="text-base font-semibold text-gold-50">
                  {t("fb.modal.title")}
                </h3>
              </div>
              <button
                aria-label={t("fb.cancel")}
                onClick={busy ? undefined : onClose}
                disabled={busy}
                className="text-charcoal-600 transition hover:text-gold-50 disabled:opacity-40"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4 p-5">
              {status === "success" ? (
                <div className="flex flex-col items-center gap-3 py-4 text-center">
                  <CheckCircle2 size={44} className="text-emerald-400" />
                  <p className="text-sm font-medium text-gold-50">
                    {t("fb.success")}
                  </p>
                  {postId && (
                    <a
                      href={`https://www.facebook.com/${postId}`}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1.5 text-sm text-gold-200 underline-offset-4 hover:text-gold hover:underline"
                    >
                      {t("fb.viewPost")}
                      <ExternalLink size={14} />
                    </a>
                  )}
                  <Button
                    onClick={onClose}
                    variant="outline"
                    className="mt-2 w-full"
                  >
                    {t("fb.cancel")}
                  </Button>
                </div>
              ) : (
                <>
                  {/* Onboarding / connection explainer */}
                  <div className="rounded-2xl border border-gold/15 bg-charcoal-850/60 p-3.5">
                    <div className="flex items-center gap-2 text-sm font-medium text-gold-200">
                      <ShieldCheck size={15} className="text-gold" />
                      {t("fb.modal.connected")}
                    </div>
                    <p className="mt-1.5 text-xs leading-relaxed text-charcoal-600">
                      {t("fb.modal.explainer")}
                    </p>
                  </div>

                  {/* Caption */}
                  <div>
                    <label className="mb-1.5 block text-xs font-semibold text-gold-200">
                      {t("fb.caption")}
                    </label>
                    <textarea
                      value={caption}
                      onChange={(e) => setCaption(e.target.value)}
                      disabled={busy}
                      rows={5}
                      className="w-full resize-none rounded-xl border border-white/[0.06] bg-charcoal-850 px-3 py-2.5 text-sm leading-relaxed text-gold-50 outline-none transition focus:border-gold/40 disabled:opacity-50"
                    />
                  </div>

                  {/* The artisan's uploaded photo (or text-only note) */}
                  {imageDataUrl ? (
                    <div className="flex items-center gap-3 rounded-xl border border-white/[0.06] bg-charcoal-850 p-2.5">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={imageDataUrl}
                        alt=""
                        className="h-14 w-14 shrink-0 rounded-lg object-cover"
                      />
                      <p className="text-xs leading-relaxed text-charcoal-600">
                        {t("fb.withImage")}
                      </p>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2.5 rounded-xl border border-white/[0.06] bg-charcoal-850 px-3 py-2.5 text-xs text-charcoal-600">
                      <ImageOff size={15} className="shrink-0 text-charcoal-600" />
                      {t("fb.noImage")}
                    </div>
                  )}

                  {status === "error" && errorMsg && (
                    <p className="rounded-xl border border-red-500/25 bg-red-500/10 px-3 py-2 text-xs text-red-300">
                      {errorMsg}
                    </p>
                  )}

                  <div className="flex gap-3 pt-1">
                    <Button
                      onClick={onClose}
                      variant="outline"
                      disabled={busy}
                      className="flex-1"
                    >
                      {t("fb.cancel")}
                    </Button>
                    <Button
                      onClick={handlePublish}
                      disabled={busy}
                      className="flex-1"
                    >
                      {busy ? (
                        <>
                          <Loader2 size={16} className="animate-spin" />
                          {t("fb.publishing")}
                        </>
                      ) : (
                        <>
                          <Facebook size={16} />
                          {t("fb.confirm")}
                        </>
                      )}
                    </Button>
                  </div>
                </>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
