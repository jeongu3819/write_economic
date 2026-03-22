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
          <span className="metric-label">📰 관련 뉴스</span>
          <span className="metric-value">{ranking.related_news_count}건</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">📈 관련 종목</span>
          <span className="metric-value">{ranking.related_symbol_count}개</span>
        </div>
      </div>

      <div className="keyword-card-footer">
        {ranking.competition_level && (
          <span className={`badge badge-${ranking.competition_level}`}>
            경쟁 {ranking.competition_level === 'low' ? '낮음' : ranking.competition_level === 'medium' ? '보통' : '높음'}
          </span>
        )}
        {ranking.recommended_channel && (
          <span className={`badge badge-${ranking.recommended_channel}`}>
            {ranking.recommended_channel === 'naver' ? '네이버 추천' : ranking.recommended_channel === 'tistory' ? '티스토리 추천' : '둘 다 가능'}
          </span>
        )}
      </div>
    </div>
  )
}
