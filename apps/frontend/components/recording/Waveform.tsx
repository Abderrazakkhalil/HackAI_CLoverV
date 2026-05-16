"use client";

import { motion } from "framer-motion";

/** Live gold waveform driven by analyser levels (0..1). */
export function Waveform({ levels }: { levels: number[] }) {
  return (
    <div className="flex h-12 items-center justify-center gap-[3px]">
      {levels.map((v, i) => (
        <motion.span
          key={i}
          className="w-[3px] rounded-full bg-gold-gradient"
          animate={{ height: `${Math.round(v * 100)}%` }}
          transition={{ duration: 0.12, ease: "easeOut" }}
          style={{ minHeight: 4 }}
        />
      ))}
    </div>
  );
}
