import { useEffect, useState } from "react";
import { graphqlRequest } from "../api/graphql";
import { StatusBadge } from "../components/StatusBadge";
import type { Order } from "../types";

const LIST_QUERY = `
  query Orders {
    orders {
      id
      customerEmail
      status
      lineItems { sku warehouseCode quantity }
    }
  }
`;

const CREATE_MUTATION = `
  mutation CreateOrder($customerEmail: String!, $lineItems: [LineItemInput!]!) {
    createOrder(customerEmail: $customerEmail, lineItems: $lineItems) {
      id
    }
  }
`;

const SHIP_MUTATION = `
  mutation ShipOrder($id: Int!) {
    shipOrder(id: $id) { id status }
  }
`;

const DELIVER_MUTATION = `
  mutation DeliverOrder($id: Int!) {
    deliverOrder(id: $id) { id status }
  }
`;

export function OrdersView() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ customerEmail: "", sku: "", warehouseCode: "", quantity: "1" });
  const [submitting, setSubmitting] = useState(false);

  const load = () => {
    graphqlRequest<{ orders: Order[] }>(LIST_QUERY)
      .then((data) => setOrders(data.orders))
      .catch((err) => setError((err as Error).message));
  };

  useEffect(load, []);

  const handleShip = async (id: number) => {
    setError(null);
    try {
      await graphqlRequest(SHIP_MUTATION, { id });
      load();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleDeliver = async (id: number) => {
    setError(null);
    try {
      await graphqlRequest(DELIVER_MUTATION, { id });
      load();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await graphqlRequest(CREATE_MUTATION, {
        customerEmail: form.customerEmail,
        lineItems: [{ sku: form.sku, warehouseCode: form.warehouseCode, quantity: Number(form.quantity) }],
      });
      setForm({ customerEmail: "", sku: "", warehouseCode: "", quantity: "1" });
      load();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section>
      <div className="view-header">
        <h2>Orders</h2>
      </div>
      {orders.length === 0 ? (
        <p className="empty-state">No orders yet — create one below.</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Customer</th>
              <th>Status</th>
              <th>Line items</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.id}>
                <td>{o.id}</td>
                <td>{o.customerEmail}</td>
                <td><StatusBadge status={o.status} /></td>
                <td>{o.lineItems.map((li) => `${li.sku} ×${li.quantity} (${li.warehouseCode})`).join(", ")}</td>
                <td>
                  {o.status === "confirmed" && (
                    <button type="button" onClick={() => handleShip(o.id)}>Mark shipped</button>
                  )}
                  {o.status === "shipped" && (
                    <button type="button" onClick={() => handleDeliver(o.id)}>Mark delivered</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <form className="card" onSubmit={handleSubmit}>
        <h3>Create an order</h3>
        <div className="form-grid">
          <input
            placeholder="Customer email"
            type="email"
            value={form.customerEmail}
            onChange={(e) => setForm({ ...form, customerEmail: e.target.value })}
            required
          />
          <input
            placeholder="SKU"
            value={form.sku}
            onChange={(e) => setForm({ ...form, sku: e.target.value })}
            required
          />
          <input
            placeholder="Warehouse code"
            value={form.warehouseCode}
            onChange={(e) => setForm({ ...form, warehouseCode: e.target.value })}
            required
          />
          <input
            placeholder="Quantity"
            type="number"
            min="1"
            value={form.quantity}
            onChange={(e) => setForm({ ...form, quantity: e.target.value })}
            required
          />
        </div>
        <div className="form-actions">
          <button className="btn-primary" type="submit" disabled={submitting}>
            {submitting ? "Creating…" : "Create order"}
          </button>
          {error && <span className="form-error">{error}</span>}
        </div>
      </form>
    </section>
  );
}
