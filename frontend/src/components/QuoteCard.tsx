import { formatMoney } from "../format";
import type { Quote } from "../types";

export function QuoteCard({ quote }: { quote: Quote }) {
  const money = (value: number) => formatMoney(value, quote.currency);
  return (
    <div className="quote">
      <div className="quote-header">
        <strong>Báo giá tạm tính · v{quote.version}</strong>
        <span>{quote.material_name}</span>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Hạng mục</th>
              <th>Khối lượng</th>
              <th>Đơn giá</th>
              <th>Thành tiền</th>
            </tr>
          </thead>
          <tbody>
            {quote.line_items.map((line) => (
              <tr key={line.code}>
                <td>{line.name}</td>
                <td>
                  {line.quantity} {line.unit}
                </td>
                <td>{money(line.unit_price)}</td>
                <td>{money(line.line_total)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="quote-total">
        <span>Tổng</span>
        <strong>{money(quote.grand_total)}</strong>
      </div>
      {quote.assumptions.length > 0 && (
        <p className="muted">Giả định: {quote.assumptions.join(" ")}</p>
      )}
    </div>
  );
}
