import { type KeyboardEvent, type SubmitEvent, useState } from 'react'
import { sendChatMessage } from './api/chat'
import { finalizeSession } from './api/session'
import { MarkdownResponse } from './components/MarkdownResponse'
import './App.css'

const SESSION_STORAGE_KEY = 'assessor-ia.session-id'
const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

function persistSessionId(sessionId: string) {
  try {
    localStorage.setItem(SESSION_STORAGE_KEY, sessionId)
  } catch {
    // The conversation still works for the lifetime of the current page.
  }
}

function createSessionId() {
  const sessionId = crypto.randomUUID()
  persistSessionId(sessionId)
  return sessionId
}

function getOrCreateSessionId() {
  try {
    const persistedSessionId = localStorage.getItem(SESSION_STORAGE_KEY)
    if (persistedSessionId && UUID_PATTERN.test(persistedSessionId)) {
      return persistedSessionId
    }
  } catch {
    // Fall back to an in-memory identifier when storage is unavailable.
  }

  return createSessionId()
}

function App() {
  const [sessionId, setSessionId] = useState(getOrCreateSessionId)
  const [message, setMessage] = useState('')
  const [response, setResponse] = useState('')
  const [error, setError] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [isFinalizing, setIsFinalizing] = useState(false)

  const isBusy = isSending || isFinalizing

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()

    const trimmedMessage = message.trim()
    if (!trimmedMessage) {
      return
    }

    setIsSending(true)
    setError('')
    setResponse('')

    try {
      const chatResponse = await sendChatMessage(sessionId, trimmedMessage)
      setResponse(chatResponse.content)
    } catch (caughtError: unknown) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : 'Ocorreu um erro ao enviar sua mensagem.',
      )
    } finally {
      setIsSending(false)
    }
  }

  async function handleNewSession() {
    setIsFinalizing(true)
    setError('')

    try {
      await finalizeSession(sessionId)
      setSessionId(createSessionId())
      setMessage('')
      setResponse('')
    } catch (caughtError: unknown) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : 'Ocorreu um erro ao encerrar a sessão.',
      )
    } finally {
      setIsFinalizing(false)
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
          <button
            className="secondary-button"
            type="button"
            onClick={handleNewSession}
            disabled={isBusy}
          >
            {isFinalizing ? 'Encerrando sessão...' : 'Nova sessão'}
          </button>
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
            disabled={isBusy}
            required
          />
          <button type="submit" disabled={isBusy || !message.trim()}>
            {isSending ? 'Consultando...' : 'Enviar mensagem'}
          </button>
        </form>

        <section className="response-section" aria-labelledby="response-title">
          <h2 id="response-title">Resposta</h2>
          <div className="response" role="status" aria-live="polite">
            {isSending && 'O assistente está preparando uma resposta...'}
            {isFinalizing && 'Encerrando a sessão atual...'}
            {!isBusy && error && <span className="error">{error}</span>}
            {!isBusy && !error && response && (
              <MarkdownResponse content={response} />
            )}
            {!isBusy && !error && !response && (
              <span className="placeholder">A resposta aparecerá aqui.</span>
            )}
          </div>
        </section>
      </section>
    </main>
  )
}

export default App
