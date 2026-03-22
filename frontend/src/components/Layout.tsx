import { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps): React.JSX.Element {
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        {children}
      </main>
    </div>
  )
}

function Sidebar(): React.JSX.Element {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        📊 EconBlog
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`} end>
          🏠 대시보드
        </NavLink>
        <NavLink to="/drafts" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          📝 저장된 초안
        </NavLink>
      </nav>

      <div className="sidebar-section-title">도움말</div>
      <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', padding: '0 var(--space-sm)' }}>
        1. 대시보드에서 이슈 수집<br/>
        2. 키워드 카드 클릭<br/>
        3. 초안 생성 & 복사
      </div>
    </aside>
  )
}
