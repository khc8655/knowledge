import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { useAppStore } from '@/stores/app'
import {
  Search, Upload, LayoutDashboard, Layers,
  Settings, ListOrdered, Briefcase,
} from 'lucide-react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: '仪表盘' },
  { to: '/search', icon: Search, label: '查询' },
  { to: '/upload', icon: Upload, label: '上传' },
  { to: '/cards', icon: Layers, label: '卡片' },
  { to: '/workspace', icon: Briefcase, label: '售前工作台' },
  { to: '/indexes', icon: ListOrdered, label: '索引' },
  { to: '/settings', icon: Settings, label: '配置' },
]

export function Sidebar() {
  const collapsed = useAppStore((s) => s.sidebarCollapsed)

  return (
    <aside
      className={cn(
        'fixed left-0 top-[56px] bottom-0 z-40 flex flex-col border-r bg-surface-container-lowest transition-[width] duration-200',
        collapsed ? 'w-[64px]' : 'w-[240px]'
      )}
    >
      <nav className="flex flex-col gap-1 p-3 flex-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )
            }
          >
            <Icon className="h-5 w-5 shrink-0" />
            {!collapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
