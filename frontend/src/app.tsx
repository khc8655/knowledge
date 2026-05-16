import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppShell } from '@/components/layout/app-shell'
import SearchPage from '@/pages/search'
import DashboardPage from '@/pages/dashboard'
import UploadPage from '@/pages/upload'
import CardsPage from '@/pages/cards'
import IndexesPage from '@/pages/indexes'
import SettingsPage from '@/pages/settings'

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
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/cards" element={<CardsPage />} />
          <Route path="/indexes" element={<IndexesPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/workspace" element={<Placeholder title="售前工作台" />} />
          <Route path="/templates" element={<Placeholder title="模板管理" />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
