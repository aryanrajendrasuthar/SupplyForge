import { useEffect, useState } from "react";
import { graphqlRequest } from "../api/graphql";
import type { Sku } from "../types";

const LIST_QUERY = `
  query Skus {
    skus {
      sku
      name
      category
      pricingTiers { minQuantity unitPrice }
    }
  }
`;

const CREATE_MUTATION = `
  mutation CreateSku($sku: String!, $name: String!, $category: String!) {
    createSku(sku: $sku, name: $name, category: $category) {
      sku
    }
  }
`;

export function CatalogView() {
  const [skus, setSkus] = useState<Sku[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ sku: "", name: "", category: "" });
  const [submitting, setSubmitting] = useState(false);

  const load = () => {
    graphqlRequest<{ skus: Sku[] }>(LIST_QUERY)
      .then((data) => setSkus(data.skus))
      .catch((err) => setError((err as Error).message));
  };

  useEffect(load, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await graphqlRequest(CREATE_MUTATION, form);
      setForm({ sku: "", name: "", category: "" });
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
        <h2>Catalog</h2>
      </div>
      {skus.length === 0 ? (
        <p className="empty-state">No SKUs yet — add one below.</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>SKU</th>
              <th>Name</th>
              <th>Category</th>
              <th>Base price</th>
            </tr>
          </thead>
          <tbody>
            {skus.map((s) => (
              <tr key={s.sku}>
                <td>{s.sku}</td>
                <td>{s.name}</td>
                <td>{s.category}</td>
                <td>{s.pricingTiers[0]?.unitPrice ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <form className="card" onSubmit={handleSubmit}>
        <h3>Add a SKU</h3>
        <div className="form-grid">
          <input
            placeholder="SKU code"
            value={form.sku}
            onChange={(e) => setForm({ ...form, sku: e.target.value })}
            required
          />
          <input
            placeholder="Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
          <input
            placeholder="Category"
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
            required
          />
        </div>
        <div className="form-actions">
          <button className="btn-primary" type="submit" disabled={submitting}>
            {submitting ? "Adding…" : "Add SKU"}
          </button>
          {error && <span className="form-error">{error}</span>}
        </div>
      </form>
    </section>
  );
}
