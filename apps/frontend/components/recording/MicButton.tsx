"use client";

import { motion } from "framer-motion";
import { Mic, Square, RotateCcw } from "lucide-react";
import type { RecorderStatus } from "@/hooks/useRecorder";

export function MicButton({
  status,
  onStart,
  onStop,
  onReset,
  size = 76,
}: {
  status: RecorderStatus;
  onStart: () => void;
  onStop: () => void;
  onReset: () => void;
  size?: number;
}) {
  const recording = status === "recording";
  const recorded = status === "recorded";

  return (
    <div className="relative flex items-center justify-center">
      {recording && (
        <>
          <span className="absolute inset-0 m-auto animate-pulse-ring rounded-full bg-gold/40" style={{ width: size, height: size }} />
          <span
            className="absolute inset-0 m-auto animate-pulse-ring rounded-full bg-gold/30"
            style={{ width: size, height: size, animationDelay: "0.6s" }}
          />
        </>
      )}
      <motion.button
        type="button"
        onClick={recording ? onStop : recorded ? onReset : onStart}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.94 }}
        aria-label={
          recording ? "Stop recording" : recorded ? "Re-record" : "Start recording"
        }
        style={{ width: size, height: size }}
        className={`relative flex items-center justify-center rounded-full transition-colors ${
          recording
            ? "bg-charcoal-800 text-gold ring-2 ring-gold"
            : recorded
              ? "bg-charcoal-800 text-gold-200 ring-1 ring-gold/30"
              : "bg-gold-gradient text-charcoal-950 shadow-gold-lg"
        }`}
      >
        {recording ? (
          <Square size={26} fill="currentColor" />
        ) : recorded ? (
          <RotateCcw size={26} />
        ) : (
          <Mic size={28} />
        )}
      </motion.button>
    </div>
  );
}
