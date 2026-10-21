import React from 'react'

interface Props {
  children: React.ReactNode
}

interface State {
  error: Error | null
  info: string
}

/**
 * 全域錯誤邊界：任何渲染錯誤都在畫面上顯示，而不是整頁空白。
 * 示範時若出現錯誤，評審者會直接看到原因而不是一片白。
 */
export default class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { error: null, info: '' }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    this.setState({ info: info.componentStack ?? '' })
    console.error('[ErrorBoundary]', error, info)
  }

  render() {
    const { error, info } = this.state
    if (!error) return this.props.children
    return (
      <div style={{ padding: 24, fontFamily: 'monospace' }}>
        <h2 style={{ color: '#cf1322' }}>頁面發生錯誤</h2>
        <p style={{ fontWeight: 700 }}>{error.message}</p>
        <pre style={{ whiteSpace: 'pre-wrap', color: '#555' }}>{error.stack}</pre>
        {info && <pre style={{ whiteSpace: 'pre-wrap', color: '#999' }}>{info}</pre>}
      </div>
    )
  }
}
