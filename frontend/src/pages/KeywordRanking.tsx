import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import api from '../api/client'
import KeywordCard from '../components/KeywordCard'
import WeekSelector from '../components/WeekSelector'
import type { WeeklyRun, KeywordRanking, ApiResponse } from '../types'

export default function KeywordRanking(): React.JSX.Element {
  const { weekKey } = useParams<{ weekKey: string }>()
  const [rankings, setRankings] = useState<KeywordRanking[]>([])
  const [weeks, setWeeks] = useState<string[]>([])
  const [selectedWeek, setSelectedWeek] = useState(weekKey || '')
  const [docFilter, setDocFilter] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadWeeks()
  }, [])

  useEffect(() => {
    if (selectedWeek) loadRankings()
  }, [selectedWeek, docFilter])

  const loadWeeks = async (): Promise<void> => {
    try {
      const res = await api.get<unknown, ApiResponse<WeeklyRun[]>>('/issues/weeks')
      const data = res.data || []
      const weekKeys = [...new Set(data.map((w) => w.week_key))]
      setWeeks(weekKeys)
      if (!selectedWeek && weekKeys.length > 0) {
        setSelectedWeek(weekKeys[0])
      }
    } catch (err) {
      console.error(err)
    }
  }

  const loadRankings = async (): Promise<void> => {
    setLoading(true)
    try {
      const params = docFilter ? '?min_doc_count=100000' : ''
      const res = await api.get<unknown, ApiResponse<KeywordRanking[]>>(`/keywords/${selectedWeek}/top${params}`)
      setRankings(res.data || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">키워드 랭킹</h1>
        <p className="page-subtitle">{selectedWeek} 주차 상위 키워드</p>
      </div>

      <div className="filter-bar">
        <WeekSelector
          weeks={weeks}
          selected={selectedWeek}
          onChange={setSelectedWeek}
        />

        <div className="toggle-container">
          <div
            className={`toggle ${docFilter ? 'active' : ''}`}
            onClick={() => setDocFilter(!docFilter)}
          />
          <span>문서 수 10만 이상만</span>
        </div>
      </div>

      {loading ? (
        <div className="loading-container">
          <div className="spinner" />
          <span>키워드 로딩 중...</span>
        </div>
      ) : rankings.length > 0 ? (
        <div className="keyword-grid">
          {rankings.map((k) => (
            <KeywordCard key={k.id} ranking={k} />
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">🔍</div>
          <p>해당 주차에 랭킹된 키워드가 없습니다</p>
        </div>
      )}
    </div>
  )
}
