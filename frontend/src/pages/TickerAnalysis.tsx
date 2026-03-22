import { useState, useEffect } from 'react'
import api from '../api/client'
import CopyButton from '../components/CopyButton'
import type {
  TickerAnalysis,
  TickerBlogResult,
  ModelInfo,
  ModelsData,
  ApiResponse,
} from '../types'

export default function TickerAnalysisPage(): React.JSX.Element {
  const [ticker, setTicker] = useState('')
  const [models, setModels] = useState<ModelInfo[]>([])
  const [selectedModel, setSelectedModel] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [result, setResult] = useState<TickerAnalysis | null>(null)
  const [blogResult, setBlogResult] = useState<TickerBlogResult | null>(null)
  const [blogGenerating, setBlogGenerating] = useState(false)
  const [error, setError] = useState('')
  const [activeBlogTab, setActiveBlogTab] = useState<'naver' | 'tistory'>('naver')

  useEffect(() => {
    loadModels()
  }, [])

  const loadModels = async () => {
    try {
      const res = await api.get<unknown, ApiResponse<ModelsData>>('/models')
      if (res.data) {
        setModels(res.data.models || [])
        setSelectedModel(res.data.default_model || 'gpt-4o')
      }
    } catch {
      setModels([{ id: 'gpt-4o', owned_by: 'openai' }])
      setSelectedModel('gpt-4o')
    }
  }

  const handleAnalyze = async () => {
    if (!ticker.trim()) return
    setAnalyzing(true)
    setError('')
    setResult(null)
    setBlogResult(null)

    try {
      const res = await api.post<unknown, ApiResponse<TickerAnalysis>>('/ticker/analyze', {
        ticker: ticker.trim().toUpperCase(),
        model: selectedModel || undefined,
      })
      if (res.success && res.data) {
        setResult(res.data)
      } else {
        setError(res.error || '분석에 실패했습니다.')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '분석 중 오류가 발생했습니다.')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleBlogify = async () => {
    if (!result) return
    setBlogGenerating(true)

    try {
      const res = await api.post<unknown, ApiResponse<TickerBlogResult>>('/ticker/blogify', {
        ticker: result.ticker,
        analysis_data: result,
        platform: activeBlogTab,
        model: selectedModel || undefined,
      })
      if (res.success && res.data) {
        setBlogResult(res.data)
      }
    } catch (err) {
      console.error('Blog generation failed:', err)
    } finally {
      setBlogGenerating(false)
    }
  }

  const getSentimentBadge = (sentiment: string) => {
    const map: Record<string, { cls: string; emoji: string }> = {
      '긍정': { cls: 'badge-positive', emoji: '🟢' },
      '부정': { cls: 'badge-negative', emoji: '🔴' },
      '중립': { cls: 'badge-neutral', emoji: '🟡' },
    }
    const s = map[sentiment] || map['중립']
    return <span className={`badge ${s.cls}`}>{s.emoji} {sentiment}</span>
  }

  const getFullAnalysisText = (): string => {
    if (!result) return ''
    let text = `📊 ${result.ticker} 분석 결과\n\n`
    text += `🏢 기업개요\n${result.company_overview || '정보 없음'}\n\n`
    text += `📰 최신 뉴스\n`
    result.news.forEach((n, i) => {
      text += `${i + 1}. ${n.title}\n   ${n.link}\n   ${n.relative_time || n.date}\n   ${n.summary}\n\n`
    })
    text += `📋 최신 공시\n`
    result.filings.forEach((f, i) => {
      text += `${i + 1}. ${f.title}\n   ${f.link}\n   ${f.relative_time || f.date}\n   ${f.summary}\n\n`
    })
    text += `📉 공매도 비율: ${result.short_interest}\n\n`
    text += `💡 트레이더 해석: ${result.trader_sentiment}\n${result.trader_interpretation}\n`
    return text
  }

  const getBlogFullText = (): string => {
    if (!blogResult) return ''
    let text = blogResult.titles[0] || ''
    text += '\n\n' + (blogResult.intros[0] || '')
    text += '\n\n' + blogResult.body
    text += '\n\n핵심 요약: ' + blogResult.summary
    text += '\n\n' + blogResult.hashtags.map(h => `#${h}`).join(' ')
    text += '\n\n' + blogResult.caution
    return text
  }

  return (
    <div className="ticker-page">
      <div className="page-header">
        <h1 className="page-title">📈 티커 분석</h1>
        <p className="page-subtitle">종목 티커를 입력하면 기업개요, 뉴스, 공시, 공매도, 트레이더 해석을 한눈에 확인합니다</p>
      </div>

      {/* 입력 영역 */}
      <div className="ticker-input-area">
        <div className="ticker-input-row">
          <input
            id="ticker-input"
            type="text"
            className="ticker-input"
            placeholder="티커 입력 (예: NVDA, AAPL, TSLA)"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
            disabled={analyzing}
          />

          <select
            id="model-select"
            className="model-select"
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            disabled={analyzing}
          >
            {models.map((m) => (
              <option key={m.id} value={m.id}>{m.id}</option>
            ))}
          </select>

          <button
            id="analyze-btn"
            className="btn btn-primary"
            onClick={handleAnalyze}
            disabled={analyzing || !ticker.trim()}
          >
            {analyzing && <span className="spinner" />}
            {analyzing ? '분석 중...' : '🔍 분석 실행'}
          </button>
        </div>
      </div>

      {/* 에러 */}
      {error && (
        <div className="ticker-error fade-in">
          ⚠️ {error}
        </div>
      )}

      {/* 로딩 */}
      {analyzing && (
        <div className="loading-container">
          <div className="spinner" style={{ width: 40, height: 40 }} />
          <span>StockTitan에서 데이터를 수집하고 AI 해석을 생성하고 있습니다...</span>
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>약 10~30초 소요</span>
        </div>
      )}

      {/* 결과 */}
      {result && !analyzing && (
        <div className="ticker-result fade-in">
          {/* 헤더 */}
          <div className="ticker-result-header">
            <div>
              <h2 className="ticker-result-title">{result.ticker}</h2>
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                {result.model_used} · {new Date(result.analyzed_at).toLocaleString('ko-KR')}
              </span>
            </div>
            <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
              <CopyButton text={getFullAnalysisText()} label="전체 복사" />
            </div>
          </div>

          {/* 기업개요 */}
          <div className="ticker-section">
            <h3 className="ticker-section-title">🏢 기업개요</h3>
            <p className="ticker-section-body">{result.company_overview || '기업개요 정보를 불러올 수 없습니다.'}</p>
          </div>

          {/* 최신 뉴스 */}
          <div className="ticker-section">
            <h3 className="ticker-section-title">📰 최신 뉴스 ({result.news.length}건)</h3>
            {result.news.length > 0 ? (
              <div className="ticker-items-list">
                {result.news.map((n, i) => (
                  <div key={i} className="ticker-item-card">
                    <div className="ticker-item-header">
                      <span className="ticker-item-badge badge-news">뉴스</span>
                      <span className="ticker-item-time">{n.relative_time || n.date || '시간 정보 없음'}</span>
                    </div>
                    <a href={n.link} target="_blank" rel="noopener noreferrer" className="ticker-item-title">
                      {n.title}
                    </a>
                    {n.summary && <p className="ticker-item-summary">{n.summary}</p>}
                  </div>
                ))}
              </div>
            ) : (
              <p className="ticker-empty-text">수집된 뉴스가 없습니다.</p>
            )}
          </div>

          {/* 최신 공시 */}
          <div className="ticker-section">
            <h3 className="ticker-section-title">📋 최신 공시 ({result.filings.length}건)</h3>
            {result.filings.length > 0 ? (
              <div className="ticker-items-list">
                {result.filings.map((f, i) => (
                  <div key={i} className="ticker-item-card">
                    <div className="ticker-item-header">
                      <span className="ticker-item-badge badge-filing">공시</span>
                      <span className="ticker-item-time">{f.relative_time || f.date || '시간 정보 없음'}</span>
                    </div>
                    <a href={f.link} target="_blank" rel="noopener noreferrer" className="ticker-item-title">
                      {f.title}
                    </a>
                    {f.summary && <p className="ticker-item-summary">{f.summary}</p>}
                  </div>
                ))}
              </div>
            ) : (
              <p className="ticker-empty-text">수집된 공시가 없습니다.</p>
            )}
          </div>

          {/* 공매도 비율 */}
          <div className="ticker-section">
            <h3 className="ticker-section-title">📉 공매도 비율</h3>
            <div className="ticker-short-interest">
              <span className="short-value">{result.short_interest}</span>
              {result.short_interest_pct && (
                <span className="short-pct">({result.short_interest_pct} of Float)</span>
              )}
            </div>
          </div>

          {/* 트레이더 해석 */}
          <div className="ticker-section">
            <h3 className="ticker-section-title">💡 트레이더 해석</h3>
            <div className="ticker-trader">
              {getSentimentBadge(result.trader_sentiment)}
              <p className="ticker-trader-text">{result.trader_interpretation}</p>
            </div>
          </div>

          {/* 관련 링크 */}
          <div className="ticker-section">
            <h3 className="ticker-section-title">🔗 관련 링크</h3>
            <div className="ticker-links">
              <a href={result.links.overview} target="_blank" rel="noopener noreferrer" className="ticker-link">
                Overview
              </a>
              <a href={result.links.news} target="_blank" rel="noopener noreferrer" className="ticker-link">
                News
              </a>
              <a href={result.links.sec_filings} target="_blank" rel="noopener noreferrer" className="ticker-link">
                SEC Filings
              </a>
            </div>
          </div>

          {/* 블로그 생성 */}
          <div className="ticker-section ticker-blog-section">
            <h3 className="ticker-section-title">📝 블로그형 생성</h3>
            <div className="ticker-blog-controls">
              <div className="tabs" style={{ marginBottom: 'var(--space-md)' }}>
                <button className={`tab ${activeBlogTab === 'naver' ? 'active' : ''}`} onClick={() => setActiveBlogTab('naver')}>
                  🟢 네이버 블로그
                </button>
                <button className={`tab ${activeBlogTab === 'tistory' ? 'active' : ''}`} onClick={() => setActiveBlogTab('tistory')}>
                  🟠 티스토리
                </button>
              </div>
              <button
                className="btn btn-primary"
                onClick={handleBlogify}
                disabled={blogGenerating}
              >
                {blogGenerating && <span className="spinner" />}
                {blogGenerating ? '생성 중...' : `${activeBlogTab === 'naver' ? '네이버' : '티스토리'} 블로그 생성`}
              </button>
            </div>

            {/* 블로그 결과 */}
            {blogResult && (
              <div className="ticker-blog-result fade-in">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-md)' }}>
                  <h4>생성된 블로그 글</h4>
                  <CopyButton text={getBlogFullText()} label="전체 복사" />
                </div>

                {/* 제목 후보 */}
                <div className="draft-section">
                  <div className="draft-section-title">📌 제목 후보 (3개)</div>
                  {blogResult.titles.map((t, i) => (
                    <div key={i} className="draft-title-candidate">
                      <span>{t}</span>
                      <CopyButton text={t} label="" />
                    </div>
                  ))}
                </div>

                {/* 도입부 후보 */}
                <div className="draft-section">
                  <div className="draft-section-title">✏️ 도입부 후보 (2개)</div>
                  {blogResult.intros.map((intro, i) => (
                    <div key={i} className="draft-title-candidate" style={{ fontSize: 'var(--font-size-sm)' }}>
                      <span>{intro}</span>
                      <CopyButton text={intro} label="" />
                    </div>
                  ))}
                </div>

                {/* 본문 */}
                <div className="draft-section">
                  <div className="draft-section-title">
                    📝 본문
                    <CopyButton text={blogResult.body} label="복사" />
                  </div>
                  <div className="draft-body">{blogResult.body}</div>
                </div>

                {/* 핵심 요약 */}
                <div className="draft-section">
                  <div className="draft-section-title">
                    💡 핵심 요약
                    <CopyButton text={blogResult.summary} label="복사" />
                  </div>
                  <div className="draft-body" style={{ fontSize: 'var(--font-size-sm)' }}>{blogResult.summary}</div>
                </div>

                {/* 해시태그 */}
                <div className="draft-section">
                  <div className="draft-section-title">#️⃣ 해시태그</div>
                  <div className="hashtags-container">
                    {blogResult.hashtags.map((tag, i) => (
                      <span key={i} className="hashtag">#{tag}</span>
                    ))}
                  </div>
                </div>

                {/* 주의문구 */}
                {blogResult.caution && (
                  <div className="draft-section">
                    <div className="draft-section-title">⚠️ 주의문구</div>
                    <div className="draft-body" style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
                      {blogResult.caution}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 빈 상태 */}
      {!result && !analyzing && !error && (
        <div className="empty-state">
          <div className="empty-state-icon">📊</div>
          <p>티커를 입력하고 분석을 실행하세요</p>
          <p style={{ fontSize: 'var(--font-size-xs)', marginTop: 'var(--space-sm)', color: 'var(--color-text-muted)' }}>
            예: NVDA, AAPL, TSLA, AMD, MSFT
          </p>
        </div>
      )}
    </div>
  )
}
