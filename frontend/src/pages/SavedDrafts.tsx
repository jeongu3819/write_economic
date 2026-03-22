import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import WeekSelector from '../components/WeekSelector'
import StatusBadge from '../components/StatusBadge'
import type { BlogDraft, WeeklyRun, ApiResponse } from '../types'

export default function SavedDrafts(): React.JSX.Element {
  const navigate = useNavigate()
  const [drafts, setDrafts] = useState<BlogDraft[]>([])
  const [weeks, setWeeks] = useState<string[]>([])
  const [selectedWeek, setSelectedWeek] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadWeeks()
    loadDrafts()
  }, [])

  useEffect(() => {
    loadDrafts()
  }, [selectedWeek])

  const loadWeeks = async (): Promise<void> => {
    try {
      const res = await api.get<unknown, ApiResponse<WeeklyRun[]>>('/issues/weeks')
      const data = res.data || []
      setWeeks([...new Set(data.map((w) => w.week_key))])
    } catch (err) {
      console.error(err)
    }
  }

  const loadDrafts = async (): Promise<void> => {
    setLoading(true)
    try {
      const query = selectedWeek ? `?week_key=${selectedWeek}` : ''
      const res = await api.get<unknown, ApiResponse<BlogDraft[]>>(`/drafts${query}`)
      setDrafts(res.data || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">저장된 초안</h1>
        <p className="page-subtitle">생성된 블로그 초안을 관리합니다</p>
      </div>

      <div className="filter-bar">
        <WeekSelector
          weeks={weeks}
          selected={selectedWeek}
          onChange={setSelectedWeek}
        />
        <button className="btn btn-ghost" onClick={() => setSelectedWeek('')}>
          전체 보기
        </button>
      </div>

      {loading ? (
        <div className="loading-container">
          <div className="spinner" />
        </div>
      ) : drafts.length > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
          {drafts.map((d) => (
            <div
              key={d.id}
              className="card"
              style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
              onClick={() => navigate(`/draft/${d.keyword_ranking_id || d.id}`)}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: 'var(--font-size-lg)', marginBottom: 4 }}>
                  {d.keyword}
                </div>
                <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', display: 'flex', gap: 'var(--space-md)' }}>
                  <span>{d.week_key}</span>
                  <span>{(d.title_candidates_json || [])[0] || ''}</span>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
                <StatusBadge status={d.status} />
                <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                  {d.created_at ? new Date(d.created_at).toLocaleDateString('ko-KR') : ''}
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <p>저장된 초안이 없습니다</p>
          <p style={{ fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-sm)' }}>
            키워드 카드를 클릭하여 초안을 생성해보세요
          </p>
        </div>
      )}
    </div>
  )
}
