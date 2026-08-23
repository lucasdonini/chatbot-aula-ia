import { type KeyboardEvent, type SubmitEvent, useState } from 'react'
import { sendChatMessage } from './api/chat'
import { MarkdownResponse } from './components/MarkdownResponse'
import './App.css'

function App() {
  const [message, setMessage] = useState('')
  const [response, setResponse] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()

    const trimmedMessage = message.trim()
    if (!trimmedMessage) {
      return
    }

    setIsLoading(true)
    setError('')
    setResponse('')

    try {
      setResponse(await sendChatMessage(trimmedMessage))
    } catch (caughtError: unknown) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : 'Ocorreu um erro ao enviar sua mensagem.',
      )
    } finally {
      setIsLoading(false)
    }
  }

  function handleMessageKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.ctrlKey && event.key === 'Enter') {
      event.preventDefault()
      event.currentTarget.form?.requestSubmit()
    }
  }

  return (
    <main className="chat-page">
      <section className="chat-card" aria-labelledby="page-title">
        <header className="chat-header">
          <p className="eyebrow">Assessor.IA</p>
          <h1 id="page-title">Como posso ajudar?</h1>
          <p className="subtitle">
            Envie uma mensagem para conversar com seu assistente.
          </p>
        </header>

        <form className="chat-form" onSubmit={handleSubmit}>
          <label htmlFor="message">Sua mensagem</label>
          <textarea
            id="message"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            onKeyDown={handleMessageKeyDown}
            placeholder="Escreva sua pergunta aqui..."
            rows={5}
            disabled={isLoading}
            required
          />
          <button type="submit" disabled={isLoading || !message.trim()}>
            {isLoading ? 'Consultando...' : 'Enviar mensagem'}
          </button>
        </form>

        <section className="response-section" aria-labelledby="response-title">
          <h2 id="response-title">Resposta</h2>
          <div className="response" role="status" aria-live="polite">
            {isLoading && 'O assistente está preparando uma resposta...'}
            {!isLoading && error && <span className="error">{error}</span>}
            {!isLoading && !error && response && (
              <MarkdownResponse content={response} />
            )}
            {!isLoading && !error && !response && (
              <span className="placeholder">A resposta aparecerá aqui.</span>
            )}
          </div>
        </section>
      </section>
    </main>
  )
}

export default App
