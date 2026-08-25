// @vitest-environment jsdom

import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { sendChatMessage } from './api/chat'
import App from './App'

const SESSION_ID = '123e4567-e89b-12d3-a456-426614174000'

vi.mock('./api/chat', () => ({
  sendChatMessage: vi.fn(),
}))

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
  vi.unstubAllGlobals()
})

function renderApp() {
  vi.stubGlobal('crypto', {
    randomUUID: vi.fn(() => SESSION_ID),
  })
  render(<App />)
}

describe('App', () => {
  it('envia a mensagem e apresenta a resposta do assistente', async () => {
    const user = userEvent.setup()
    vi.mocked(sendChatMessage).mockResolvedValue('**Resposta** do assistente')
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

  it('reutiliza a mesma sessão em mensagens consecutivas', async () => {
    const user = userEvent.setup()
    vi.mocked(sendChatMessage).mockResolvedValue('Resposta do assistente')
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
})
