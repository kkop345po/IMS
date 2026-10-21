import { useState } from 'react'
import { Card, Table, Tag, Input, Select, Space, Typography } from 'antd'
import { useStock } from '../api/client'
import type { StockRow } from '../api/client'

export default function StockPage() {
  const [keyword, setKeyword] = useState('')
  const [warehouseId, setWarehouseId] = useState<number | undefined>(undefined)
  const [lowOnly, setLowOnly] = useState(false)

  const { data, isLoading } = useStock({
    ...(keyword ? { q: keyword } : {}),
    ...(warehouseId ? { warehouse_id: warehouseId } : {}),
    ...(lowOnly ? { low_only: 1 } : {}),
    size: 100,
  })

  const columns = [
    { title: '商品編號', dataIndex: 'item_code', key: 'item_code' },
    { title: '商品名稱', dataIndex: 'item_name', key: 'item_name' },
    { title: '倉庫', dataIndex: 'warehouse_code', key: 'warehouse_code' },
    {
      title: '在手',
      dataIndex: 'on_hand',
      key: 'on_hand',
      align: 'right' as const,
      render: (v: string) => Number(v).toLocaleString(),
    },
    {
      title: '占用',
      dataIndex: 'reserved',
      key: 'reserved',
      align: 'right' as const,
      render: (v: string) => Number(v).toLocaleString(),
    },
    {
      title: '可用',
      dataIndex: 'available',
      key: 'available',
      align: 'right' as const,
      render: (v: string) => <b>{Number(v).toLocaleString()}</b>,
    },
    {
      title: '狀態',
      key: 'status',
      render: (_: unknown, r: StockRow) =>
        r.is_low ? <Tag color="warning">低於安全水位</Tag> : <Tag color="success">正常</Tag>,
    },
  ]

  return (
    <Card
      title="庫存現況"
      extra={
        <Space>
          <Input.Search
            placeholder="搜尋商品編號或名稱"
            allowClear
            onSearch={(v) => setKeyword(v.trim())}
            style={{ width: 220 }}
          />
          <Select
            allowClear
            placeholder="全部倉庫"
            style={{ width: 160 }}
            onChange={(v) => setWarehouseId(v)}
            options={[
              { value: 1, label: 'WH-A 總倉' },
              { value: 2, label: 'WH-B 倉北' },
              { value: 3, label: 'WH-C 倉南' },
            ]}
          />
          <Typography.Text
            strong
            onClick={() => setLowOnly((v) => !v)}
            style={{ cursor: 'pointer', color: lowOnly ? '#1677ff' : undefined }}
          >
            僅顯示需補貨
          </Typography.Text>
        </Space>
      }
    >
      <Table
        rowKey={(r) => `${r.item_id}-${r.warehouse_id}-${r.bin_id}`}
        dataSource={data?.items ?? []}
        columns={columns}
        loading={isLoading}
        pagination={{ pageSize: 20, showTotal: (t) => `共 ${t} 筆` }}
        size="middle"
      />
    </Card>
  )
}
