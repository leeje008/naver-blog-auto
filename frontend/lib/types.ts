export interface BlogDraft {
  title: string;
  content: string;
  hashtags: string[];
  meta?: {
    keyword?: string;
    model?: string;
    template?: string;
    created_at?: string;
  };
}

export interface SeoCheckItem {
  key: string;
  label: string;
  score: number;
  maxScore: number;
  passed: boolean;
  suggestions: string[];
}

export interface SeoResult {
  totalScore: number;
  grade: string;
  items: SeoCheckItem[];
  profile: string;
}

export interface KeywordResult {
  keyword: string;
  score: number;
  source: string;
  blog_count: number;
  competition: string;
}

export interface TopPostMetrics {
  avg_length: number;
  avg_images: number;
  avg_headings: number;
  keyword_density: number;
  common_patterns: string[];
}

export interface HistoryEntry {
  id: string;
  title: string;
  keyword: string;
  created_at: string;
  word_count: number;
  seo_score: number;
  tags: string[];
  content?: string;
}

export interface SeoProfile {
  name: string;
  weights: Record<string, number>;
}
