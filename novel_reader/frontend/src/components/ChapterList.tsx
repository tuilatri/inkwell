import type { Chapter } from '../types'

interface Props {
  chapters: Chapter[]
  onSelect: (id: number) => void
}

export default function ChapterList({ chapters, onSelect }: Props) {
  return (
    <ul className="stack" style={{ listStyle: 'none', padding: 0 }}>
      {chapters.map((chapter) => (
        <li key={chapter.id}>
          <button type="button" onClick={() => onSelect(chapter.id)}>
            {chapter.number !== null ? `${chapter.number}. ` : ''}{chapter.title}
          </button>
        </li>
      ))}
    </ul>
  )
}
