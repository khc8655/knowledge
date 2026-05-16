import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppShell } from '@/components/layout/app-shell'
import SearchPage from '@/pages/search'
import DashboardPage from '@/pages/dashboard'
import UploadPage from '@/pages/upload'
import CardsPage from '@/pages/cards'
import IndexesPage from '@/pages/indexes'
import SettingsPage from '@/pages/settings'
import WorkspacePage from '@/pages/workspace'
import ProposalViewPage from '@/pages/proposal-view'
import TenderViewPage from '@/pages/tender-view'
import BomViewPage from '@/pages/bom-view'
import ReplyViewPage from '@/pages/reply-view'
import TemplatesPage from '@/pages/templates'
import OutputReviewPage from '@/pages/output-review'

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
          <Route path="/workspace" element={<WorkspacePage />} />
          <Route path="/proposals/:id" element={<ProposalViewPage />} />
          <Route path="/tender" element={<TenderViewPage />} />
          <Route path="/bom" element={<BomViewPage />} />
          <Route path="/reply" element={<ReplyViewPage />} />
          <Route path="/templates" element={<TemplatesPage />} />
          <Route path="/outputs/:id/review" element={<OutputReviewPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
