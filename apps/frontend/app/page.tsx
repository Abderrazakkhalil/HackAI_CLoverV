"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AppShell } from "@/components/layout/AppShell";
import { InputScreen } from "@/components/screens/InputScreen";
import { GenerationScreen } from "@/components/screens/GenerationScreen";
import { ProductScreen } from "@/components/screens/ProductScreen";
import { useRecorder } from "@/hooks/useRecorder";
import { processArtisanProduct } from "@/lib/api";
import { screenVariants } from "@/lib/motion";
import type { ProcessResponse } from "@/lib/types";

type Phase = "input" | "loading" | "result";

export default function Home() {
  const [phase, setPhase] = useState<Phase>("input");
  const [image, setImage] = useState<File | null>(null);
  const [result, setResult] = useState<ProcessResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const recorder = useRecorder();

  async function handleGenerate() {
    if (!recorder.blob) return;
    setError(null);
    setPhase("loading");
    const startedAt = Date.now();
    try {
      const data = await processArtisanProduct(recorder.blob, image);
      // Let the cinematic loader breathe for at least a moment.
      const elapsed = Date.now() - startedAt;
      if (elapsed < 2600) {
        await new Promise((r) => setTimeout(r, 2600 - elapsed));
      }
      setResult(data);
      setPhase("result");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generation failed.");
      setPhase("input");
    }
  }

  function restart() {
    setResult(null);
    setImage(null);
    setError(null);
    recorder.reset();
    setPhase("input");
  }

  return (
    <AppShell
      onBack={phase === "result" ? restart : undefined}
      headerVariant={phase === "result" ? "result" : "default"}
    >
      <AnimatePresence mode="wait">
        <motion.div
          key={phase}
          variants={screenVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          className="flex flex-1 flex-col"
        >
          {phase === "input" && (
            <InputScreen
              image={image}
              setImage={setImage}
              recorder={recorder}
              onGenerate={handleGenerate}
              error={error}
            />
          )}
          {phase === "loading" && <GenerationScreen />}
          {phase === "result" && result && (
            <ProductScreen data={result} onRestart={restart} />
          )}
        </motion.div>
      </AnimatePresence>
    </AppShell>
  );
}
