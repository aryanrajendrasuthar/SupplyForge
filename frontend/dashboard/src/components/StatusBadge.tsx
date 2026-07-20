const STATUS_STYLE: Record<string, { color: string; icon: string }> = {
  approved: { color: "var(--status-good)", icon: "✓" },
  confirmed: { color: "var(--status-good)", icon: "✓" },
  registered: { color: "var(--status-warning)", icon: "●" },
  pending: { color: "var(--status-warning)", icon: "●" },
  pending_validation: { color: "var(--status-warning)", icon: "●" },
  under_review: { color: "var(--status-warning)", icon: "●" },
  validated: { color: "var(--status-good)", icon: "✓" },
  rejected: { color: "var(--status-serious)", icon: "▲" },
  cancelled: { color: "var(--status-critical)", icon: "✕" },
  deactivated: { color: "var(--status-critical)", icon: "✕" },
};

// Status is always shown as icon + label, never color alone — a status
// color can look identical to a categorical series color to some viewers.
export function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLE[status] ?? { color: "var(--text-muted)", icon: "○" };
  const label = status.replace(/_/g, " ");

  return (
    <span className="status-badge" style={{ color: style.color, borderColor: style.color }}>
      <span aria-hidden="true">{style.icon}</span>
      {label}
    </span>
  );
}
