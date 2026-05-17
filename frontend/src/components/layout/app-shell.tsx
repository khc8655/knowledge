import { Outlet } from 'react-router-dom'
import { TopBar } from './topbar'

export function AppShell() {
  return (
    <div className="min-h-screen bg-background">
      <TopBar />
      <main className="pt-[48px]">
        <Outlet />
      </main>
    </div>
  )
}
