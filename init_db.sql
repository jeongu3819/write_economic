CREATE DATABASE IF NOT EXISTS economy_blog
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE economy_blog;

-- 1. 주차별 실행 이력
CREATE TABLE IF NOT EXISTS weekly_runs (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  week_key        VARCHAR(10) NOT NULL,
  run_started_at  DATETIME,
  run_finished_at DATETIME,
  status          VARCHAR(20) DEFAULT 'pending',
  total_source_count INT DEFAULT 0,
  total_keyword_count INT DEFAULT 0,
  note            TEXT,
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_week (week_key)
) ENGINE=InnoDB;

-- 2. 수집된 원본 데이터
CREATE TABLE IF NOT EXISTS source_items (
  id                      INT AUTO_INCREMENT PRIMARY KEY,
  week_key                VARCHAR(10) NOT NULL,
  source_type             VARCHAR(20) NOT NULL,
  source_site             VARCHAR(30) NOT NULL,
  title                   VARCHAR(500) NOT NULL,
  summary                 TEXT,
  url                     VARCHAR(2000),
  published_at            DATETIME,
  raw_text                MEDIUMTEXT,
  normalized_topic        VARCHAR(200),
  related_symbols_json    JSON,
  related_industries_json JSON,
  created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_week (week_key),
  INDEX idx_source (source_site, source_type)
) ENGINE=InnoDB;

-- 3. 키워드 후보
CREATE TABLE IF NOT EXISTS keyword_candidates (
  id                    INT AUTO_INCREMENT PRIMARY KEY,
  week_key              VARCHAR(10) NOT NULL,
  keyword               VARCHAR(200) NOT NULL,
  keyword_type          VARCHAR(50),
  recommendation_reasons_json JSON,
  origin_summary        TEXT,
  related_news_count    INT DEFAULT 0,
  related_symbol_count  INT DEFAULT 0,
  source_item_ids_json  JSON,
  created_at            DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_week (week_key)
) ENGINE=InnoDB;

-- 4. 키워드 랭킹
CREATE TABLE IF NOT EXISTS keyword_rankings (
  id                      INT AUTO_INCREMENT PRIMARY KEY,
  week_key                VARCHAR(10) NOT NULL,
  keyword                 VARCHAR(200) NOT NULL,
  keyword_type            VARCHAR(50),
  recommendation_reasons_json JSON,
  rank_no                 INT,
  final_score             DECIMAL(10,2) DEFAULT 0,
  issue_score             DECIMAL(10,2) DEFAULT 0,
  search_score            DECIMAL(10,2) DEFAULT 0,
  competition_penalty     DECIMAL(10,2) DEFAULT 0,
  search_volume           INT DEFAULT 0,
  document_count          INT DEFAULT 0,
  keyword_ratio           DECIMAL(10,4) DEFAULT 0,
  related_news_count      INT DEFAULT 0,
  related_symbol_count    INT DEFAULT 0,
  summary_line            VARCHAR(500),
  competition_level       VARCHAR(10),
  recommended_channel     VARCHAR(20),
  is_doc_count_100k_plus  BOOLEAN DEFAULT FALSE,
  extra_metrics_json      JSON,
  created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_week_rank (week_key, rank_no)
) ENGINE=InnoDB;

-- 5. 블로그 초안
CREATE TABLE IF NOT EXISTS blog_drafts (
  id                      INT AUTO_INCREMENT PRIMARY KEY,
  week_key                VARCHAR(10) NOT NULL,
  keyword_ranking_id      INT,
  keyword                 VARCHAR(200) NOT NULL,
  title_candidates_json   JSON,
  intro_candidates_json   JSON,
  body_naver              MEDIUMTEXT,
  body_tistory_md         MEDIUMTEXT,
  body_tistory_html       MEDIUMTEXT,
  summary_text            TEXT,
  hashtags_json           JSON,
  caution_note            TEXT,
  status                  VARCHAR(20) DEFAULT 'draft',
  created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_week (week_key),
  FOREIGN KEY (keyword_ranking_id) REFERENCES keyword_rankings(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 6. 프롬프트 템플릿
CREATE TABLE IF NOT EXISTS prompt_templates (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  template_name   VARCHAR(100) NOT NULL,
  template_type   VARCHAR(30) NOT NULL,
  version         INT DEFAULT 1,
  system_prompt   MEDIUMTEXT NOT NULL,
  schema_json     JSON,
  is_active       BOOLEAN DEFAULT TRUE,
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_type_active (template_type, is_active)
) ENGINE=InnoDB;

-- 7. 티커 분석 캐시
CREATE TABLE IF NOT EXISTS ticker_analyses (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  ticker          VARCHAR(20) NOT NULL,
  model_used      VARCHAR(50),
  result_json     JSON NOT NULL,
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_ticker (ticker),
  INDEX idx_created (created_at)
) ENGINE=InnoDB;
