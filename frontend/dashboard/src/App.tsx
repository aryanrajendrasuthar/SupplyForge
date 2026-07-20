import { useState } from "react";
import { CatalogView } from "./views/CatalogView";
import { DashboardView } from "./views/DashboardView";
import { InventoryView } from "./views/InventoryView";
import { OrdersView } from "./views/OrdersView";
import { SuppliersView } from "./views/SuppliersView";

const TABS = {
  dashboard: { label: "Dashboard", view: DashboardView },
  catalog: { label: "Catalog", view: CatalogView },
  inventory: { label: "Inventory", view: InventoryView },
  orders: { label: "Orders", view: OrdersView },
  suppliers: { label: "Suppliers", view: SuppliersView },
} as const;

type TabKey = keyof typeof TABS;

function App() {
  const [activeTab, setActiveTab] = useState<TabKey>("dashboard");
  const ActiveView = TABS[activeTab].view;

  return (
    <>
      <header className="app-header">
        <h1>SupplyForge</h1>
        <nav className="tab-nav">
          {(Object.keys(TABS) as TabKey[]).map((key) => (
            <button
              key={key}
              type="button"
              aria-current={activeTab === key ? "page" : undefined}
              onClick={() => setActiveTab(key)}
            >
              {TABS[key].label}
            </button>
          ))}
        </nav>
      </header>
      <main className="app-main">
        <ActiveView />
      </main>
    </>
  );
}

export default App;
