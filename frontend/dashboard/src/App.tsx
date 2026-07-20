import { useState } from "react";
import type { CurrentUser } from "./api/auth";
import { logout } from "./api/auth";
import { CatalogView } from "./views/CatalogView";
import { DashboardView } from "./views/DashboardView";
import { InventoryView } from "./views/InventoryView";
import { LoginView } from "./views/LoginView";
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
  // Resets on reload — there's no session-check endpoint yet to restore this
  // from the httponly cookie, so a refresh sends you back to the login form
  // even though the cookie (and thus the ability to read/write data) is
  // still valid. A stated simplification, not a security gap.
  const [user, setUser] = useState<CurrentUser | null>(null);

  if (!user) {
    return <LoginView onLoggedIn={setUser} />;
  }

  const ActiveView = TABS[activeTab].view;

  const handleLogout = async () => {
    await logout();
    setUser(null);
  };

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
        <span style={{ marginLeft: "auto", color: "var(--text-secondary)", fontSize: 14 }}>
          {user.email} ({user.role})
        </span>
        <button type="button" onClick={handleLogout}>
          Log out
        </button>
      </header>
      <main className="app-main">
        <ActiveView />
      </main>
    </>
  );
}

export default App;
