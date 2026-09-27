import { formatSlotValue } from "../format";
import type { ConversationStatus, SlotValue } from "../types";

export interface ConversationSnapshot {
  status: ConversationStatus;
  currentSection: string;
  completedSections: string[];
  slots: Record<string, SlotValue>;
  missingSlots: string[];
}

interface Props {
  snapshot: ConversationSnapshot | null;
  extractor: string | null;
  onReset: () => void;
}

export function StatePanel({ snapshot, extractor, onReset }: Props) {
  const slots = Object.entries(snapshot?.slots ?? {});
  return (
    <aside className="panel">
      <button type="button" onClick={onReset}>
        Tạo hội thoại mới
      </button>
      <dl>
        <dt>Extractor</dt>
        <dd>{extractor ?? "…"}</dd>
        <dt>Trạng thái</dt>
        <dd>
          <span className={`badge ${snapshot?.status ?? ""}`}>{snapshot?.status ?? "…"}</span>
        </dd>
        <dt>Section hiện tại</dt>
        <dd>
          <code>{snapshot?.currentSection ?? "…"}</code>
        </dd>
        <dt>Đã hoàn thành</dt>
        <dd>{snapshot?.completedSections.join(" → ") || "—"}</dd>
        {snapshot && snapshot.missingSlots.length > 0 && (
          <>
            <dt>Còn thiếu</dt>
            <dd>{snapshot.missingSlots.join(", ")}</dd>
          </>
        )}
      </dl>
      <h3>Memory (slots)</h3>
      {slots.length === 0 ? (
        <p className="muted">Chưa có thông tin.</p>
      ) : (
        <table className="slots">
          <tbody>
            {slots.map(([name, slot]) => (
              <tr key={name}>
                <th>{name}</th>
                <td>{formatSlotValue(slot.normalized_value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </aside>
  );
}
