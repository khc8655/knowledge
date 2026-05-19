import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { useAppStore } from '@/stores/app'
import {
  Search, Upload, LayoutDashboard, Layers,
  Settings, ListOrdered, Briefcase, FileText,
} from 'lucide-react'

const navSections = [
  {
    label: '',
    items: [
      { to: '/', icon: LayoutDashboard, label: '仪表盘' },
      { to: '/search', icon: Search, label: '查询' },
      { to: '/upload', icon: Upload, label: '上传' },
      { to: '/cards', icon: Layers, label: '卡片' },
    ],
  },
  {
    label: '工作台',
    items: [
      { to: '/workspace', icon: Briefcase, label: '售前工作台' },
      { to: '/templates', icon: FileText, label: '模板' },
    ],
  },
  {
    label: '系统',
    items: [
      { to: '/indexes', icon: ListOrdered, label: '索引' },
      { to: '/settings', icon: Settings, label: '配置' },
    ],
  },
]

export function Sidebar() {
  const collapsed = useAppStore((s) => s.sidebarCollapsed)

  return (
    <aside
      className={cn(
        'fixed left-0 top-[52px] bottom-0 z-40 flex flex-col border-r bg-white transition-[width] duration-200',
        collapsed ? 'w-[56px]' : 'w-[220px]'
      )}
    >
      <nav className="flex-1 overflow-y-auto py-4 px-2">
        {navSections.map((section, si) => (
          <div key={si} className={cn(si > 0 && 'mt-5')}>
            {section.label && !collapsed && (
              <div className="px-3 mb-2 text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                {section.label}
              </div>
            )}
            <div className="flex flex-col gap-1">
              {section.items.map(({ to, icon: Icon, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === '/'}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-colors duration-200',
                      isActive
                        ? 'bg-primary/10 text-primary'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    )
                  }
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  {!collapsed && <span>{label}</span>}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      {!collapsed && (
        <div className="border-t px-3 py-3">
          <div className="text-[11px] text-muted-foreground">知识库平台</div>
          <div className="text-[11px] text-muted-foreground/60">v1.0</div>
        </div>
      )}
    </aside>
  )
}
