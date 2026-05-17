// What the artisan will speak into the mic. Distinct from the UI
// language: this picks which ASR model runs on the backend.

export type SpeechLang = "darija" | "amazigh";

export const SPEECH_LANGS: {
  id: SpeechLang;
  nativeLabel: string;
}[] = [
  { id: "darija", nativeLabel: "الدارجة" },
  { id: "amazigh", nativeLabel: "ⵜⴰⵎⴰⵣⵉⵖⵜ" },
];

export const DEFAULT_SPEECH_LANG: SpeechLang = "darija";

const STORAGE_KEY = "hirfati.speechLang";

export function loadSpeechLang(): SpeechLang {
  if (typeof window === "undefined") return DEFAULT_SPEECH_LANG;
  const raw = window.localStorage.getItem(STORAGE_KEY);
  return raw === "amazigh" || raw === "darija" ? raw : DEFAULT_SPEECH_LANG;
}

export function saveSpeechLang(lang: SpeechLang) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, lang);
}
