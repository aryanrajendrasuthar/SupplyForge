import { useEffect, useState } from "react";
import { graphqlRequest } from "../api/graphql";
import type { StockItem } from "../types";

const QUERY = `
  query Stock {
    stock {
      warehouseCode
      sku
      quantityOnHand
      reservedQuantity
      availableQuantity
      reorderThreshold
    }
    lowStockItems {
      warehouseCode
      sku
      availableQuantity
      reorderThreshold
    }
  }
`;

export function InventoryView() {
  const [stock, setStock] = useState<StockItem[]>([]);
  const [lowStock, setLowStock] = useState<StockItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    graphqlRequest<{ stock: StockItem[]; lowStockItems: StockItem[] }>(QUERY)
      .then((data) => {
        setStock(data.stock);
        setLowStock(data.lowStockItems);
      })
      .catch((err) => setError((err as Error).message));
  }, []);

  if (error) return <p className="form-error">{error}</p>;

  return (
    <section>
      <div className="view-header">
        <h2>Inventory</h2>
      </div>

      {lowStock.length > 0 && (
        <div className="card">
          <h3>Low stock</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Warehouse</th>
                <th>SKU</th>
                <th>Available</th>
                <th>Reorder at</th>
              </tr>
            </thead>
            <tbody>
              {lowStock.map((item) => (
                <tr key={`${item.warehouseCode}-${item.sku}`}>
                  <td>{item.warehouseCode}</td>
                  <td>{item.sku}</td>
                  <td>{item.availableQuantity}</td>
                  <td>{item.reorderThreshold}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {stock.length === 0 ? (
        <p className="empty-state">No stock recorded yet.</p>
      ) : (
        <table className="data-table" style={{ marginTop: 20 }}>
          <thead>
            <tr>
              <th>Warehouse</th>
              <th>SKU</th>
              <th>On hand</th>
              <th>Reserved</th>
              <th>Available</th>
            </tr>
          </thead>
          <tbody>
            {stock.map((item) => (
              <tr key={`${item.warehouseCode}-${item.sku}`}>
                <td>{item.warehouseCode}</td>
                <td>{item.sku}</td>
                <td>{item.quantityOnHand}</td>
                <td>{item.reservedQuantity}</td>
                <td>{item.availableQuantity}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
