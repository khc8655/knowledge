import { Outlet } from 'react-router-dom'
import { Sidebar } from './sidebar'
import { TopBar } from './topbar'
import { useAppStore } from '@/stores/app'
import { cn } from '@/lib/utils'

export function AppShell() {
  const collapsed = useAppStore((s) => s.sidebarCollapsed)

  return (
    <div className="min-h-screen bg-background">
      <TopBar />
      <Sidebar />
      <main
        className={cn(
          'pt-[56px] transition-[margin-left] duration-200',
          collapsed ? 'ml-[64px]' : 'ml-[240px]'
        )}
      >
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
