import { useState } from 'react'
import {
  App,
  Button,
  Card,
  DatePicker,
  Form,
  Input,
  InputNumber,
  Modal,
  Select,
  Table,
  Tag,
  Space,
} from 'antd'
import { PlusOutlined, SendOutlined, InboxOutlined } from '@ant-design/icons'
import { useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { api, useBins, useCapabilities, useItems, usePurchaseOrders, useSuppliers, useWarehouses } from '../api/client'
import type { PurchaseOrderRow } from '../api/client'

const STATUS_TAG: Record<string, { color: string; text: string }> = {
  draft: { color: 'default', text: '草稿' },
  sent: { color: 'processing', text: '已送出' },
  partially_received: { color: 'warning', text: '部分收貨' },
  received: { color: 'success', text: '已收貨' },
}

export default function PurchaseOrdersPage() {
  const { data, isLoading, refetch } = usePurchaseOrders()
  const { data: itemData } = useItems()
  const { data: supplierData } = useSuppliers()
  const { data: whData } = useWarehouses()
  const { data: binData } = useBins()
  const qc = useQueryClient()
  const { message } = App.useApp()
  const caps = useCapabilities()
  const canPurchase = caps.includes('purchase.manage')
  const canReceive = caps.includes('stock.receive')

  const [createOpen, setCreateOpen] = useState(false)
  const [receiveTarget, setReceiveTarget] = useState<PurchaseOrderRow | null>(null)
  const [form] = Form.useForm()
  const [receiveForm] = Form.useForm()
  // useWatch：倉庫一變，儲位選項要即時連動（getFieldValue 不會觸發重繪）
  const receiveWarehouseId = Form.useWatch('warehouse_id', receiveForm)

  const items = itemData?.items ?? []
  const suppliers = supplierData?.items ?? []
  const warehouses = whData?.items ?? []
  const bins = binData?.items ?? []

  const createOrder = async (values: Record<string, unknown>) => {
    try {
      const lines = (values.lines ?? []) as { item_id: number; qty: number; unit_price: number }[]
      const res = await api.createPurchaseOrder({
        supplier_id: values.supplier_id as number,
        expected_date: values.expected_date ? dayjs(values.expected_date as string).format('YYYY-MM-DD') : undefined,
        lines: lines.map((l) => ({
          item_id: l.item_id,
          qty: Number(l.qty),
          unit_price: Number(l.unit_price ?? 0),
        })),
      })
      message.success(`採購單 ${res.po_no} 已建立`)
      setCreateOpen(false)
      form.resetFields()
      qc.invalidateQueries({ queryKey: ['purchase-orders'] })
    } catch (e) {
      message.error(e instanceof Error ? e.message : '建立失敗')
    }
  }

  const send = async (id: number) => {
    try {
      await api.sendPurchaseOrder(id)
      message.success('已送出')
      refetch()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '送出失敗')
    }
  }

  const receive = async (values: Record<string, unknown>) => {
    if (!receiveTarget) return
    try {
      await api.receivePurchaseOrder(receiveTarget.id, values)
      message.success('入庫完成')
      setReceiveTarget(null)
      receiveForm.resetFields()
      refetch()
      qc.invalidateQueries({ queryKey: ['stock'] })
      qc.invalidateQueries({ queryKey: ['replenishment'] })
    } catch (e) {
      message.error(e instanceof Error ? e.message : '收貨失敗')
    }
  }

  const columns = [
    { title: '採購單號', dataIndex: 'po_no', key: 'po_no', width: 130 },
    {
      title: '供應商',
      dataIndex: 'supplier_id',
      key: 'supplier_id',
      render: (v: number) => suppliers.find((s) => s.id === v)?.company_name ?? `#${v}`,
    },
    {
      title: '品項',
      key: 'lines',
      render: (_: unknown, r: PurchaseOrderRow) => (
        <Space orientation="vertical" size={0}>
          {r.lines.map((l) => (
            <span key={l.id}>
              {items.find((i) => i.id === l.item_id)?.name ?? `#${l.item_id}`} ×{' '}
              {Number(l.qty).toLocaleString()}
              {Number(l.received_qty) > 0 ? `（已收 ${Number(l.received_qty).toLocaleString()}）` : ''}
            </span>
          ))}
        </Space>
      ),
    },
    {
      title: '總價',
      dataIndex: 'total',
      key: 'total',
      align: 'right' as const,
      render: (v: string) => `NT$${Number(v).toLocaleString()}`,
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
      render: (_: unknown, r: PurchaseOrderRow) => (
        <Space>
          {r.status === 'draft' && (
            <Button size="small" icon={<SendOutlined />} onClick={() => send(r.id)}>
              送出
            </Button>
          )}
          {(r.status === 'sent' || r.status === 'partially_received') && canReceive && (
            <Button
              size="small"
              type="primary"
              icon={<InboxOutlined />}
              onClick={() => {
                setReceiveTarget(r)
                receiveForm.resetFields()
              }}
            >
              收貨入庫
            </Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <Card
      title="採購單"
      extra={
        canPurchase && (
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
            新增採購單
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
        title="新增採購單"
        open={createOpen}
        width={640}
        onCancel={() => setCreateOpen(false)}
        onOk={() => form.submit()}
        okText="建立"
      >
        <Form form={form} layout="vertical" onFinish={createOrder}>
          <Form.Item label="供應商" name="supplier_id" rules={[{ required: true, message: '請選擇供應商' }]}>
            <Select
              placeholder="選擇供應商"
              options={suppliers.map((s) => ({ value: s.id, label: s.company_name }))}
            />
          </Form.Item>
          <Form.Item label="預估到貨日" name="expected_date">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.List name="lines">
            {(fields, { add, remove }) => (
              <>
                {fields.map((field) => (
                  <Space key={field.key} align="baseline" style={{ display: 'flex', marginBottom: 8 }}>
                    <Form.Item
                      {...field}
                      name={[field.name, 'item_id']}
                      rules={[{ required: true, message: '請選品項' }]}
                      style={{ marginBottom: 0 }}
                    >
                      <Select
                        style={{ width: 220 }}
                        placeholder="商品"
                        options={items.map((i) => ({ value: i.id, label: `${i.code} ${i.name}` }))}
                      />
                    </Form.Item>
                    <Form.Item
                      {...field}
                      name={[field.name, 'qty']}
                      rules={[{ required: true, message: '請填數量' }]}
                      style={{ marginBottom: 0 }}
                    >
                      <InputNumber min={0} placeholder="數量" style={{ width: 120 }} />
                    </Form.Item>
                    <Form.Item {...field} name={[field.name, 'unit_price']} style={{ marginBottom: 0 }}>
                      <InputNumber min={0} precision={2} placeholder="單價" style={{ width: 120 }} />
                    </Form.Item>
                    <Button danger size="small" onClick={() => remove(field.name)}>
                      移除
                    </Button>
                  </Space>
                ))}
                <Button type="dashed" block onClick={() => add({ qty: 1, unit_price: 0 })}>
                  + 新增品項
                </Button>
              </>
            )}
          </Form.List>
        </Form>
      </Modal>

      <Modal
        title={`收貨入庫 — ${receiveTarget?.po_no ?? ''}`}
        open={!!receiveTarget}
        onCancel={() => setReceiveTarget(null)}
        onOk={() => receiveForm.submit()}
        okText="確認入庫"
      >
        <Form form={receiveForm} layout="vertical" onFinish={receive}>
          <Form.Item
            label="品項"
            name="line_id"
            rules={[{ required: true, message: '請選擇要收貨的品項' }]}
          >
            <Select
              placeholder="選擇品項"
              options={(receiveTarget?.lines ?? []).map((l) => ({
                value: l.id,
                label: `${items.find((i) => i.id === l.item_id)?.name ?? `#${l.item_id}`}（單據 ${Number(
                  l.qty,
                ).toLocaleString()}）`,
              }))}
            />
          </Form.Item>
          <Form.Item label="實收數量" name="received_qty" rules={[{ required: true, message: '請填實收數量' }]}>
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            label="差異原因"
            name="diff_reason"
            extra="實收少於單據數量時必填（FR-8）"
          >
            <Input placeholder="例：破損 2 箱" />
          </Form.Item>
          <Form.Item label="倉庫" name="warehouse_id" rules={[{ required: true, message: '請選擇倉庫' }]}>
            <Select
              placeholder="選擇倉庫"
              options={warehouses.map((w) => ({ value: w.id, label: `${w.code} ${w.name}` }))}
              onChange={(v) => receiveForm.setFieldValue('bin_id', undefined)}
            />
          </Form.Item>
          <Form.Item label="儲位" name="bin_id" rules={[{ required: true, message: '請選擇儲位' }]}>
            <Select
              placeholder="選擇儲位"
              options={bins
                .filter((b) => b.warehouse_id === receiveWarehouseId)
                .map((b) => ({ value: b.id, label: b.code }))}
            />
          </Form.Item>
          <Form.Item label="批次碼（選填）" name="lot_code">
            <Input placeholder="例：LOT-2026-001" />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
