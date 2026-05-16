// Artisan profile — collected once at sign-up, persisted locally (no
// accounts in the MVP), and attached to every generated post.

export interface ArtisanProfile {
  full_name: string;
  city_region: string;
  phone: string;
}

const STORAGE_KEY = "hirfati.artisan";

export function loadArtisan(): ArtisanProfile | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const p = JSON.parse(raw) as ArtisanProfile;
    if (p.full_name && p.city_region && p.phone) return p;
    return null;
  } catch {
    return null;
  }
}

export function saveArtisan(p: ArtisanProfile): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(p));
}
