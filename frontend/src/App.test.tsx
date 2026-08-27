// @vitest-environment jsdom

import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { sendChatMessage } from './api/chat'
import { finalizeSession } from './api/session'
import App from './App'

const SESSION_ID = '123e4567-e89b-12d3-a456-426614174000'
const NEXT_SESSION_ID = '123e4567-e89b-12d3-a456-426614174001'
const SESSION_STORAGE_KEY = 'assessor-ia.session-id'

vi.mock('./api/chat', () => ({
  sendChatMessage: vi.fn(),
}))
vi.mock('./api/session', () => ({
  finalizeSession: vi.fn(),
}))

afterEach(() => {
  cleanup()
  localStorage.clear()
  vi.clearAllMocks()
  vi.unstubAllGlobals()
})

function renderApp(nextSessionId = SESSION_ID) {
  const randomUUID = vi
    .fn()
    .mockReturnValueOnce(SESSION_ID)
    .mockReturnValue(nextSessionId)
  vi.stubGlobal('crypto', {
    randomUUID,
  })
  render(<App />)
  return { randomUUID }
}

describe('App', () => {
  it('envia a mensagem e apresenta a resposta do assistente', async () => {
    const user = userEvent.setup()
    vi.mocked(sendChatMessage).mockResolvedValue({
      session_id: SESSION_ID,
      content: '**Resposta** do assistente',
    })
    renderApp()

    await user.type(screen.getByLabelText('Sua mensagem'), 'Minha pergunta')
    await user.click(screen.getByRole('button', { name: 'Enviar mensagem' }))

    expect(sendChatMessage).toHaveBeenCalledWith(SESSION_ID, 'Minha pergunta')
    await waitFor(() => {
      expect(screen.getByRole('status').textContent).toContain(
        'Resposta do assistente',
      )
    })
  })

  it('apresenta erro público quando o envio falha', async () => {
    const user = userEvent.setup()
    vi.mocked(sendChatMessage).mockRejectedValue(
      new Error('Não foi possível conectar ao assistente.'),
    )
    renderApp()

    await user.type(screen.getByLabelText('Sua mensagem'), 'Minha pergunta')
    await user.click(screen.getByRole('button', { name: 'Enviar mensagem' }))

    expect(
      await screen.findByText('Não foi possível conectar ao assistente.'),
    ).toBeTruthy()
  })

  it('não permite enviar uma mensagem vazia', () => {
    renderApp()

    const submitButton = screen.getByRole('button', {
      name: 'Enviar mensagem',
    }) as HTMLButtonElement
    expect(submitButton.disabled).toBe(true)
    expect(sendChatMessage).not.toHaveBeenCalled()
  })

  it('persiste a sessão criada para reutilizá-la depois', () => {
    renderApp()

    expect(localStorage.getItem(SESSION_STORAGE_KEY)).toBe(SESSION_ID)
  })

  it('reutiliza a sessão persistida ao abrir novamente', async () => {
    const user = userEvent.setup()
    localStorage.setItem(SESSION_STORAGE_KEY, SESSION_ID)
    vi.mocked(sendChatMessage).mockResolvedValue({
      session_id: SESSION_ID,
      content: 'Resposta do assistente',
    })

    const { randomUUID } = renderApp(NEXT_SESSION_ID)

    await user.type(screen.getByLabelText('Sua mensagem'), 'Continuar conversa')
    await user.click(screen.getByRole('button', { name: 'Enviar mensagem' }))

    await waitFor(() =>
      expect(sendChatMessage).toHaveBeenCalledWith(
        SESSION_ID,
        'Continuar conversa',
      ),
    )
    expect(randomUUID).not.toHaveBeenCalled()
  })

  it('substitui um identificador persistido inválido', () => {
    localStorage.setItem(SESSION_STORAGE_KEY, 'id-inválido')

    renderApp()

    expect(localStorage.getItem(SESSION_STORAGE_KEY)).toBe(SESSION_ID)
  })

  it('reutiliza a mesma sessão em mensagens consecutivas', async () => {
    const user = userEvent.setup()
    vi.mocked(sendChatMessage).mockResolvedValue({
      session_id: SESSION_ID,
      content: 'Resposta do assistente',
    })
    renderApp()

    const messageInput = screen.getByLabelText('Sua mensagem')
    const submitButton = screen.getByRole('button', { name: 'Enviar mensagem' })

    await user.type(messageInput, 'Primeira pergunta')
    await user.click(submitButton)
    await waitFor(() => expect(sendChatMessage).toHaveBeenCalledTimes(1))

    await user.clear(messageInput)
    await user.type(messageInput, 'Segunda pergunta')
    await user.click(submitButton)
    await waitFor(() => expect(sendChatMessage).toHaveBeenCalledTimes(2))

    expect(sendChatMessage).toHaveBeenNthCalledWith(
      1,
      SESSION_ID,
      'Primeira pergunta',
    )
    expect(sendChatMessage).toHaveBeenNthCalledWith(
      2,
      SESSION_ID,
      'Segunda pergunta',
    )
  })

  it('encerra a sessão atual antes de iniciar outra', async () => {
    const user = userEvent.setup()
    vi.mocked(finalizeSession).mockResolvedValue({
      session_id: SESSION_ID,
      session_summary: 'Resumo da sessão',
    })
    vi.mocked(sendChatMessage).mockResolvedValue({
      session_id: NEXT_SESSION_ID,
      content: 'Resposta da nova sessão',
    })
    renderApp(NEXT_SESSION_ID)

    await user.click(screen.getByRole('button', { name: 'Nova sessão' }))
    await waitFor(() =>
      expect(finalizeSession).toHaveBeenCalledWith(SESSION_ID),
    )
    expect(localStorage.getItem(SESSION_STORAGE_KEY)).toBe(NEXT_SESSION_ID)

    await user.type(screen.getByLabelText('Sua mensagem'), 'Nova pergunta')
    await user.click(screen.getByRole('button', { name: 'Enviar mensagem' }))

    await waitFor(() =>
      expect(sendChatMessage).toHaveBeenCalledWith(
        NEXT_SESSION_ID,
        'Nova pergunta',
      ),
    )
  })

  it('preserva a sessão atual quando o encerramento falha', async () => {
    const user = userEvent.setup()
    vi.mocked(finalizeSession).mockRejectedValue(
      new Error('Não foi possível encerrar a sessão.'),
    )
    vi.mocked(sendChatMessage).mockResolvedValue({
      session_id: SESSION_ID,
      content: 'Resposta do assistente',
    })
    renderApp(NEXT_SESSION_ID)

    await user.click(screen.getByRole('button', { name: 'Nova sessão' }))
    expect(
      await screen.findByText('Não foi possível encerrar a sessão.'),
    ).toBeTruthy()
    expect(localStorage.getItem(SESSION_STORAGE_KEY)).toBe(SESSION_ID)

    await user.type(screen.getByLabelText('Sua mensagem'), 'Tentar novamente')
    await user.click(screen.getByRole('button', { name: 'Enviar mensagem' }))

    await waitFor(() =>
      expect(sendChatMessage).toHaveBeenCalledWith(
        SESSION_ID,
        'Tentar novamente',
      ),
    )
  })
})
