import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import KeywordCard from '../components/KeywordCard'
import StatusBadge from '../components/StatusBadge'
import type { WeeklyRun, KeywordRanking, ApiResponse } from '../types'

export default function Dashboard(): React.JSX.Element {
  const navigate = useNavigate()
  const [weeks, setWeeks] = useState<WeeklyRun[]>([])
  const [topKeywords, setTopKeywords] = useState<KeywordRanking[]>([])
  const [collecting, setCollecting] = useState(false)
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const [statusMsg, setStatusMsg] = useState('')
  const [weekDisplay, setWeekDisplay] = useState('')

  useEffect(() => {
    loadWeeks()
    loadWeekInfo()
    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current)
    }
  }, [])

  const loadWeekInfo = async () => {
    try {
      const res = await api.get<unknown, ApiResponse<{ week: { week_key: string; display: string } }>>('/health')
      if (res.data?.week) {
        setWeekDisplay(`${res.data.week.week_key} (${res.data.week.display})`)
      }
    } catch {
      // ignore
    }
  }

  const loadWeeks = async (): Promise<void> => {
    try {
      const res = await api.get<unknown, ApiResponse<WeeklyRun[]>>('/issues/weeks')
      const data = res.data || []
      setWeeks(data)

      const completed = data.find((w) => w.status === 'completed')
      if (completed) {
        await loadTopKeywords(completed.week_key)
      }
    } catch (err) {
      console.error('Failed to load weeks:', err)
    }
  }

  const loadTopKeywords = async (weekKey: string): Promise<void> => {
    try {
      const res = await api.get<unknown, ApiResponse<KeywordRanking[]>>(`/keywords/${weekKey}/top`)
      setTopKeywords(res.data || [])
    } catch (err) {
      console.error('Failed to load keywords:', err)
    }
  }

  const handleCollect = async (): Promise<void> => {
    setCollecting(true)
    setStatusMsg('수집 파이프라인 시작...')

    try {
      const res = await api.post<unknown, ApiResponse<{ week_key: string; status: string; display?: string }>>('/issues/collect-weekly', {})
      const weekKey = res.data?.week_key

      if (res.data?.display) {
        setWeekDisplay(`${weekKey} (${res.data.display})`)
      }

      if (res.data?.status === 'already_running') {
        setStatusMsg('이미 수집이 진행 중입니다.')
        setCollecting(false)
        return
      }

      const timer = setInterval(async () => {
        try {
          const statusRes = await api.get<unknown, ApiResponse<WeeklyRun>>(`/issues/${weekKey}/status`)
          const status = statusRes.data?.status

          if (status === 'completed') {
            clearInterval(timer)
            setCollecting(false)
            setStatusMsg('✅ 수집 및 키워드 분석 완료!')
            loadWeeks()
            if (weekKey) loadTopKeywords(weekKey)
          } else if (status === 'failed') {
            clearInterval(timer)
            setCollecting(false)
            setStatusMsg('❌ 수집 실패. 로그를 확인해주세요.')
          } else {
            setStatusMsg(`⏳ 수집 진행 중... (${statusRes.data?.total_source_count || 0}건 수집됨)`)
          }
        } catch {
          // keep polling
        }
      }, 3000)

      pollTimerRef.current = timer
    } catch (err) {
      setCollecting(false)
      setStatusMsg(`오류: ${err instanceof Error ? err.message : String(err)}`)
    }
  }

  const handleDeleteRun = async (e: React.MouseEvent, weekKey: string) => {
    e.stopPropagation()
    if (!window.confirm(`'${weekKey}' 실행 이력을 정말 삭제하시겠습니까?\n관련된 모든 데이터(수집된 뉴스, 키워드, 초안)가 함께 영구 삭제됩니다.`)) return

    try {
      const res = await api.delete<unknown, ApiResponse<{deleted: boolean}>>(`/issues/runs/${weekKey}`)
      if (res.data?.deleted || res.success) {
        setWeeks(weeks.filter(w => w.week_key !== weekKey))
        if (weekDisplay.includes(weekKey)) {
          setWeekDisplay('')
          setTopKeywords([])
        }
      } else {
        alert(res.error || '삭제 실패')
      }
    } catch (err) {
      console.error(err)
      alert('삭제 중 오류가 발생했습니다.')
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">대시보드</h1>
        <p className="page-subtitle">주간 이슈를 수집하고 블로그 키워드를 분석합니다</p>
      </div>

      {/* 현재 주차 표시 */}
      {weekDisplay && (
        <div className="week-display">
          📅 현재 수집: <strong>{weekDisplay}</strong>
        </div>
      )}

      {/* 상단 버튼 2개 */}
      <div className="dashboard-actions">
        <button
          id="collect-btn"
          className="btn btn-primary btn-lg"
          onClick={handleCollect}
          disabled={collecting}
        >
          {collecting && <span className="spinner" />}
          {collecting ? '수집 중...' : '🚀 수집/키워드 분석 시작'}
        </button>

        <button
          id="ticker-btn"
          className="btn btn-secondary btn-lg"
          onClick={() => navigate('/ticker')}
        >
          📈 티커 분석
        </button>

        {statusMsg && (
          <span className="status-msg">{statusMsg}</span>
        )}
      </div>

      {weeks.length > 0 && (
        <div style={{ marginBottom: 'var(--space-xl)' }}>
          <h2 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 600, marginBottom: 'var(--space-md)' }}>
            최근 실행 이력
          </h2>
          <div style={{ display: 'flex', gap: 'var(--space-sm)', flexWrap: 'wrap' }}>
            {weeks.slice(0, 5).map((w) => (
              <div
                key={w.id}
                className="card"
                style={{ cursor: 'pointer', padding: 'var(--space-md)', minWidth: 180, position: 'relative' }}
                onClick={() => navigate(`/keywords/${w.week_key}`)}
              >
                <div style={{ fontWeight: 600, marginBottom: 4 }}>{w.week_key}</div>
                <button
                  onClick={(e) => handleDeleteRun(e, w.week_key)}
                  style={{
                    position: 'absolute',
                    top: '8px',
                    right: '8px',
                    background: 'none',
                    border: 'none',
                    color: 'var(--color-text-muted)',
                    cursor: 'pointer',
                    fontSize: 'var(--font-size-sm)'
                  }}
                  title="실행 이력 삭제"
                >
                  ✕
                </button>
                {w.display && (
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginBottom: 4 }}>
                    {w.display}
                  </div>
                )}
                <div style={{ display: 'flex', gap: 'var(--space-sm)', alignItems: 'center' }}>
                  <StatusBadge status={w.status} />
                  <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                    {w.total_source_count}건
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {topKeywords.length > 0 && (
        <div>
          <h2 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 600, marginBottom: 'var(--space-md)' }}>
            🏆 상위 키워드 Top 10
          </h2>
          <div className="keyword-grid">
            {topKeywords.map((k) => (
              <KeywordCard key={k.id} ranking={k} />
            ))}
          </div>
        </div>
      )}

      {weeks.length === 0 && !collecting && (
        <div className="empty-state">
          <div className="empty-state-icon">📡</div>
          <p>아직 수집된 데이터가 없습니다</p>
          <p style={{ fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-sm)' }}>
            위의 "이번 주 뉴스 수집" 버튼을 눌러 시작하세요
          </p>
        </div>
      )}
    </div>
  )
}
