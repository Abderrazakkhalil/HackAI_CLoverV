// Mirror of the backend Hirafi pipeline contracts.
// Kept in sync with packages/shared-types.

export interface LocalizedText {
  en: string;
  fr: string;
  ar: string;
}

export interface Price {
  amount: number;
  currency: string;
  price_usd_estimate: number;
  negotiable: boolean;
}

export interface Dimensions {
  length_cm: number | null;
  width_cm: number | null;
  height_cm: number | null;
  weight_kg: number | null;
}

export interface Origin {
  country: string;
  region: string | null;
  technique: string | null;
}

export interface Shipping {
  local_available: boolean;
  international_available: boolean;
  fragile: boolean;
}

export interface Product {
  title: LocalizedText;
  description: LocalizedText;
  category: string;
  subcategory: string | null;
  tags: string[];
  price: Price;
  dimensions: Dimensions;
  materials: string[];
  colors: string[];
  origin: Origin;
  condition: string;
  quantity_available: number | null;
  lead_time_days: number | null;
  shipping: Shipping;
  artisan_notes: string | null;
  raw_transcript: string;
  confidence_score: number;
  missing_fields: string[];
}

export type PriceSource = "user" | "extracted" | "ai_recommended";

export interface PriceRecommendation {
  suggested: number;
  min: number;
  max: number;
  currency: string;
  confidence: number;
  reasoning: string;
  comparable_ids: string[];
}

export interface Meta {
  pipeline_version: string;
  asr_model: string;
  asr_provider: string;
  llm_model: string;
  processed_at: string;
  audio_filename: string;
  inference_ms: number;
  price_source: PriceSource;
  price_recommendation: PriceRecommendation | null;
}

export interface TranscriptionResult {
  text: string;
  language: string;
  source: "moulsot" | "tamazight-nlp" | "mock";
}

export interface Artisan {
  full_name: string;
  city_region: string;
  phone: string;
}

export interface ProcessResponse {
  product: Product;
  meta: Meta;
  transcription: TranscriptionResult;
  artisan: Artisan | null;
  image_data_url: string | null;
}

export interface ApiError {
  error: string;
  detail?: string | null;
}
