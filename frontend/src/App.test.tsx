// @vitest-environment jsdom

import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { sendChatMessage } from './api/chat'
import App from './App'

vi.mock('./api/chat', () => ({
  sendChatMessage: vi.fn(),
}))

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('App', () => {
  it('envia a mensagem e apresenta a resposta do assistente', async () => {
    const user = userEvent.setup()
    vi.mocked(sendChatMessage).mockResolvedValue('**Resposta** do assistente')
    render(<App />)

    await user.type(screen.getByLabelText('Sua mensagem'), 'Minha pergunta')
    await user.click(screen.getByRole('button', { name: 'Enviar mensagem' }))

    expect(sendChatMessage).toHaveBeenCalledWith('Minha pergunta')
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
    render(<App />)

    await user.type(screen.getByLabelText('Sua mensagem'), 'Minha pergunta')
    await user.click(screen.getByRole('button', { name: 'Enviar mensagem' }))

    expect(
      await screen.findByText('Não foi possível conectar ao assistente.'),
    ).toBeTruthy()
  })

  it('não permite enviar uma mensagem vazia', () => {
    render(<App />)

    const submitButton = screen.getByRole('button', {
      name: 'Enviar mensagem',
    }) as HTMLButtonElement
    expect(submitButton.disabled).toBe(true)
    expect(sendChatMessage).not.toHaveBeenCalled()
  })
})
