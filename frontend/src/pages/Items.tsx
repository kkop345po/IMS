import { useState } from 'react'
import { Button, Card, Form, Input, InputNumber, Modal, Select, Table, Tabs, Tag, App } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { api, useCapabilities, useItems, useSuppliers } from '../api/client'
import { useQueryClient } from '@tanstack/react-query'
import type { ItemRow, SupplierRow } from '../api/client'

export default function ItemsPage() {
  const [keyword, setKeyword] = useState('')
  const { data, isLoading } = useItems(keyword)
  const { data: supplierData } = useSuppliers()
  const qc = useQueryClient()
  const { message } = App.useApp()
  const caps = useCapabilities()
  const canManageItem = caps.includes('item.manage')
  const canManageSupplier = caps.includes('supplier.manage')

  const [itemOpen, setItemOpen] = useState(false)
  const [supplierOpen, setSupplierOpen] = useState(false)
  const [itemForm] = Form.useForm()
  const [supplierForm] = Form.useForm()

  const suppliers = supplierData?.items ?? []

  const createItem = async (values: Record<string, unknown>) => {
    try {
      const payload = {
        ...values,
        default_purchase_price: Number(values.default_purchase_price ?? 0),
        default_selling_price: Number(values.default_selling_price ?? 0),
        min_stock: Number(values.min_stock ?? 0),
        max_stock: Number(values.max_stock ?? 0),
      }
      const res = await api.createItem(payload as never)
      message.success(`商品已建立（編號 ${res.code}）`)
      setItemOpen(false)
      itemForm.resetFields()
      qc.invalidateQueries({ queryKey: ['items'] })
    } catch (e) {
      message.error(e instanceof Error ? e.message : '建立失敗')
    }
  }

  const createSupplier = async (values: Record<string, unknown>) => {
    try {
      await api.createSupplier(values as never)
      message.success('供應商已建立')
      setSupplierOpen(false)
      supplierForm.resetFields()
      qc.invalidateQueries({ queryKey: ['suppliers'] })
    } catch (e) {
      message.error(e instanceof Error ? e.message : '建立失敗')
    }
  }

  const itemColumns = [
    { title: '商品編號', dataIndex: 'code', key: 'code', width: 120 },
    { title: '商品名稱', dataIndex: 'name', key: 'name' },
    { title: '分類', dataIndex: 'category', key: 'category', render: (v: string) => v ?? '—' },
    {
      title: '安全水位（最低／最高）',
      key: 'stock',
      render: (_: unknown, r: ItemRow) => `${Number(r.min_stock).toLocaleString()} / ${Number(r.max_stock).toLocaleString()}`,
    },
    {
      title: '建議售價',
      dataIndex: 'default_selling_price',
      key: 'price',
      align: 'right' as const,
      render: (v: string) => `NT$${Number(v).toLocaleString()}`,
    },
  ]

  const supplierColumns = [
    { title: '統編', dataIndex: 'tax_id', key: 'tax_id', width: 140 },
    { title: '公司名稱', dataIndex: 'company_name', key: 'company_name' },
    { title: '聯絡人', dataIndex: 'contact_name', key: 'contact_name' },
    { title: '電話', dataIndex: 'phone', key: 'phone' },
    {
      title: '狀態',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (v: boolean) => (v ? <Tag color="success">啟用</Tag> : <Tag color="default">停用</Tag>),
    },
  ]

  return (
    <Card
      title="商品與供應商主檔"
      extra={
        <Input.Search
          placeholder="搜尋商品編號或名稱"
          allowClear
          style={{ width: 240 }}
          onSearch={(v) => setKeyword(v.trim())}
        />
      }
    >
      <Tabs
        items={[
          {
            key: 'items',
            label: `商品（${data?.total ?? 0}）`,
            children: (
              <>
                {canManageItem && (
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => setItemOpen(true)}
                    style={{ marginBottom: 12 }}
                  >
                    新增商品
                  </Button>
                )}
                <Table
                  rowKey="id"
                  dataSource={data?.items ?? []}
                  columns={itemColumns}
                  loading={isLoading}
                  pagination={{ pageSize: 10 }}
                  size="middle"
                />
              </>
            ),
          },
          {
            key: 'suppliers',
            label: `供應商（${suppliers.length}）`,
            children: (
              <>
                {canManageSupplier && (
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => setSupplierOpen(true)}
                    style={{ marginBottom: 12 }}
                  >
                    新增供應商
                  </Button>
                )}
                <Table
                  rowKey="id"
                  dataSource={suppliers}
                  columns={supplierColumns}
                  pagination={{ pageSize: 10 }}
                  size="middle"
                />
              </>
            ),
          },
        ]}
      />

      <Modal
        title="新增商品"
        open={itemOpen}
        onCancel={() => setItemOpen(false)}
        onOk={() => itemForm.submit()}
        okText="建立"
      >
        <Form form={itemForm} layout="vertical" onFinish={createItem}>
          <Form.Item label="商品名稱" name="name" rules={[{ required: true, message: '請輸入商品名稱' }]}>
            <Input placeholder="例：碳酸飲料 500ml" />
          </Form.Item>
          <Form.Item label="分類" name="category">
            <Input placeholder="例：飲料" />
          </Form.Item>
          <Form.Item label="供應商" name="supplier_id">
            <Select
              allowClear
              placeholder="選擇供應商"
              options={suppliers.map((s: SupplierRow) => ({ value: s.id, label: s.company_name }))}
            />
          </Form.Item>
          <Form.Item label="預設採購單價" name="default_purchase_price">
            <InputNumber min={0} precision={2} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="建議售價" name="default_selling_price">
            <InputNumber min={0} precision={2} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="安全水位最低值" name="min_stock" extra="低於此值會出現在補貨建議">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="安全水位最高值" name="max_stock" extra="補貨建議以此值為目標">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="基本單位" name="uom_base" initialValue="個">
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="新增供應商"
        open={supplierOpen}
        onCancel={() => setSupplierOpen(false)}
        onOk={() => supplierForm.submit()}
        okText="建立"
      >
        <Form form={supplierForm} layout="vertical" onFinish={createSupplier}>
          <Form.Item label="統編" name="tax_id" rules={[{ required: true, message: '請輸入統編' }]}>
            <Input placeholder="例：12345678" />
          </Form.Item>
          <Form.Item
            label="公司名稱"
            name="company_name"
            rules={[{ required: true, message: '請輸入公司名稱' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item label="聯絡人" name="contact_name">
            <Input />
          </Form.Item>
          <Form.Item label="電話" name="phone">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
