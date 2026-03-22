import { useNavigate } from 'react-router-dom'
import type { KeywordRanking } from '../types'

interface KeywordCardProps {
  ranking: KeywordRanking
}

export default function KeywordCard({ ranking }: KeywordCardProps): React.JSX.Element {
  const navigate = useNavigate()

  const formatNumber = (n: number): string => {
    if (n >= 10000) return `${(n / 10000).toFixed(1)}만`
    if (n >= 1000) return `${(n / 1000).toFixed(1)}천`
    return String(n)
  }

  return (
    <div
      className="card keyword-card fade-in"
      onClick={() => navigate(`/draft/${ranking.id}`)}
      style={{ animationDelay: `${((ranking.rank_no ?? 1) - 1) * 60}ms` }}
    >
      <div className="keyword-card-rank">{ranking.rank_no}</div>

      <div className="keyword-card-header">
        <div className="keyword-card-title">{ranking.keyword}</div>
        <div className="keyword-card-score">
          {Number(ranking.final_score).toFixed(0)}
        </div>
      </div>

      <div className="keyword-card-summary">
        {ranking.summary_line || '이슈 요약 없음'}
      </div>

      <div className="keyword-card-metrics">
        <div className="metric-item">
          <span className="metric-label">🔍 검색량</span>
          <span className="metric-value">{formatNumber(ranking.search_volume)}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">📄 문서 수</span>
          <span className="metric-value">{formatNumber(ranking.document_count)}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">📰 뉴스</span>
          <span className="metric-value">{ranking.related_news_count}건</span>
        </div>
      </div>

      {ranking.recommendation_reasons_json && ranking.recommendation_reasons_json.length > 0 && (
        <div style={{ marginTop: 'var(--space-md)', padding: 'var(--space-sm) 0', borderTop: '1px solid var(--color-border)' }}>
          <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-primary-dark)', marginBottom: 'var(--space-xs)' }}>
            💡 추천 사유
          </div>
          <ul style={{ margin: 0, paddingLeft: 'var(--space-md)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
            {ranking.recommendation_reasons_json.map((r, i) => (
              <li key={i} style={{ marginBottom: 2 }}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="keyword-card-footer" style={{ marginTop: 'var(--space-md)' }}>
        {ranking.keyword_type && (
          <span className={`badge`} style={{ 
            background: ranking.keyword_type === 'traffic' ? '#fff0f0' : ranking.keyword_type === 'investment' ? '#f0f4ff' : '#f0fff4',
            color: ranking.keyword_type === 'traffic' ? '#e53e3e' : ranking.keyword_type === 'investment' ? '#3182ce' : '#38a169',
            border: 'none',
            fontWeight: 600
          }}>
            {ranking.keyword_type === 'traffic' ? '🔥 트래픽형' : ranking.keyword_type === 'investment' ? '💰 투자/주식형' : '📝 블로그 제목형'}
          </span>
        )}
        {ranking.recommended_channel && (
          <span className={`badge badge-${ranking.recommended_channel}`}>
            {ranking.recommended_channel === 'naver' ? 'N 검색 추천' : ranking.recommended_channel === 'tistory' ? 'T 검색 추천' : 'N+T 동시 추천'}
          </span>
        )}
      </div>
    </div>
  )
}
