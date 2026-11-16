export interface Novel { id: number; title: string }
export interface Variant { id: number; lang: string }
export interface Chapter { id: number; number: number | null; title: string }
export interface Progress { chapter_id: number; scroll_pos: number }
export interface SearchHit {
  chapter_id: number
  novel_title: string
  lang: string
  chapter_title: string
  snippet: string
}
