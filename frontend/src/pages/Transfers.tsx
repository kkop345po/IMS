import { useState } from 'react'
import { App, Button, Card, Form, InputNumber, Modal, Select, Space, Table, Tag } from 'antd'
import { PlusOutlined, ExportOutlined, ImportOutlined } from '@ant-design/icons'
import { useQueryClient } from '@tanstack/react-query'
import {
  api,
  useBins,
  useCapabilities,
  useItems,
  useTransfers,
  useWarehouses,
} from '../api/client'
import type { TransferRow } from '../api/client'

const STATUS_TAG: Record<string, { color: string; text: string }> = {
  draft: { color: 'default', text: '草稿' },
  in_transit: { color: 'processing', text: '在途中' },
  received: { color: 'success', text: '已調入' },
}

export default function TransfersPage() {
  const { data, isLoading, refetch } = useTransfers()
  const { data: itemData } = useItems()
  const { data: whData } = useWarehouses()
  const { data: binData } = useBins()
  const caps = useCapabilities()
  const qc = useQueryClient()
  const { message } = App.useApp()

  const [open, setOpen] = useState(false)
  const [form] = Form.useForm()
  // useWatch：倉庫一變，儲位選項要即時連動
  const fromWarehouseId = Form.useWatch('from_warehouse_id', form)
  const toWarehouseId = Form.useWatch('to_warehouse_id', form)

  const items = itemData?.items ?? []
  const warehouses = whData?.items ?? []
  const bins = binData?.items ?? []
  const canCreate = caps.includes('transfer.create')
  const canExecute = caps.includes('transfer.execute')

  const refreshAll = () => {
    refetch()
    qc.invalidateQueries({ queryKey: ['stock'] })
    qc.invalidateQueries({ queryKey: ['replenishment'] })
  }

  const create = async (values: Record<string, unknown>) => {
    try {
      const res = await api.createTransfer({
        item_id: values.item_id as number,
        from_warehouse_id: values.from_warehouse_id as number,
        from_bin_id: values.from_bin_id as number | undefined,
        to_warehouse_id: values.to_warehouse_id as number,
        to_bin_id: values.to_bin_id as number | undefined,
        qty: Number(values.qty ?? 0),
      })
      message.success(`調撥單 ${res.transfer_no} 已建立`)
      setOpen(false)
      form.resetFields()
      refreshAll()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '建立失敗')
    }
  }

  const out = async (id: number) => {
    try {
      await api.executeTransferOut(id)
      message.success('已調出，貨物在途中（不計入任一倉可用量）')
      refreshAll()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '調出失敗')
    }
  }

  const in_ = async (id: number) => {
    try {
      await api.executeTransferIn(id)
      message.success('已調入，數量計入目標倉')
      refreshAll()
    } catch (e) {
      message.error(e instanceof Error ? e.message : '調入失敗')
    }
  }

  const columns = [
    { title: '調撥單號', dataIndex: 'transfer_no', key: 'transfer_no', width: 130 },
    {
      title: '商品',
      key: 'item',
      render: (_: unknown, r: TransferRow) => `${r.item_code ?? ''} ${r.item_name ?? ''}`,
    },
    {
      title: '數量',
      dataIndex: 'qty',
      key: 'qty',
      align: 'right' as const,
      render: (v: string) => Number(v).toLocaleString(),
    },
    {
      title: '來源 → 目標',
      key: 'route',
      render: (_: unknown, r: TransferRow) => (
        <Space>
          <Tag>WH-{String.fromCharCode(64 + r.from_warehouse_id)}</Tag>
          <span>→</span>
          <Tag color="blue">WH-{String.fromCharCode(64 + r.to_warehouse_id)}</Tag>
        </Space>
      ),
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
      render: (_: unknown, r: TransferRow) => (
        <Space>
          {r.status === 'draft' && canExecute && (
            <Button size="small" icon={<ExportOutlined />} onClick={() => out(r.id)}>
              調出
            </Button>
          )}
          {r.status === 'in_transit' && canExecute && (
            <Button size="small" type="primary" icon={<ImportOutlined />} onClick={() => in_(r.id)}>
              調入
            </Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <Card
      title="調撥單（跨倉庫）"
      extra={
        canCreate && (
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>
            新增調撥單
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
      <div style={{ marginTop: 12, color: '#888' }}>
        流程：草稿 → 調出（在途中，不計入任一倉可用量）→ 調入（計入目標倉）
      </div>

      <Modal
        title="新增調撥單"
        open={open}
        onCancel={() => setOpen(false)}
        onOk={() => form.submit()}
        okText="建立"
      >
        <Form form={form} layout="vertical" onFinish={create}>
          <Form.Item label="商品" name="item_id" rules={[{ required: true, message: '請選擇商品' }]}>
            <Select
              placeholder="選擇商品"
              options={items.map((i) => ({ value: i.id, label: `${i.code} ${i.name}` }))}
            />
          </Form.Item>
          <Form.Item
            label="來源倉庫"
            name="from_warehouse_id"
            rules={[{ required: true, message: '請選擇來源倉庫' }]}
          >
            <Select
              placeholder="選擇來源倉庫"
              options={warehouses.map((w) => ({ value: w.id, label: `${w.code} ${w.name}` }))}
              onChange={(v) => form.setFieldValue('from_bin_id', undefined)}
            />
          </Form.Item>
          <Form.Item label="來源儲位" name="from_bin_id">
            <Select
              allowClear
              placeholder="選擇儲位（可留空）"
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
              placeholder="選擇目標倉庫"
              options={warehouses.map((w) => ({ value: w.id, label: `${w.code} ${w.name}` }))}
              onChange={(v) => form.setFieldValue('to_bin_id', undefined)}
            />
          </Form.Item>
          <Form.Item label="目標儲位" name="to_bin_id">
            <Select
              allowClear
              placeholder="選擇儲位（可留空）"
              options={bins
                .filter((b) => b.warehouse_id === toWarehouseId)
                .map((b) => ({ value: b.id, label: b.code }))}
            />
          </Form.Item>
          <Form.Item label="數量" name="qty" rules={[{ required: true, message: '請輸入數量' }]}>
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
