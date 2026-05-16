import type { Variants } from "framer-motion";

export const easePremium = [0.22, 1, 0.36, 1] as [
  number,
  number,
  number,
  number,
];

export const screenVariants: Variants = {
  initial: { opacity: 0, y: 24, scale: 0.985 },
  animate: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.55, ease: easePremium },
  },
  exit: {
    opacity: 0,
    y: -18,
    scale: 0.985,
    transition: { duration: 0.35, ease: easePremium },
  },
};

export const staggerContainer: Variants = {
  animate: { transition: { staggerChildren: 0.09, delayChildren: 0.08 } },
};

export const fadeUp: Variants = {
  initial: { opacity: 0, y: 18 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: easePremium },
  },
};
