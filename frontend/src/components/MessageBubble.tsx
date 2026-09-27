import { assetUrl } from "../api";
import type { Asset, Quote } from "../types";
import { QuoteCard } from "./QuoteCard";

export interface UiMessage {
  role: "user" | "assistant";
  content: string;
  assets?: Asset[];
  quote?: Quote | null;
  error?: boolean;
}

export function MessageBubble({ message }: { message: UiMessage }) {
  return (
    <div className={`message ${message.role}${message.error ? " error" : ""}`}>
      <p>{message.content}</p>
      {message.assets?.map((asset) => (
        <figure key={asset.id}>
          <img src={assetUrl(asset.url)}alt={asset.description} loading="lazy" />
          <figcaption>{asset.description}</figcaption>
        </figure>
      ))}
      {message.quote && <QuoteCard quote={message.quote} />}
    </div>
  );
}
