// Mirrors the response schemas in backend/app/api/schemas.py.

export type ConversationStatus = "COLLECTING" | "QUOTED" | "NEEDS_HUMAN" | "COMPLETED";

export interface SlotValue {
  value: unknown;
  normalized_value: unknown;
  source_message: string;
  confidence: number;
  updated_at: string;
}

export interface QuoteLine {
  code: string;
  name: string;
  description: string;
  unit: string;
  quantity: string;
  unit_price: number;
  line_total: number;
}

export interface Quote {
  quote_id: string;
  material_code: string;
  material_name: string;
  line_items: QuoteLine[];
  subtotal: number;
  accessory_total: number;
  appliance_total: number;
  grand_total: number;
  currency: string;
  assumptions: string[];
  version: number;
}

export interface Asset {
  id: string;
  description: string;
  url: string;
}

export interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
  assets: Asset[];
  created_at: string;
}

export interface SessionResponse {
  session_id: string;
  status: ConversationStatus;
  current_section: string;
  completed_sections: string[];
  slots: Record<string, SlotValue>;
  missing_slots: string[];
  message_history: ConversationMessage[];
  quote: Quote | null;
}

export interface ChatResponse {
  session_id: string;
  reply: string;
  status: ConversationStatus;
  current_section: string;
  completed_sections: string[];
  collected_slots: Record<string, SlotValue>;
  missing_slots: string[];
  quote: Quote | null;
  assets: Asset[];
}

export interface HealthResponse {
  status: string;
  extractor: string;
}
