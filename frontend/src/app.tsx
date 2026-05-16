import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppShell } from '@/components/layout/app-shell'
import SearchPage from '@/pages/search'
import DashboardPage from '@/pages/dashboard'

function Placeholder({ title }: { title: string }) {
  return (
    <div>
      <h1 className="font-heading text-h1">{title}</h1>
      <p className="text-muted-foreground mt-2">页面开发中...</p>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/upload" element={<Placeholder title="上传文档" />} />
          <Route path="/cards" element={<Placeholder title="卡片管理" />} />
          <Route path="/indexes" element={<Placeholder title="索引管理" />} />
          <Route path="/settings" element={<Placeholder title="系统配置" />} />
          <Route path="/workspace" element={<Placeholder title="售前工作台" />} />
          <Route path="/templates" element={<Placeholder title="模板管理" />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
