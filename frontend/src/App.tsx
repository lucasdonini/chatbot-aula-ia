import { type FormEvent, type KeyboardEvent, useState } from 'react'
import './App.css'

function App() {
  const [message, setMessage] = useState('')
  const [response, setResponse] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const trimmedMessage = message.trim()
    if (!trimmedMessage) {
      return
    }

    setIsLoading(true)
    setError('')
    setResponse('')

    try {
      const apiResponse = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmedMessage }),
      })

      if (!apiResponse.ok) {
        throw new Error('Não foi possível obter uma resposta do assistente.')
      }

      const responseBody: unknown = await apiResponse.json()
      if (typeof responseBody !== 'string') {
        throw new Error('O assistente retornou uma resposta em formato inválido.')
      }

      setResponse(responseBody)
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
          <output className="response" aria-live="polite">
            {isLoading && 'O assistente está preparando uma resposta...'}
            {!isLoading && error && <span className="error">{error}</span>}
            {!isLoading && !error && response}
            {!isLoading && !error && !response && (
              <span className="placeholder">A resposta aparecerá aqui.</span>
            )}
          </output>
        </section>
      </section>
    </main>
  )
}

export default App
