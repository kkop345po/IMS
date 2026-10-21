import { Layout, Menu, Button, Typography, Space, Select } from 'antd'
import {
  BarChartOutlined,
  LogoutOutlined,
  ShoppingCartOutlined,
  ToolOutlined,
  ShopOutlined,
  FileTextOutlined,
  ShoppingOutlined,
  SwapOutlined,
} from '@ant-design/icons'
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router'
import { useCurrentUser, useLogout } from './api/client'
import { api } from './api/client'
import { useQueryClient } from '@tanstack/react-query'
import LoginPage from './pages/Login'
import StockPage from './pages/Stock'
import ReplenishmentPage from './pages/Replenishment'
import ReportsPage from './pages/Reports'
import ItemsPage from './pages/Items'
import PurchaseOrdersPage from './pages/PurchaseOrders'
import SalesOrdersPage from './pages/SalesOrders'
import TransfersPage from './pages/Transfers'

const { Header, Content } = Layout

const DEMO_ACCOUNTS = [
  { value: 'admin', label: 'admin（管理員・全部）' },
  { value: 'warehouse', label: 'warehouse（倉管）' },
  { value: 'purchasing', label: 'purchasing（採購）' },
  { value: 'sales', label: 'sales（銷售）' },
  { value: 'accounting', label: 'accounting（會計）' },
  { value: 'manager', label: 'manager（主管）' },
  { value: 'viewer', label: 'viewer（唯讀）' },
]

export default function App() {
  const { data: user, isLoading, isError } = useCurrentUser()
  const logout = useLogout()
  const navigate = useNavigate()
  const location = useLocation()
  const qc = useQueryClient()

  if (isLoading) return null
  if (isError || !user) {
    // 未登入：任何路徑都顯示登入畫面（不要用 Navigate 導回 /login，否則登入後
    // 會被 catch-all 彈回登入頁，造成「登入成功卻沒換頁」）
    return (
      <Routes>
        <Route path="*" element={<LoginPage />} />
      </Routes>
    )
  }

  const can = (cap: string) => user.capabilities.includes(cap)

  const menuItems = [
    ...(can('item.view')
      ? [{ key: '/items', icon: <ShopOutlined />, label: <Link to="/items">商品與供應商</Link> }]
      : []),
    ...(can('stock.view')
      ? [{ key: '/stock', icon: <ToolOutlined />, label: <Link to="/stock">庫存現況</Link> }]
      : []),
    ...(can('purchase.manage')
      ? [
          {
            key: '/purchase-orders',
            icon: <FileTextOutlined />,
            label: <Link to="/purchase-orders">採購單</Link>,
          },
        ]
      : []),
    ...(can('replenishment.view')
      ? [
          {
            key: '/replenishment',
            icon: <ShoppingCartOutlined />,
            label: <Link to="/replenishment">補貨建議</Link>,
          },
        ]
      : []),
    ...(can('sales.manage')
      ? [
          {
            key: '/sales-orders',
            icon: <ShoppingOutlined />,
            label: <Link to="/sales-orders">銷售單</Link>,
          },
        ]
      : []),
    ...(can('transfer.create') || can('transfer.execute')
      ? [
          {
            key: '/transfers',
            icon: <SwapOutlined />,
            label: <Link to="/transfers">調撥單</Link>,
          },
        ]
      : []),
    ...(can('report.view')
      ? [{ key: '/reports', icon: <BarChartOutlined />, label: <Link to="/reports">業績與毛利</Link> }]
      : []),
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography.Title level={4} style={{ color: '#fff', margin: 0 }}>
          庫存管理系統
        </Typography.Title>
        <Space>
          <Select
            size="small"
            style={{ width: 210 }}
            value={user.username}
            onChange={async (v) => {
              try {
                await api.login(v, 'Passw0rd!')
                qc.invalidateQueries()
                navigate('/stock')
              } catch {
                /* 切換失敗就留在原角色 */
              }
            }}
            options={DEMO_ACCOUNTS}
          />
          <Typography.Text style={{ color: '#fff' }}>
            {user.username}（{user.role}）
          </Typography.Text>
          <Button
            icon={<LogoutOutlined />}
            onClick={() => logout.mutate(undefined, { onSuccess: () => navigate('/login') })}
          >
            登出
          </Button>
        </Space>
      </Header>
      <Layout>
        <Layout.Sider width={200} theme="light">
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            style={{ height: '100%' }}
          />
        </Layout.Sider>
        <Layout>
          <Content style={{ margin: 16 }}>
            <Routes>
              <Route path="/items" element={<ItemsPage />} />
              <Route path="/stock" element={<StockPage />} />
              <Route path="/purchase-orders" element={<PurchaseOrdersPage />} />
              <Route path="/replenishment" element={<ReplenishmentPage />} />
              <Route path="/sales-orders" element={<SalesOrdersPage />} />
              <Route path="/transfers" element={<TransfersPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="*" element={<Navigate to={menuItems[0]?.key ?? '/login'} replace />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Layout>
  )
}
