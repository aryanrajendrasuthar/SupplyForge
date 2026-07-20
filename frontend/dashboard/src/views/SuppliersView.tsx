import { useEffect, useState } from "react";
import { graphqlRequest } from "../api/graphql";
import { StatusBadge } from "../components/StatusBadge";
import type { Supplier } from "../types";

const LIST_QUERY = `
  query Suppliers {
    suppliers {
      id
      legalName
      contactEmail
      status
    }
  }
`;

const REGISTER_MUTATION = `
  mutation RegisterSupplier($legalName: String!, $contactEmail: String!) {
    registerSupplier(legalName: $legalName, contactEmail: $contactEmail) {
      id
    }
  }
`;

export function SuppliersView() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ legalName: "", contactEmail: "" });
  const [submitting, setSubmitting] = useState(false);

  const load = () => {
    graphqlRequest<{ suppliers: Supplier[] }>(LIST_QUERY)
      .then((data) => setSuppliers(data.suppliers))
      .catch((err) => setError((err as Error).message));
  };

  useEffect(load, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await graphqlRequest(REGISTER_MUTATION, form);
      setForm({ legalName: "", contactEmail: "" });
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
        <h2>Suppliers</h2>
      </div>
      {suppliers.length === 0 ? (
        <p className="empty-state">No suppliers yet — register one below.</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Legal name</th>
              <th>Contact email</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {suppliers.map((s) => (
              <tr key={s.id}>
                <td>{s.id}</td>
                <td>{s.legalName}</td>
                <td>{s.contactEmail}</td>
                <td><StatusBadge status={s.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <form className="card" onSubmit={handleSubmit}>
        <h3>Register a supplier</h3>
        <div className="form-grid">
          <input
            placeholder="Legal name"
            value={form.legalName}
            onChange={(e) => setForm({ ...form, legalName: e.target.value })}
            required
          />
          <input
            placeholder="Contact email"
            type="email"
            value={form.contactEmail}
            onChange={(e) => setForm({ ...form, contactEmail: e.target.value })}
            required
          />
        </div>
        <div className="form-actions">
          <button className="btn-primary" type="submit" disabled={submitting}>
            {submitting ? "Registering…" : "Register supplier"}
          </button>
          {error && <span className="form-error">{error}</span>}
        </div>
      </form>
    </section>
  );
}
