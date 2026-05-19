import { Outlet } from 'react-router-dom'
import { TopBar } from './topbar'

export function AppShell() {
  return (
    <div className="min-h-screen bg-background">
      <div className="fixed inset-0 bg-gradient-to-br from-[#f0f7fa] via-background to-[#f0f4f8] -z-10" />
      <TopBar />
      <main className="pt-[52px]">
        <Outlet />
      </main>
    </div>
  )
}
