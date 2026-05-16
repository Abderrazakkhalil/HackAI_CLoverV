"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Check } from "lucide-react";
import { Logo } from "@/components/Logo";

const STEPS = [
  "Transcribing your voice",
  "Understanding your product",
  "Crafting the perfect description",
  "Almost done…",
];

function Particles() {
  const dots = Array.from({ length: 14 });
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {dots.map((_, i) => {
        const left = (i * 37) % 100;
        const delay = (i % 7) * 0.5;
        const dur = 6 + (i % 5);
        return (
          <motion.span
            key={i}
            className="absolute h-1 w-1 rounded-full bg-gold/60"
            style={{ left: `${left}%`, bottom: -8 }}
            animate={{ y: [-0, -360], opacity: [0, 0.9, 0] }}
            transition={{
              duration: dur,
              delay,
              repeat: Infinity,
              ease: "easeOut",
            }}
          />
        );
      })}
    </div>
  );
}

export function GenerationScreen() {
  const [progress, setProgress] = useState(6);
  const [step, setStep] = useState(0);

  useEffect(() => {
    const p = setInterval(
      () => setProgress((v) => (v >= 96 ? v : v + Math.random() * 7)),
      280,
    );
    const s = setInterval(
      () => setStep((v) => Math.min(v + 1, STEPS.length - 1)),
      1300,
    );
    return () => {
      clearInterval(p);
      clearInterval(s);
    };
  }, []);

  const R = 70;
  const C = 2 * Math.PI * R;
  const pct = Math.min(progress, 100);

  return (
    <div className="relative flex flex-1 flex-col items-center justify-center">
      <Particles />

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h2 className="text-2xl font-bold tracking-tight text-gold-50">
          Generating your
          <br />
          product listing…
        </h2>
        <p className="mt-2 text-sm text-charcoal-600">
          Sit back while our AI works its magic ✨
        </p>
      </motion.div>

      {/* Progress ring + glowing logo */}
      <div className="relative my-10 flex items-center justify-center">
        <motion.div
          className="absolute h-44 w-44 rounded-full bg-gold/15 blur-2xl"
          animate={{ scale: [1, 1.15, 1], opacity: [0.5, 0.85, 0.5] }}
          transition={{ duration: 2.6, repeat: Infinity }}
        />
        <svg width="180" height="180" className="-rotate-90">
          <defs>
            <linearGradient id="hf-ring" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#f0dcae" />
              <stop offset="50%" stopColor="#d4a85a" />
              <stop offset="100%" stopColor="#9a7332" />
            </linearGradient>
          </defs>
          <circle
            cx="90"
            cy="90"
            r={R}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth="4"
          />
          <motion.circle
            cx="90"
            cy="90"
            r={R}
            fill="none"
            stroke="url(#hf-ring)"
            strokeWidth="4"
            strokeLinecap="round"
            strokeDasharray={C}
            animate={{ strokeDashoffset: C - (C * pct) / 100 }}
            transition={{ ease: "easeOut" }}
          />
        </svg>
        <div className="absolute flex flex-col items-center">
          <motion.div
            animate={{ scale: [1, 1.06, 1] }}
            transition={{ duration: 2.4, repeat: Infinity }}
          >
            <Logo size={64} glow spin />
          </motion.div>
          <span className="mt-3 font-mono text-lg font-semibold text-gold-gradient">
            {Math.round(pct)}%
          </span>
        </div>
      </div>

      {/* Checklist */}
      <div className="w-full rounded-2xl border border-white/[0.05] bg-charcoal-850/50 p-5">
        <div className="flex flex-col gap-3.5">
          {STEPS.map((label, i) => {
            const done = i < step;
            const active = i === step;
            return (
              <motion.div
                key={label}
                initial={{ opacity: 0, x: -8 }}
                animate={{
                  opacity: done || active ? 1 : 0.4,
                  x: 0,
                }}
                transition={{ delay: i * 0.1 }}
                className="flex items-center gap-3"
              >
                <span
                  className={`flex h-6 w-6 items-center justify-center rounded-full border text-[11px] transition ${
                    done
                      ? "border-gold bg-gold text-charcoal-950"
                      : active
                        ? "border-gold/60 text-gold"
                        : "border-charcoal-600 text-charcoal-600"
                  }`}
                >
                  {done ? (
                    <Check size={13} strokeWidth={3} />
                  ) : active ? (
                    <motion.span
                      className="h-2 w-2 rounded-full bg-gold"
                      animate={{ opacity: [1, 0.3, 1] }}
                      transition={{ duration: 1, repeat: Infinity }}
                    />
                  ) : (
                    ""
                  )}
                </span>
                <span
                  className={`text-sm ${
                    done || active ? "text-gold-50" : "text-charcoal-600"
                  }`}
                >
                  {label}
                </span>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
