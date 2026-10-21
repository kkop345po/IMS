import { useState } from 'react'
import { Button, Card, Form, Input, Typography, App } from 'antd'
import { useNavigate } from 'react-router'
import { useLogin } from '../api/client'

export default function LoginPage() {
  const [form] = Form.useForm()
  const login = useLogin()
  const navigate = useNavigate()
  const { message } = App.useApp()

  const onFinish = async (values: { username: string; password: string }) => {
    try {
      await login.mutateAsync(values)
      message.success('登入成功')
      navigate('/stock')
    } catch (e) {
      message.error(e instanceof Error ? e.message : '登入失敗')
    }
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 120 }}>
      <Card title="庫存管理系統 — 登入" style={{ width: 380 }}>
        <Form form={form} layout="vertical" onFinish={onFinish} initialValues={{ username: 'admin', password: 'Passw0rd!' }}>
          <Form.Item label="帳號" name="username" rules={[{ required: true, message: '請輸入帳號' }]}>
            <Input autoComplete="username" placeholder="admin / warehouse / sales / manager" />
          </Form.Item>
          <Form.Item label="密碼" name="password" rules={[{ required: true, message: '請輸入密碼' }]}>
            <Input.Password autoComplete="current-password" />
          </Form.Item>
          <Button type="primary" htmlType="submit" block loading={login.isPending}>
            登入
          </Button>
          <Typography.Paragraph type="secondary" style={{ marginTop: 16, marginBottom: 0 }}>
            測試帳號：admin / warehouse / purchasing / sales / accounting / manager / viewer
            <br />
            密碼：Passw0rd!
          </Typography.Paragraph>
        </Form>
      </Card>
    </div>
  )
}
