import { useEffect, useState } from "react";
import { graphqlRequest } from "../api/graphql";
import { StatTile } from "../components/StatTile";
import { StatusBars } from "../components/StatusBars";
import type { DashboardSummary } from "../types";

const QUERY = `
  query DashboardSummary {
    dashboardSummary {
      totalActiveSkus
      totalActiveSuppliers
      lowStockItemCount
      ordersByStatus { status count }
    }
  }
`;

export function DashboardView() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    graphqlRequest<{ dashboardSummary: DashboardSummary }>(QUERY)
      .then((data) => setSummary(data.dashboardSummary))
      .catch((err) => setError((err as Error).message));
  }, []);

  if (error) return <p className="form-error">{error}</p>;
  if (!summary) return <p className="empty-state">Loading…</p>;

  const totalOrders = summary.ordersByStatus.reduce((sum, s) => sum + s.count, 0);

  return (
    <section>
      <div className="view-header">
        <h2>Dashboard</h2>
      </div>
      <div className="stat-grid">
        <StatTile label="Active SKUs" value={summary.totalActiveSkus} />
        <StatTile label="Approved suppliers" value={summary.totalActiveSuppliers} />
        <StatTile label="Low-stock items" value={summary.lowStockItemCount} />
        <StatTile label="Total orders" value={totalOrders} />
      </div>
      <div className="card">
        <h3>Orders by status</h3>
        <StatusBars counts={summary.ordersByStatus} />
      </div>
    </section>
  );
}
