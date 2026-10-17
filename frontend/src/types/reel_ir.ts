export type LayoutMode = 'single_focus' | 'split_stage' | 'code_spotlight';
export type TemplateArchetype = 'standard_spotlight' | 'bug_hunter' | 'vs_battle' | 'predict_output';

export interface RedactionBox {
  id: string;
  start: number;
  end: number;
  bbox: [number, number, number, number];
  secret_type: 'api_key' | 'jwt_secret' | 'password' | 'email';
  confidence: number;
}

export interface SocialGrowthPack {
  hook_title: string;
  broad_hashtags: string[];
  stack_hashtags: string[];
  micro_api_hashtags: string[];
  pinned_code_comment: string;
  qr_code_data: string;
}

export interface WordAlignment {
  id: string;
  word: string;
  start: number;
  end: number;
  confidence: number;
  is_technical: boolean;
  raw_asr_word?: string;
  provenance_frame_time?: number;
  provenance_bbox?: [number, number, number, number];
  provenance_thumbnail_url?: string;
}

export interface ViewportKeyframe {
  timestamp: number;
  mode: LayoutMode;
  top_crop: [number, number, number, number];
  bottom_crop?: [number, number, number, number];
  transition_duration: number;
}

export interface CodeSpotlightCard {
  id: string;
  start: number;
  end: number;
  language: string;
  code: string;
  active_line_indices: number[];
  verified_by_ast: boolean;
}

export interface BrandKitConfig {
  id: string;
  name: string;
  primary_color: string;
  secondary_color: string;
  background_color: string;
  text_color: string;
  font_family: string;
  font_size_pt: number;
  logo_path?: string;
  logo_base64?: string;
  logo_position: 'top_left' | 'top_right' | 'bottom_left';
  show_provenance_badge: boolean;
  enable_intro_bumper: boolean;
  intro_bumper_duration: number;
  enable_outro_bumper: boolean;
  outro_bumper_duration: number;
  watermark_text?: string;
}

export interface ReelIR {
  schema_version: string;
  reel_id: string;
  mode: 'mode_a_extract' | 'mode_b_prompt';
  title: string;
  source_media_path?: string;
  clip_start: number;
  clip_end: number;
  total_duration: number;
  audio_path: string;
  transcript: WordAlignment[];
  viewports: ViewportKeyframe[];
  code_cards: CodeSpotlightCard[];
  redaction_boxes: RedactionBox[];
  template_archetype: TemplateArchetype;
  growth_pack?: SocialGrowthPack;
  typing_hyperlapse_intervals: [number, number][];
  brand_kit: BrandKitConfig;
  pedagogical_score: number;
  error_resolved_at?: number;
  entry_closure_verified: boolean;
  exit_closure_verified: boolean;
  technical_term_count: number;
  created_at: string;
}
