import { useState } from 'react'
import {
  App,
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Modal,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Row,
  Col,
} from 'antd'
import { PlusOutlined, SendOutlined, TruckOutlined } from '@ant-design/icons'
import { useQueryClient } from '@tanstack/react-query'
import { api, useCapabilities, useItems, useSalesOrders, useSalesPreview, useWarehouses } from '../api/client'
import type { PreviewLine, SalesOrderRow } from '../api/client'

const STATUS_TAG: Record<string, { color: string; text: string }> = {
  draft: { color: 'default', text: '草稿' },
  sent: { color: 'processing', text: '已送出' },
  shipped: { color: 'success', text: '已出貨' },
  cancelled: { color: 'error', text: '已取消' },
}

export default function SalesOrdersPage() {
  const { data, isLoading, refetch } = useSalesOrders()
  const { data: itemData } = useItems()
  const { data: whData } = useWarehouses()
  const qc = useQueryClient()
  const { message } = App.useApp()
  const caps = useCapabilities()
  const canSell = caps.includes('sales.manage')

  const [createOpen, setCreateOpen] = useState(false)
  const [lines, setLines] = useState<PreviewLine[]>([])
  const [form] = Form.useForm()

  const items = itemData?.items ?? []
  const warehouses = whData?.items ?? []
  const preview = useSalesPreview(lines, createOpen)

  const addLine = () => {
    setLines([...lines, { item_id: 0, warehouse_id: warehouses[0]?.id ?? 1, qty: 1 }])
  }

  const updateLine = (index: number, patch: Partial<PreviewLine>) => {
    setLines(lines.map((l, i) => (i === index ? { ...l, ...patch } : l)))
  }

  const removeLine = (index: number) => setLines(lines.filter((_, i) => i !== index))

  const createOrder = async (values: Record<string, unknown>) => {
    try {
      const res = await api.createSalesOrder({
        customer_name: values.customer_name as string,
        lines: lines.map((l) => ({
          item_id: l.item_id,
          warehouse_id: l.warehouse_id,
          qty: Number(l.qty),
          unit_price: l.unit_price,
        })),
      })
      message.success(`銷售單 ${res.so_no} 已建立`)
      setCreateOpen(false)
      setLines([])
      form.resetFields()
      qc.invalidateQueries({ queryKey: ['sales-orders'] })
    } catch (e) {
      message.error(e instanceof Error ? e.message : '建立失敗')
    }
  }

  const send = async (id: number) => {
    try {
      await api.sendSalesOrder(id)
      message.success('已送出（已建立庫存占用）')
      refetch()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '送出失敗')
    }
  }

  const ship = async (id: number) => {
    try {
      const res = await api.shipSalesOrder(id)
      message.success(`已出貨，毛利 NT$${Number(res.gross_margin).toLocaleString()}`)
      refetch()
      qc.invalidateQueries({ queryKey: ['stock'] })
      qc.invalidateQueries({ queryKey: ['sales-performance'] })
    } catch (e) {
      message.error(e instanceof Error ? e.message : '出貨失敗')
    }
  }

  const columns = [
    { title: '銷售單號', dataIndex: 'so_no', key: 'so_no', width: 130 },
    { title: '客戶', dataIndex: 'customer_name', key: 'customer_name' },
    {
      title: '品項',
      key: 'lines',
      render: (_: unknown, r: SalesOrderRow) => (
        <Space orientation="vertical" size={0}>
          {r.lines.map((l) => (
            <span key={l.id}>
              {items.find((i) => i.id === l.item_id)?.name ?? `#${l.item_id}`} ×{' '}
              {Number(l.qty).toLocaleString()}
            </span>
          ))}
        </Space>
      ),
    },
    {
      title: '金額',
      dataIndex: 'total',
      key: 'total',
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
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      render: (v: string) => <Tag color={STATUS_TAG[v]?.color}>{STATUS_TAG[v]?.text ?? v}</Tag>,
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: unknown, r: SalesOrderRow) => (
        <Space>
          {r.status === 'draft' && (
            <Button size="small" icon={<SendOutlined />} onClick={() => send(r.id)}>
              送出
            </Button>
          )}
          {r.status === 'sent' && (
            <Button size="small" type="primary" icon={<TruckOutlined />} onClick={() => ship(r.id)}>
              出貨
            </Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <Card
      title="銷售單"
      extra={
        canSell && (
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setCreateOpen(true)
              if (lines.length === 0) addLine()
            }}
          >
            新增銷售單
          </Button>
        )
      }
    >
      <Table
        rowKey="id"
        dataSource={data?.items ?? []}
        columns={columns}
        loading={isLoading}
        pagination={{ pageSize: 10 }}
        size="middle"
      />

      <Modal
        title="新增銷售單"
        open={createOpen}
        width={760}
        onCancel={() => setCreateOpen(false)}
        onOk={() => form.submit()}
        okText="建立"
      >
        <Form form={form} layout="vertical" onFinish={createOrder}>
          <Form.Item label="客戶名稱" name="customer_name">
            <Input placeholder="例：台北門市" />
          </Form.Item>
        </Form>

        <Table
          rowKey={(_, i) => String(i)}
          dataSource={lines}
          pagination={false}
          size="small"
          columns={[
            {
              title: '商品',
              key: 'item',
              render: (_: unknown, __: unknown, index: number) => (
                <Select
                  style={{ width: 220 }}
                  value={lines[index]?.item_id || undefined}
                  placeholder="選擇商品"
                  onChange={(v) => updateLine(index, { item_id: v })}
                  options={items.map((i) => ({ value: i.id, label: `${i.code} ${i.name}` }))}
                />
              ),
            },
            {
              title: '倉庫',
              key: 'wh',
              render: (_: unknown, __: unknown, index: number) => (
                <Select
                  style={{ width: 140 }}
                  value={lines[index]?.warehouse_id}
                  onChange={(v) => updateLine(index, { warehouse_id: v })}
                  options={warehouses.map((w) => ({ value: w.id, label: w.code }))}
                />
              ),
            },
            {
              title: '數量',
              key: 'qty',
              render: (_: unknown, __: unknown, index: number) => (
                <InputNumber
                  min={0}
                  value={lines[index]?.qty}
                  onChange={(v) => updateLine(index, { qty: Number(v ?? 0) })}
                />
              ),
            },
            {
              title: '可用量',
              key: 'available',
              render: (_: unknown, __: unknown, index: number) => {
                const p = preview.data?.lines?.[index]
                if (!p) return '—'
                return p.insufficient ? (
                  <Tag color="error">不足（{Number(p.available).toLocaleString()}）</Tag>
                ) : (
                  <Tag color="success">{Number(p.available).toLocaleString()}</Tag>
                )
              },
            },
            {
              title: '小計',
              key: 'amount',
              align: 'right',
              render: (_: unknown, __: unknown, index: number) => {
                const p = preview.data?.lines?.[index]
                return p ? `NT$${Number(p.amount).toLocaleString()}` : '—'
              },
            },
            {
              title: '毛利',
              key: 'margin',
              align: 'right',
              render: (_: unknown, __: unknown, index: number) => {
                const p = preview.data?.lines?.[index]
                if (!p) return '—'
                return <b>NT${Number(p.gross_margin).toLocaleString()}</b>
              },
            },
            {
              title: '',
              key: 'del',
              render: (_: unknown, __: unknown, index: number) => (
                <Button danger size="small" onClick={() => removeLine(index)}>
                  移除
                </Button>
              ),
            },
          ]}
        />
        <Button type="dashed" block onClick={addLine} style={{ marginTop: 12 }}>
          + 新增品項
        </Button>

        {preview.data && (
          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col span={6}>
              <Statistic title="應收金額" value={Number(preview.data.total)} prefix="NT$" precision={0} />
            </Col>
            <Col span={6}>
              <Statistic title="銷貨成本" value={Number(preview.data.total_cost)} prefix="NT$" precision={0} />
            </Col>
            <Col span={6}>
              <Statistic
                title="毛利"
                value={Number(preview.data.gross_margin)}
                prefix="NT$"
                precision={0}
                valueStyle={{ color: '#389e0d' }}
              />
            </Col>
            <Col span={6}>
              <Statistic title="毛利率" value={Number(preview.data.gross_margin_rate)} suffix="%" precision={2} />
            </Col>
          </Row>
        )}
      </Modal>
    </Card>
  )
}
