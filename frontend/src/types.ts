// Shared type definitions

export interface WeeklyRun {
  id: number
  week_key: string
  status: string
  total_source_count: number
  total_keyword_count: number
  run_started_at: string | null
  run_finished_at: string | null
  note: string | null
  created_at: string | null
}

export interface SourceItem {
  id: number
  week_key: string
  source_type: string
  source_site: string
  title: string
  summary: string | null
  url: string | null
  published_at: string | null
  normalized_topic: string | null
  related_symbols_json: string[] | null
  related_industries_json: string[] | null
}

export interface KeywordRanking {
  id: number
  week_key: string
  keyword: string
  rank_no: number | null
  final_score: number | null
  issue_score: number | null
  search_score: number | null
  competition_penalty: number | null
  search_volume: number
  document_count: number
  keyword_ratio: number | null
  related_news_count: number
  related_symbol_count: number
  summary_line: string | null
  competition_level: 'low' | 'medium' | 'high' | null
  recommended_channel: 'naver' | 'tistory' | 'both' | null
  is_doc_count_100k_plus: boolean
  extra_metrics_json: Record<string, unknown> | null
}

export interface BlogDraft {
  id: number
  week_key: string
  keyword_ranking_id: number | null
  keyword: string
  title_candidates_json: string[] | null
  intro_candidates_json: string[] | null
  body_naver: string | null
  body_tistory_md: string | null
  body_tistory_html: string | null
  summary_text: string | null
  hashtags_json: string[] | null
  caution_note: string | null
  status: 'draft' | 'archived'
  created_at: string | null
  updated_at: string | null
}

export interface ApiResponse<T> {
  success: boolean
  data: T
  error: string | null
}
