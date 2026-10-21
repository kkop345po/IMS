/**
 * API 客戶端（AD-9：伺服器狀態由 TanStack Query 持有，前端不自算庫存／毛利）。
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export type Role =
  | 'admin' | 'warehouse' | 'purchasing' | 'sales' | 'accounting' | 'manager' | 'viewer'

export interface CurrentUser {
  id: number
  username: string
  role: Role
  capabilities: string[]
}

export class ApiError extends Error {
  code: string
  details: Record<string, unknown>
  status: number
  constructor(status: number, code: string, message: string, details: Record<string, unknown> = {}) {
    super(message)
    this.status = status
    this.code = code
    this.details = details
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const text = await response.text()
  const data = text ? JSON.parse(text) : null
  if (!response.ok) {
    throw new ApiError(
      response.status,
      data?.code ?? 'UNKNOWN',
      data?.message ?? `請求失敗（${response.status}）`,
      data?.details ?? {},
    )
  }
  return data as T
}

export const api = {
  login: (username: string, password: string) =>
    request<CurrentUser>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  logout: () => request<{ ok: boolean }>('/auth/logout', { method: 'POST' }),
  me: () => request<CurrentUser>('/auth/me'),
  stock: (params: Record<string, string | number> = {}) => {
    const qs = new URLSearchParams(params as Record<string, string>).toString()
    return request<{ total: number; items: StockRow[] }>(`/stock${qs ? `?${qs}` : ''}`)
  },
  replenishment: (mode: 'purchase' | 'transfer' = 'purchase') =>
    request<{ items: ReplenishmentRow[] }>(`/replenishment?mode=${mode}`),
  salesPerformance: (period = 'all') =>
    request<{ period: string; items: PerformanceRow[] }>(`/reports/sales-performance?period=${period}`),
  inventoryTurnover: (period = 'all') =>
    request<{ period: string; sold_cost: string; stock_value: string; turnover: string }>(
      `/reports/inventory-turnover?period=${period}`,
    ),
  items: (q = '') =>
    request<{ total: number; items: ItemRow[] }>(`/items?q=${encodeURIComponent(q)}`),
  suppliers: () => request<{ items: SupplierRow[] }>('/suppliers'),
  warehouses: () => request<{ items: WarehouseRow[] }>('/warehouses'),
  bins: () => request<{ items: BinRow[] }>('/bins'),
  purchaseOrders: () => request<{ items: PurchaseOrderRow[] }>('/purchase-orders'),
  salesOrders: () => request<{ items: SalesOrderRow[] }>('/sales-orders'),
  salesPreview: (lines: PreviewLine[], discountType?: string, discountValue?: number) =>
    request<PreviewResult>('/sales-orders/preview', {
      method: 'POST',
      body: JSON.stringify({ lines, discount_type: discountType, discount_value: discountValue }),
    }),
  createItem: (payload: Partial<ItemRow> & { name: string; uoms?: { unit_name: string; conversion_factor: number }[] }) =>
    request<{ id: number; code: string }>('/items', { method: 'POST', body: JSON.stringify(payload) }),
  createSupplier: (payload: Partial<SupplierRow> & { tax_id: string; company_name: string }) =>
    request<{ id: number; tax_id: string }>('/suppliers', { method: 'POST', body: JSON.stringify(payload) }),
  createPurchaseOrder: (payload: { supplier_id: number; expected_date?: string; lines: PurchaseLineInput[] }) =>
    request<{ id: number; po_no: string; status: string }>('/purchase-orders', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  sendPurchaseOrder: (id: number) =>
    request<{ status: string }>(`/purchase-orders/${id}/send`, { method: 'POST' }),
  receivePurchaseOrder: (id: number, payload: Record<string, unknown>) =>
    request<{ status: string }>(`/purchase-orders/${id}/receive`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  createSalesOrder: (payload: { customer_name?: string; lines: PreviewLine[]; discount_type?: string; discount_value?: number }) =>
    request<{ id: number; so_no: string; status: string }>('/sales-orders', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  sendSalesOrder: (id: number) => request<{ status: string }>(`/sales-orders/${id}/send`, { method: 'POST' }),
  shipSalesOrder: (id: number) =>
    request<{ status: string; gross_margin: string }>(`/sales-orders/${id}/ship`, { method: 'POST' }),
  transfers: () => request<{ items: TransferRow[] }>('/transfers'),
  createTransfer: (payload: {
    item_id: number
    from_warehouse_id: number
    from_bin_id?: number
    to_warehouse_id: number
    to_bin_id?: number
    qty: number
  }) => request<{ id: number; transfer_no: string; status: string }>('/transfers', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  executeTransferOut: (id: number) =>
    request<{ status: string }>(`/transfers/${id}/out`, { method: 'POST' }),
  executeTransferIn: (id: number) =>
    request<{ status: string }>(`/transfers/${id}/receive`, { method: 'POST' }),
}

export interface StockRow {
  item_id: number
  item_code: string
  item_name: string
  warehouse_id: number
  warehouse_code: string
  bin_id: number
  on_hand: string
  reserved: string
  available: string
  min_stock: string
  max_stock: string
  is_low: boolean
}

export interface ReplenishmentRow {
  item_id: number
  code: string
  name: string
  available: string
  min_stock: string
  max_stock: string
  suggest_qty: string
  supplier_id: number | null
  unit_price: string
  estimated_total: string
}

export interface PerformanceRow {
  salesperson_id: number
  username: string
  order_count: number
  qty: string
  sales_amount: string
  total_cost: string
  gross_margin: string
  gross_margin_rate: string
}

export interface ItemRow {
  id: number
  code: string
  name: string
  category: string | null
  min_stock: string
  max_stock: string
  default_selling_price: string
}

export interface SupplierRow {
  id: number
  tax_id: string
  company_name: string
  contact_name: string | null
  phone: string | null
  is_active: boolean
}

export interface WarehouseRow {
  id: number
  code: string
  name: string
  bin_count: number
}

export interface BinRow {
  id: number
  code: string
  warehouse_id: number
  zone: string
  rack: string
}

export interface PurchaseLineInput {
  item_id: number
  qty: number
  unit_price: number
}

export interface PurchaseOrderRow {
  id: number
  po_no: string
  supplier_id: number
  status: string
  total: string
  expected_date: string | null
  lines: { id: number; item_id: number; qty: string; unit_price: string; received_qty: string }[]
}

export interface SalesOrderRow {
  id: number
  so_no: string
  customer_name: string | null
  salesperson_id: number
  status: string
  total: string
  total_cost: string
  gross_margin: string
  created_at: string
  shipped_at: string | null
  lines: {
    id: number
    item_id: number
    qty: string
    unit_price: string
    line_total: string
    unit_cost_snapshot: string | null
  }[]
}

export interface PreviewLine {
  item_id: number
  warehouse_id: number
  qty: number
  unit_price?: number
  discount_type?: string
  discount_value?: number
}

export interface PreviewLineResult {
  item_id: number
  item_code: string
  item_name: string
  available: string
  unit_price: string
  unit_cost: string
  qty: string
  amount: string
  line_cost: string
  gross_margin: string
  insufficient: boolean
}

export interface PreviewResult {
  lines: PreviewLineResult[]
  total: string
  total_cost: string
  gross_margin: string
  gross_margin_rate: string
}

export interface TransferRow {
  id: number
  transfer_no: string
  item_id: number
  item_code: string | null
  item_name: string | null
  from_warehouse_id: number
  to_warehouse_id: number
  qty: string
  status: string
  created_at: string
}

// ── React Query hooks ───────────────────────────────────────────
export function useCurrentUser() {
  return useQuery({
    queryKey: ['me'],
    queryFn: api.me,
    retry: false,
  })
}

export function useCapabilities(): string[] {
  const { data } = useCurrentUser()
  return data?.capabilities ?? []
}

export function useStock(params: Record<string, string | number> = {}) {
  return useQuery({
    queryKey: ['stock', params],
    queryFn: () => api.stock(params),
  })
}

export function useReplenishment(mode: 'purchase' | 'transfer' = 'purchase') {
  return useQuery({
    queryKey: ['replenishment', mode],
    queryFn: () => api.replenishment(mode),
  })
}

export function useSalesPerformance(period = 'all') {
  return useQuery({
    queryKey: ['sales-performance', period],
    queryFn: () => api.salesPerformance(period),
  })
}

export function useInventoryTurnover(period = 'all') {
  return useQuery({
    queryKey: ['inventory-turnover', period],
    queryFn: () => api.inventoryTurnover(period),
  })
}

export function useLogin() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) =>
      api.login(username, password),
    onSuccess: () => qc.invalidateQueries(),
  })
}

export function useLogout() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.logout,
    onSuccess: () => qc.clear(),
  })
}

export function useItems(q = '') {
  return useQuery({
    queryKey: ['items', q],
    queryFn: () => api.items(q),
  })
}

export function useSuppliers() {
  return useQuery({ queryKey: ['suppliers'], queryFn: api.suppliers })
}

export function useWarehouses() {
  return useQuery({ queryKey: ['warehouses'], queryFn: api.warehouses })
}

export function useBins() {
  return useQuery({ queryKey: ['bins'], queryFn: api.bins })
}

export function usePurchaseOrders() {
  return useQuery({ queryKey: ['purchase-orders'], queryFn: api.purchaseOrders })
}

export function useSalesOrders() {
  return useQuery({ queryKey: ['sales-orders'], queryFn: api.salesOrders })
}

export function useSalesPreview(lines: PreviewLine[], enabled: boolean) {
  return useQuery({
    queryKey: ['sales-preview', lines],
    queryFn: () => api.salesPreview(lines),
    enabled: enabled && lines.length > 0,
  })
}

export function useTransfers() {
  return useQuery({ queryKey: ['transfers'], queryFn: api.transfers })
}
