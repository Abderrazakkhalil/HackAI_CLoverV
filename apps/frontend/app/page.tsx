"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AppShell } from "@/components/layout/AppShell";
import { InputScreen } from "@/components/screens/InputScreen";
import { GenerationScreen } from "@/components/screens/GenerationScreen";
import { ProductScreen } from "@/components/screens/ProductScreen";
import { ProfileScreen } from "@/components/screens/ProfileScreen";
import { ArtisanOnboarding } from "@/components/artisan/ArtisanOnboarding";
import { useRecorder } from "@/hooks/useRecorder";
import { processArtisanProduct } from "@/lib/api";
import { screenVariants } from "@/lib/motion";
import {
  loadArtisan,
  saveArtisan,
  type ArtisanProfile,
} from "@/lib/artisan";
import {
  DEFAULT_SPEECH_LANG,
  loadSpeechLang,
  saveSpeechLang,
  type SpeechLang,
} from "@/lib/speechLang";
import type { ProcessResponse } from "@/lib/types";

type Phase = "onboarding" | "input" | "loading" | "result" | "profile";

export default function Home() {
  const [phase, setPhase] = useState<Phase>("input");
  const [artisan, setArtisan] = useState<ArtisanProfile | null>(null);
  const [image, setImage] = useState<File | null>(null);
  const [speechLang, setSpeechLangState] =
    useState<SpeechLang>(DEFAULT_SPEECH_LANG);
  const [result, setResult] = useState<ProcessResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const recorder = useRecorder();

  // Sign-up gate: no profile yet → onboarding first.
  useEffect(() => {
    const saved = loadArtisan();
    if (saved) setArtisan(saved);
    else setPhase("onboarding");
    setSpeechLangState(loadSpeechLang());
  }, []);

  function setSpeechLang(l: SpeechLang) {
    setSpeechLangState(l);
    saveSpeechLang(l);
  }

  function completeOnboarding(p: ArtisanProfile) {
    saveArtisan(p);
    setArtisan(p);
    setPhase("input");
  }

  async function handleGenerate() {
    if (!recorder.blob) return;
    setError(null);
    setPhase("loading");
    const startedAt = Date.now();
    try {
      const data = await processArtisanProduct(
        recorder.blob,
        image,
        artisan,
        speechLang,
      );
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

  const gated = phase === "onboarding";

  return (
    <AppShell
      onBack={
        phase === "result"
          ? restart
          : phase === "profile"
            ? () => setPhase("input")
            : undefined
      }
      onEditProfile={
        phase === "input" ? () => setPhase("profile") : undefined
      }
      activeTab={phase === "profile" ? "profile" : "home"}
      onHome={gated ? undefined : () => setPhase("input")}
      onProfile={
        gated || !artisan ? undefined : () => setPhase("profile")
      }
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
          {phase === "onboarding" && (
            <ArtisanOnboarding initial={artisan} onDone={completeOnboarding} />
          )}
          {phase === "input" && (
            <InputScreen
              image={image}
              setImage={setImage}
              recorder={recorder}
              speechLang={speechLang}
              setSpeechLang={setSpeechLang}
              onGenerate={handleGenerate}
              error={error}
            />
          )}
          {phase === "loading" && <GenerationScreen />}
          {phase === "result" && result && (
            <ProductScreen data={result} onRestart={restart} />
          )}
          {phase === "profile" && artisan && (
            <ProfileScreen
              artisan={artisan}
              onEdit={() => setPhase("onboarding")}
              onBack={() => setPhase("input")}
            />
          )}
        </motion.div>
      </AnimatePresence>
    </AppShell>
  );
}
