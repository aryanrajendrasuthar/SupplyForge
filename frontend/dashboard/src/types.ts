export interface PricingTier {
  minQuantity: number;
  unitPrice: string;
}

export interface Sku {
  sku: string;
  name: string;
  description: string | null;
  category: string;
  complianceCerts: string[];
  isActive: boolean;
  pricingTiers: PricingTier[];
}

export interface StockItem {
  warehouseCode: string;
  sku: string;
  quantityOnHand: number;
  reservedQuantity: number;
  availableQuantity: number;
  reorderThreshold: number;
}

export interface Supplier {
  id: number;
  legalName: string;
  contactEmail: string;
  contactPhone: string | null;
  status: string;
}

export interface LineItem {
  sku: string;
  warehouseCode: string;
  quantity: number;
}

export interface Order {
  id: number;
  customerEmail: string;
  status: string;
  cancellationReason: string | null;
  lineItems: LineItem[];
}

export interface OrderStatusCount {
  status: string;
  count: number;
}

export interface DashboardSummary {
  totalActiveSkus: number;
  totalActiveSuppliers: number;
  lowStockItemCount: number;
  ordersByStatus: OrderStatusCount[];
}
