import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

type MarkdownResponseProps = Readonly<{
  content: string
}>

export function MarkdownResponse({ content }: MarkdownResponseProps) {
  return (
    <div className="markdown-response">
      <Markdown
        components={{ h1: 'h3', h2: 'h4' }}
        remarkPlugins={[remarkGfm]}
        skipHtml
      >
        {content}
      </Markdown>
    </div>
  )
}
