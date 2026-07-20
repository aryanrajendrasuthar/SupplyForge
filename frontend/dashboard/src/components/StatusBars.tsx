import type { OrderStatusCount } from "../types";
import { StatusBadge } from "./StatusBadge";

const BAR_COLOR: Record<string, string> = {
  confirmed: "var(--status-good)",
  pending: "var(--status-warning)",
  cancelled: "var(--status-critical)",
};

// Magnitude comparison across a handful of states — bars, not a table,
// but colored by status (state), not by categorical series identity.
export function StatusBars({ counts }: { counts: OrderStatusCount[] }) {
  if (counts.length === 0) {
    return <p className="empty-state">No orders yet.</p>;
  }

  const max = Math.max(...counts.map((c) => c.count));

  return (
    <div className="status-bars">
      {counts.map((c) => (
        <div className="status-bar-row" key={c.status}>
          <StatusBadge status={c.status} />
          <div className="status-bar-track">
            <div
              className="status-bar-fill"
              style={{
                width: `${(c.count / max) * 100}%`,
                background: BAR_COLOR[c.status] ?? "var(--text-muted)",
              }}
            />
          </div>
          <span className="status-bar-count">{c.count}</span>
        </div>
      ))}
    </div>
  );
}
