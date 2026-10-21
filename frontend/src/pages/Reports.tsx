import { useState } from 'react'
import { Card, Table, Select, Statistic, Row, Col, Tag, Result, Space } from 'antd'
import { useInventoryTurnover, useSalesPerformance } from '../api/client'
import type { PerformanceRow } from '../api/client'

const PERIODS = [
  { label: '本週', value: 'week' },
  { label: '本月', value: 'month' },
  { label: '本季', value: 'quarter' },
  { label: '累計', value: 'all' },
]

export default function ReportsPage() {
  const [period, setPeriod] = useState('all')
  const { data: perf, isLoading, error } = useSalesPerformance(period)
  const { data: turnover } = useInventoryTurnover(period)

  if (error) {
    const status = (error as { status?: number }).status
    return (
      <Card title="業績與毛利">
        <Result
          status={status === 403 ? '403' : '500'}
          title={status === 403 ? '此角色無權限檢視業績報表' : '資料載入失敗'}
          subTitle={
            status === 403
              ? '業績與毛利屬於管理層／會計／唯讀的權限（report.view）。請用右上角的角色切換器切換為 manager、accounting、viewer 或 admin。'
              : '請確認後端服務是否已啟動。'
          }
        />
      </Card>
    )
  }

  const columns = [
    { title: '銷貨員', dataIndex: 'username', key: 'username' },
    {
      title: '訂單數',
      dataIndex: 'order_count',
      key: 'order_count',
      align: 'right' as const,
    },
    {
      title: '成交件數',
      dataIndex: 'qty',
      key: 'qty',
      align: 'right' as const,
      render: (v: string) => Number(v).toLocaleString(),
    },
    {
      title: '銷售金額',
      dataIndex: 'sales_amount',
      key: 'sales_amount',
      align: 'right' as const,
      render: (v: string) => `NT$${Number(v).toLocaleString()}`,
    },
    {
      title: '銷貨成本',
      dataIndex: 'total_cost',
      key: 'total_cost',
      align: 'right' as const,
      render: (v: string) => `NT$${Number(v).toLocaleString()}`,
    },
    {
      title: '毛利',
      dataIndex: 'gross_margin',
      key: 'gross_margin',
      align: 'right' as const,
      render: (v: string) => <b style={{ color: '#389e0d' }}>NT${Number(v).toLocaleString()}</b>,
    },
    {
      title: '毛利率',
      dataIndex: 'gross_margin_rate',
      key: 'gross_margin_rate',
      align: 'right' as const,
      render: (v: string) => `${v}%`,
    },
  ]

  const totalMargin = (perf?.items ?? []).reduce((sum, r) => sum + Number(r.gross_margin), 0)
  const totalAmount = (perf?.items ?? []).reduce((sum, r) => sum + Number(r.sales_amount), 0)

  return (
    <Space orientation="vertical" size={16} style={{ width: '100%' }}>
      <Card
        title="業績與毛利"
        extra={
          <Select
            value={period}
            style={{ width: 120 }}
            onChange={setPeriod}
            options={PERIODS}
          />
        }
      >
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Statistic title="期間銷售金額" value={totalAmount} prefix="NT$" precision={0} />
          </Col>
          <Col span={6}>
            <Statistic title="期間毛利" value={totalMargin} prefix="NT$" precision={0} styles={{ content: { color: '#389e0d' } }} />
          </Col>
          <Col span={6}>
            <Statistic title="庫存週轉率" value={Number(turnover?.turnover ?? 0)} precision={2} />
          </Col>
          <Col span={6}>
            <Statistic title="目前庫存價值" value={Number(turnover?.stock_value ?? 0)} prefix="NT$" precision={0} />
          </Col>
        </Row>
        <Table
          rowKey={(r: PerformanceRow) => r.salesperson_id}
          dataSource={perf?.items ?? []}
          columns={columns}
          loading={isLoading}
          pagination={false}
          size="middle"
        />
        <div style={{ marginTop: 12 }}>
          <Tag color="blue">規則</Tag>
          毛利 = 應收金額 − 出庫數量 × 出庫當下成本快照（AD-4）；只計已出貨的單據
        </div>
      </Card>
    </Space>
  )
}
