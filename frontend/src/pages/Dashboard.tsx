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

  useEffect(() => {
    loadWeeks()
    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current)
    }
  }, [])

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
      const res = await api.post<unknown, ApiResponse<{ week_key: string; status: string }>>('/issues/collect', {})
      const weekKey = res.data?.week_key

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
            loadTopKeywords(weekKey)
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

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">대시보드</h1>
        <p className="page-subtitle">주간 이슈를 수집하고 블로그 키워드를 분석합니다</p>
      </div>

      <div style={{ marginBottom: 'var(--space-xl)', display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
        <button
          className="btn btn-primary"
          onClick={handleCollect}
          disabled={collecting}
          style={{ padding: '0.75rem 2rem', fontSize: 'var(--font-size-base)' }}
        >
          {collecting && <span className="spinner" />}
          {collecting ? '수집 중...' : '🚀 이번 주 이슈 수집'}
        </button>
        {statusMsg && <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>{statusMsg}</span>}
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
                style={{ cursor: 'pointer', padding: 'var(--space-md)', minWidth: 180 }}
                onClick={() => navigate(`/keywords/${w.week_key}`)}
              >
                <div style={{ fontWeight: 600, marginBottom: 4 }}>{w.week_key}</div>
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
            위의 "이번 주 이슈 수집" 버튼을 눌러 시작하세요
          </p>
        </div>
      )}
    </div>
  )
}
