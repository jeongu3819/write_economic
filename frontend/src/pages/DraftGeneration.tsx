import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import api from '../api/client'
import CopyButton from '../components/CopyButton'
import type { BlogDraft, ApiResponse, ModelInfo } from '../types'

export default function DraftGeneration(): React.JSX.Element | null {
  const { rankingId } = useParams<{ rankingId: string }>()
  const [draft, setDraft] = useState<BlogDraft | null>(null)
  const [generating, setGenerating] = useState(false)
  const [activeTab, setActiveTab] = useState<'naver' | 'tistory'>('naver')
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')
  const [models, setModels] = useState<ModelInfo[]>([])
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [loadingInitial, setLoadingInitial] = useState(true)

  useEffect(() => {
    loadModels()
    checkExistingDraft()
  }, [rankingId])

  const loadModels = async () => {
    try {
      const res = await api.get<unknown, ApiResponse<{ models: ModelInfo[]; default_model: string }>>('/models')
      if (res.data?.models) {
        setModels(res.data.models)
        const draftModel = res.data.models.find(m => m.id.includes('5.4') && !m.id.includes('mini'))?.id
        setSelectedModel(draftModel || res.data.default_model || res.data.models[0]?.id || '')
      }
    } catch {
      // ignore
    }
  }

  const checkExistingDraft = async () => {
    setLoadingInitial(true)
    setError('')
    try {
      const res = await api.get<unknown, ApiResponse<BlogDraft>>(`/drafts/by-ranking/${rankingId}`)
      if (res.data) {
        setDraft(res.data)
        setSaved(true)
      } else {
        setDraft(null)
      }
    } catch {
      // ignore
    } finally {
      setLoadingInitial(false)
    }
  }

  const generateDraft = async (): Promise<void> => {
    setGenerating(true)
    setError('')
    try {
      const res = await api.post<unknown, ApiResponse<BlogDraft>>('/drafts/generate', {
        keyword_ranking_id: parseInt(rankingId || '0'),
        model: selectedModel || undefined,
      })
      setDraft(res.data)
      setSaved(true)
    } catch (err) {
      setError(`생성 실패: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setGenerating(false)
    }
  }

  const handleRegenerate = async (): Promise<void> => {
    if (!draft?.id) return
    setGenerating(true)
    setError('')
    try {
      const queryModel = selectedModel ? `?model=${selectedModel}` : ''
      const res = await api.post<unknown, ApiResponse<BlogDraft>>(`/drafts/${draft.id}/regenerate${queryModel}`)
      setDraft(res.data)
    } catch (err) {
      setError(`재생성 실패: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setGenerating(false)
    }
  }

  const getFullText = (): string => {
    if (!draft) return ''
    const titles = draft.title_candidates_json || []
    const body = activeTab === 'naver' ? draft.body_naver : draft.body_tistory_md
    const hashtags = (draft.hashtags_json || []).map((h) => `#${h}`).join(' ')

    return `${titles[0] || ''}\n\n${(draft.intro_candidates_json || [])[0] || ''}\n\n${body || ''}\n\n${hashtags}\n\n${draft.caution_note || ''}`
  }

  const renderMarkdownText = (text: string) => {
    if (!text) return ''
    
    // Split by lines to handle block elements safely
    const lines = text.split('\n')
    let html = ''
    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        
        let isHeader = false
        if (line.startsWith('### ')) {
            line = `<div style="font-weight: bold; font-size: 15px; margin-top: 12px; margin-bottom: 6px;">${line.substring(4)}</div>`
            isHeader = true
        } else if (line.startsWith('## ')) {
            line = `<div style="font-weight: bold; font-size: 16px; margin-top: 16px; margin-bottom: 8px;">${line.substring(3)}</div>`
            isHeader = true
        } else if (line.startsWith('# ')) {
            line = `<div style="font-weight: bold; font-size: 18px; margin-top: 20px; margin-bottom: 10px;">${line.substring(2)}</div>`
            isHeader = true
        }
        
        html += line
        // Don't add BR if it's a header block, or if it's the last line
        if (!isHeader && i < lines.length - 1) {
            html += '<br/>'
        }
    }
    return html
  }

  if (loadingInitial) {
    return (
      <div className="loading-container" style={{ minHeight: '60vh' }}>
        <div className="spinner" style={{ width: 40, height: 40 }} />
      </div>
    )
  }

  if (generating) {
    return (
      <div className="loading-container" style={{ minHeight: '60vh' }}>
        <div className="spinner" style={{ width: 40, height: 40 }} />
        <span style={{ fontSize: 'var(--font-size-lg)' }}>🤖 선택하신 AI가 블로그 초안을 생성하고 있습니다...</span>
        <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>약 10~20초 소요됩니다</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">⚠️</div>
        <p>{error}</p>
        <button className="btn btn-primary" onClick={generateDraft} style={{ marginTop: 'var(--space-md)' }}>
          다시 시도
        </button>
      </div>
    )
  }

  if (!draft && !error) {
    return (
      <div className="empty-state" style={{ minHeight: '60vh' }}>
        <div className="empty-state-icon">📝</div>
        <p>이 키워드로 새로운 블로그 초안을 생성합니다.</p>
        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-lg)' }}>
          작성할 AI 모델을 선택한 후 생성 버튼을 눌러주세요.
        </p>
        <div style={{ display: 'flex', gap: 'var(--space-sm)', alignItems: 'center' }}>
          <select 
            className="input" 
            style={{ width: '160px', padding: '10px' }}
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
          >
            {models.map(m => (
              <option key={m.id} value={m.id}>{m.id}</option>
            ))}
          </select>
          <button className="btn btn-primary btn-lg" onClick={generateDraft}>
            🚀 초안 생성 시작
          </button>
        </div>
      </div>
    )
  }

  if (!draft) return null

  return (
    <div className="draft-container fade-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title">{draft.keyword}</h1>
          <p className="page-subtitle">{draft.week_key} · {saved ? '✅ 저장됨' : ''}</p>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-sm)', alignItems: 'center' }}>
          <CopyButton text={getFullText()} label="전체 복사" showMobileCopy={true} />
          
          <select 
            className="input" 
            style={{ padding: '8px', fontSize: 'var(--font-size-sm)', height: '100%' }}
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
          >
            {models.map(m => (
              <option key={m.id} value={m.id}>{m.id}</option>
            ))}
          </select>

          <button className="btn btn-secondary" onClick={handleRegenerate}>
            🔄 재생성
          </button>
        </div>
      </div>

      <div className="tabs">
        <button className={`tab ${activeTab === 'naver' ? 'active' : ''}`} onClick={() => setActiveTab('naver')}>
          🟢 네이버형
        </button>
        <button className={`tab ${activeTab === 'tistory' ? 'active' : ''}`} onClick={() => setActiveTab('tistory')}>
          🟠 티스토리형
        </button>
      </div>

      <div className="draft-section">
        <div className="draft-section-title">
          📌 제목 후보
          <CopyButton text={(draft.title_candidates_json || []).join('\n')} label="복사" />
        </div>
        {(draft.title_candidates_json || []).map((title, i) => (
          <div key={i} className="draft-title-candidate">
            <span>{title}</span>
            <CopyButton text={title} label="" />
          </div>
        ))}
      </div>

      <div className="draft-section">
        <div className="draft-section-title">
          ✏️ 도입부 후보
          <CopyButton text={(draft.intro_candidates_json || []).join('\n\n')} label="복사" />
        </div>
        {(draft.intro_candidates_json || []).map((intro, i) => (
          <div key={i} className="draft-title-candidate" style={{ fontSize: 'var(--font-size-base)' }}>
            <span>{intro}</span>
            <CopyButton text={intro} label="" />
          </div>
        ))}
      </div>

      <div className="draft-section">
        <div className="draft-section-title">
          📝 본문
          <CopyButton
            text={(activeTab === 'naver' ? draft.body_naver : draft.body_tistory_md) || ''}
            label="복사"
            showMobileCopy={true}
          />
        </div>
        <div className="draft-body" dangerouslySetInnerHTML={{
          __html: activeTab === 'tistory' && draft.body_tistory_html
            ? draft.body_tistory_html
            : renderMarkdownText((activeTab === 'naver' ? draft.body_naver : draft.body_tistory_md) || '')
        }} />
      </div>

      {draft.summary_text && (
        <div className="draft-section">
          <div className="draft-section-title">
            💡 핵심 요약
            <CopyButton text={draft.summary_text} label="복사" />
          </div>
          <div className="draft-body" style={{ fontSize: 'var(--font-size-sm)' }}>
            {draft.summary_text}
          </div>
        </div>
      )}

      <div className="draft-section">
        <div className="draft-section-title">
          #️⃣ 해시태그
          <CopyButton text={(draft.hashtags_json || []).map((h) => `#${h}`).join(' ')} label="복사" />
        </div>
        <div className="hashtags-container">
          {(draft.hashtags_json || []).map((tag, i) => (
            <span key={i} className="hashtag">#{tag}</span>
          ))}
        </div>
      </div>

      {draft.caution_note && (
        <div className="draft-section">
          <div className="draft-section-title">⚠️ 주의문구</div>
          <div className="draft-body" style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
            {draft.caution_note}
          </div>
        </div>
      )}
    </div>
  )
}
