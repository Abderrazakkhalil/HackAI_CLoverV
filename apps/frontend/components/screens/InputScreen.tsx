"use client";

import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { ImageUpload } from "@/components/upload/ImageUpload";
import { MicButton } from "@/components/recording/MicButton";
import { SpeechLangPicker } from "@/components/recording/SpeechLangPicker";
import { Waveform } from "@/components/recording/Waveform";
import { Button } from "@/components/ui/Button";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { fadeUp, staggerContainer } from "@/lib/motion";
import type { useRecorder } from "@/hooks/useRecorder";
import type { SpeechLang } from "@/lib/speechLang";

function fmt(s: number) {
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(
    s % 60,
  ).padStart(2, "0")}`;
}

export function InputScreen({
  image,
  setImage,
  recorder,
  speechLang,
  setSpeechLang,
  onGenerate,
  error,
}: {
  image: File | null;
  setImage: (f: File | null) => void;
  recorder: ReturnType<typeof useRecorder>;
  speechLang: SpeechLang;
  setSpeechLang: (l: SpeechLang) => void;
  onGenerate: () => void;
  error: string | null;
}) {
  const { t } = useI18n();
  const { status, seconds, levels, error: micError, start, stop, reset } =
    recorder;
  const recording = status === "recording";
  const canGenerate = status === "recorded" && !recording;

  return (
    <motion.div
      variants={staggerContainer}
      initial="initial"
      animate="animate"
      className="flex flex-1 flex-col"
    >
      <motion.div variants={fadeUp} className="mb-6 mt-2 text-center">
        <h1 className="text-[28px] font-bold leading-tight tracking-tight text-gold-50">
          {t("input.title")}
        </h1>
        <p className="mx-auto mt-2 max-w-[18rem] text-sm text-charcoal-600">
          {t("input.subtitle")}
        </p>
      </motion.div>

      <motion.div variants={fadeUp}>
        <ImageUpload file={image} onSelect={setImage} />
      </motion.div>

      <motion.div
        variants={fadeUp}
        className="mt-5 flex flex-1 flex-col items-center justify-center gap-3 rounded-3xl border border-white/[0.05] bg-charcoal-850/40 py-7"
      >
        <SpeechLangPicker
          value={speechLang}
          onChange={setSpeechLang}
          disabled={recording}
        />

        {recording ? (
          <Waveform levels={levels} />
        ) : (
          <div className="h-12" />
        )}

        <MicButton
          status={status}
          onStart={start}
          onStop={stop}
          onReset={reset}
        />

        <div className="text-center">
          <p className="font-semibold text-gold-50">
            {recording
              ? t("rec.recording")
              : status === "recorded"
                ? t("rec.ready")
                : t("rec.pushToTalk")}
          </p>
          <p className="mt-0.5 font-mono text-sm text-charcoal-600">
            {recording
              ? fmt(seconds)
              : status === "recorded"
                ? t("rec.reRecord")
                : t(
                    speechLang === "amazigh"
                      ? "rec.describe.amazigh"
                      : "rec.describe",
                  )}
          </p>
        </div>
      </motion.div>

      {(error || micError) && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-4 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-2.5 text-center text-sm text-red-300"
        >
          {error || (micError ? t("rec.micDenied") : null)}
        </motion.div>
      )}

      <motion.div variants={fadeUp} className="mt-5">
        <Button
          onClick={onGenerate}
          disabled={!canGenerate}
          className="w-full py-4 text-base"
        >
          <Sparkles size={18} />
          {t("btn.generate")}
        </Button>
        <p className="mt-2 text-center text-xs text-charcoal-600">
          {canGenerate ? t("btn.readyWhen") : t("btn.voiceRequired")}
        </p>
      </motion.div>
    </motion.div>
  );
}
