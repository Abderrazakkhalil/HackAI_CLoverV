"use client";

import { motion } from "framer-motion";

/**
 * Hirfati brand mark — the official gold circuit-star icon.
 * The PNG already carries its own dark rounded app-tile, so the
 * component just frames it and adds optional gold glow / slow spin.
 */
export function Logo({
  size = 40,
  glow = false,
  spin = false,
  className = "",
}: {
  size?: number;
  glow?: boolean;
  spin?: boolean;
  className?: string;
}) {
  return (
    <motion.img
      src="/hirfati-logo.png"
      alt="Hirfati"
      width={size}
      height={size}
      className={`rounded-[22%] object-contain ${className}`}
      style={{
        width: size,
        height: size,
        filter: glow
          ? "drop-shadow(0 0 16px rgba(212,168,90,0.55))"
          : undefined,
      }}
      animate={spin ? { rotate: 360 } : undefined}
      transition={
        spin ? { duration: 18, repeat: Infinity, ease: "linear" } : undefined
      }
    />
  );
}

/** Larger brand lockup (splash / hero). */
export function LogoTile({ size = 72 }: { size?: number }) {
  return <Logo size={size} glow />;
}
