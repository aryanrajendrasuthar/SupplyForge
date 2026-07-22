import { useEffect, useState } from "react";
import { graphqlRequest } from "../api/graphql";
import type { Sku } from "../types";

const LIST_QUERY = `
  query Skus {
    skus {
      sku
      name
      category
      imageUrl
      technicalSpecs { key value }
      pricingTiers { minQuantity unitPrice }
    }
  }
`;

const CREATE_MUTATION = `
  mutation CreateSku($sku: String!, $name: String!, $category: String!, $imageUrl: String) {
    createSku(sku: $sku, name: $name, category: $category, imageUrl: $imageUrl) {
      sku
    }
  }
`;

export function CatalogView() {
  const [skus, setSkus] = useState<Sku[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ sku: "", name: "", category: "", imageUrl: "" });
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
      await graphqlRequest(CREATE_MUTATION, { ...form, imageUrl: form.imageUrl || null });
      setForm({ sku: "", name: "", category: "", imageUrl: "" });
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
              <th>Image</th>
              <th>SKU</th>
              <th>Name</th>
              <th>Category</th>
              <th>Base price</th>
              <th>Specs</th>
            </tr>
          </thead>
          <tbody>
            {skus.map((s) => (
              <tr key={s.sku}>
                <td>
                  {s.imageUrl ? (
                    <img src={s.imageUrl} alt={s.name} style={{ width: 32, height: 32, objectFit: "cover", borderRadius: 4 }} />
                  ) : (
                    "—"
                  )}
                </td>
                <td>{s.sku}</td>
                <td>{s.name}</td>
                <td>{s.category}</td>
                <td>{s.pricingTiers[0]?.unitPrice ?? "—"}</td>
                <td>
                  {s.technicalSpecs.length > 0
                    ? s.technicalSpecs.map((spec) => `${spec.key}: ${spec.value}`).join(", ")
                    : "—"}
                </td>
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
          <input
            placeholder="Image URL (optional)"
            value={form.imageUrl}
            onChange={(e) => setForm({ ...form, imageUrl: e.target.value })}
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
