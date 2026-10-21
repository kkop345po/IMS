import { useState } from 'react'
import { App, Button, Card, DatePicker, Form, InputNumber, Modal, Select, Space, Table, Tag, Checkbox } from 'antd'
import { ThunderboltOutlined, SwapOutlined } from '@ant-design/icons'
import { useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import {
  api,
  useBins,
  useCapabilities,
  useReplenishment,
  useSuppliers,
  useWarehouses,
} from '../api/client'
import type { ReplenishmentRow } from '../api/client'

export default function ReplenishmentPage() {
  const [mode, setMode] = useState<'purchase' | 'transfer'>('purchase')
  const { data, isLoading, refetch } = useReplenishment(mode)
  const { data: supplierData } = useSuppliers()
  const { data: whData } = useWarehouses()
  const { data: binData } = useBins()
  const caps = useCapabilities()
  const qc = useQueryClient()
  const { message } = App.useApp()

  const [selected, setSelected] = useState<ReplenishmentRow[]>([])
  const [poOpen, setPoOpen] = useState(false)
  const [toOpen, setToOpen] = useState(false)
  const [poForm] = Form.useForm()
  const [toForm] = Form.useForm()
  // useWatch：倉庫一變，儲位選項要即時連動
  const fromWarehouseId = Form.useWatch('from_warehouse_id', toForm)
  const toWarehouseId = Form.useWatch('to_warehouse_id', toForm)

  const suppliers = supplierData?.items ?? []
  const warehouses = whData?.items ?? []
  const bins = binData?.items ?? []
  const canPurchase = caps.includes('purchase.manage')
  const canTransfer = caps.includes('transfer.create')

  const refresh = () => {
    refetch()
    qc.invalidateQueries({ queryKey: ['purchase-orders'] })
    qc.invalidateQueries({ queryKey: ['transfers'] })
  }

  const toPurchaseOrder = async (values: Record<string, unknown>) => {
    try {
      const res = await api.createPurchaseOrder({
        supplier_id: values.supplier_id as number,
        expected_date: values.expected_date ? dayjs(values.expected_date as string).format('YYYY-MM-DD') : undefined,
        lines: selected.map((s) => ({
          item_id: s.item_id,
          qty: Number(s.suggest_qty),
          unit_price: Number(s.unit_price),
        })),
      })
      message.success(`採購單 ${res.po_no} 已建立，可到「採購單」送出並收貨入庫`)
      setPoOpen(false)
      setSelected([])
      poForm.resetFields()
      refresh()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '轉單失敗')
    }
  }

  const toTransfer = async (values: Record<string, unknown>) => {
    const row = selected[0]
    if (!row) return
    try {
      const res = await api.createTransfer({
        item_id: row.item_id,
        from_warehouse_id: values.from_warehouse_id as number,
        from_bin_id: values.from_bin_id as number | undefined,
        to_warehouse_id: values.to_warehouse_id as number,
        to_bin_id: values.to_bin_id as number | undefined,
        qty: Number(values.qty ?? row.suggest_qty),
      })
      message.success(`調撥單 ${res.transfer_no} 已建立，請到「調撥單」執行調出／調入`)
      setToOpen(false)
      setSelected([])
      toForm.resetFields()
      refresh()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '建立調撥單失敗')
    }
  }

  const purchaseColumns = [
    { title: '商品編號', dataIndex: 'code', key: 'code', width: 110 },
    { title: '商品名稱', dataIndex: 'name', key: 'name' },
    {
      title: '目前可用',
      dataIndex: 'available',
      key: 'available',
      align: 'right' as const,
      render: (v: string) => Number(v).toLocaleString(),
    },
    {
      title: '安全水位（最低）',
      dataIndex: 'min_stock',
      key: 'min_stock',
      align: 'right' as const,
    },
    {
      title: '建議補貨量',
      dataIndex: 'suggest_qty',
      key: 'suggest_qty',
      align: 'right' as const,
      render: (v: string) => <b style={{ color: '#cf1322' }}>{Number(v).toLocaleString()}</b>,
    },
    {
      title: '參考單價',
      dataIndex: 'unit_price',
      key: 'unit_price',
      align: 'right' as const,
      render: (v: string) => `NT$${Number(v).toLocaleString()}`,
    },
    {
      title: '預估總價',
      dataIndex: 'estimated_total',
      key: 'estimated_total',
      align: 'right' as const,
      render: (v: string) => `NT$${Number(v).toLocaleString()}`,
    },
  ]

  const transferColumns = [
    { title: '商品編號', dataIndex: 'code', key: 'code', width: 110 },
    { title: '商品名稱', dataIndex: 'name', key: 'name' },
    {
      title: '來源倉庫',
      dataIndex: 'from_warehouse_id',
      key: 'from_warehouse_id',
      render: (v: number) => warehouses.find((w) => w.id === v)?.code ?? `WH-${v}`,
    },
    {
      title: '可調撥量',
      dataIndex: 'transferable_qty',
      key: 'transferable_qty',
      align: 'right' as const,
      render: (v: string) => Number(v).toLocaleString(),
    },
    {
      title: '建議量',
      dataIndex: 'suggest_qty',
      key: 'suggest_qty',
      align: 'right' as const,
    },
  ]

  return (
    <Card
      title="補貨建議"
      extra={
        <Space>
          {mode === 'purchase' && (
            <>
              <Space orientation="vertical" size={0}>
                <Button
                  type="primary"
                  icon={<ThunderboltOutlined />}
                  disabled={selected.length === 0 || !canPurchase}
                  onClick={() => {
                    poForm.setFieldValue(
                      'supplier_id',
                      selected[0]?.supplier_id ?? suppliers[0]?.id,
                    )
                    poForm.setFieldValue('expected_date', dayjs().add(7, 'day'))
                    setPoOpen(true)
                  }}
                >
                  轉採購單{selected.length > 0 ? `（${selected.length}）` : ''}
                </Button>
                <span style={{ fontSize: 12, color: '#999' }}>勾選左側品項</span>
              </Space>
            </>
          )}
          {mode === 'transfer' && (
            <Button
              type="primary"
              icon={<SwapOutlined />}
              disabled={selected.length !== 1 || !canTransfer}
              onClick={() => {
                toForm.setFieldValue('qty', Number(selected[0]?.suggest_qty ?? 0))
                setToOpen(true)
              }}
            >
              轉調撥單
            </Button>
          )}
          <Space.Compact>
            <Button
              type={mode === 'purchase' ? 'primary' : 'default'}
              onClick={() => {
                setMode('purchase')
                setSelected([])
              }}
            >
              採購建議
            </Button>
            <Button
              type={mode === 'transfer' ? 'primary' : 'default'}
              onClick={() => {
                setMode('transfer')
                setSelected([])
              }}
            >
              跨倉調撥建議
            </Button>
          </Space.Compact>
        </Space>
      }
    >
      <Table
        rowKey={(r: ReplenishmentRow & { from_warehouse_id?: number }) =>
          `${r.item_id}-${'from_warehouse_id' in r ? r.from_warehouse_id : 0}`
        }
        dataSource={data?.items ?? []}
        columns={mode === 'purchase' ? purchaseColumns : transferColumns}
        loading={isLoading}
        locale={{ emptyText: '目前沒有需要補貨的品項' }}
        pagination={false}
        size="middle"
        rowSelection={{
          selectedRowKeys: selected.map((s) => `${s.item_id}`),
          onChange: (_keys, rows) => setSelected(rows as ReplenishmentRow[]),
        }}
      />
      <div style={{ marginTop: 16 }}>
        <Tag color="blue">規則</Tag>
        可用量 &lt; 安全水位最低值 → 建議補貨量 = 安全水位最高值 − 可用量（即時計算，不排程）
      </div>

      <Modal
        title={`轉採購單（${selected.length} 項）`}
        open={poOpen}
        onCancel={() => setPoOpen(false)}
        onOk={() => poForm.submit()}
        okText="建立採購單"
      >
        <Form form={poForm} layout="vertical" onFinish={toPurchaseOrder}>
          <Form.Item label="供應商" name="supplier_id" rules={[{ required: true, message: '請選擇供應商' }]}>
            <Select
              options={suppliers.map((s) => ({ value: s.id, label: s.company_name }))}
              placeholder="選擇供應商"
            />
          </Form.Item>
          <Form.Item label="預估到貨日" name="expected_date">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Table
            rowKey={(r: ReplenishmentRow) => String(r.item_id)}
            dataSource={selected}
            pagination={false}
            size="small"
            columns={[
              { title: '商品', dataIndex: 'name', key: 'name' },
              {
                title: '數量',
                dataIndex: 'suggest_qty',
                key: 'qty',
                align: 'right',
                render: (v: string) => Number(v).toLocaleString(),
              },
              {
                title: '小計',
                key: 'sub',
                align: 'right',
                render: (_: unknown, r: ReplenishmentRow) =>
                  `NT$${(Number(r.suggest_qty) * Number(r.unit_price)).toLocaleString()}`,
              },
            ]}
          />
        </Form>
      </Modal>

      <Modal
        title="轉調撥單"
        open={toOpen}
        onCancel={() => setToOpen(false)}
        onOk={() => toForm.submit()}
        okText="建立調撥單"
      >
        <Form form={toForm} layout="vertical" onFinish={toTransfer}>
          <Form.Item label="商品">
            <InputNumber value={selected[0]?.name} readOnly style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            label="來源倉庫"
            name="from_warehouse_id"
            rules={[{ required: true, message: '請選擇來源倉庫' }]}
          >
            <Select
              options={warehouses.map((w) => ({ value: w.id, label: `${w.code} ${w.name}` }))}
              onChange={(v) => toForm.setFieldValue('from_bin_id', undefined)}
            />
          </Form.Item>
          <Form.Item label="來源儲位" name="from_bin_id">
            <Select
              allowClear
              options={bins
                .filter((b) => b.warehouse_id === fromWarehouseId)
                .map((b) => ({ value: b.id, label: b.code }))}
            />
          </Form.Item>
          <Form.Item
            label="目標倉庫"
            name="to_warehouse_id"
            rules={[{ required: true, message: '請選擇目標倉庫' }]}
          >
            <Select
              options={warehouses.map((w) => ({ value: w.id, label: `${w.code} ${w.name}` }))}
              onChange={(v) => toForm.setFieldValue('to_bin_id', undefined)}
            />
          </Form.Item>
          <Form.Item label="目標儲位" name="to_bin_id">
            <Select
              allowClear
              options={bins
                .filter((b) => b.warehouse_id === toWarehouseId)
                .map((b) => ({ value: b.id, label: b.code }))}
            />
          </Form.Item>
          <Form.Item label="調撥數量" name="qty" rules={[{ required: true, message: '請輸入數量' }]}>
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
