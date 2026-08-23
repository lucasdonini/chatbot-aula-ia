import { afterEach, describe, expect, it, vi } from 'vitest'
import { sendChatMessage } from './chat'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('sendChatMessage', () => {
  it('envia a mensagem e devolve a resposta textual', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify('Resposta do assistente'), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(sendChatMessage('Minha pergunta')).resolves.toBe(
      'Resposta do assistente',
    )
    expect(fetchMock).toHaveBeenCalledWith('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: 'Minha pergunta' }),
    })
  })

  it('traduz falha de rede para uma mensagem pública', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')))

    await expect(sendChatMessage('Minha pergunta')).rejects.toThrow(
      'Não foi possível conectar ao assistente.',
    )
  })

  it('traduz resposta HTTP malsucedida para uma mensagem pública', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 500 })))

    await expect(sendChatMessage('Minha pergunta')).rejects.toThrow(
      'Não foi possível obter uma resposta do assistente.',
    )
  })

  it.each([
    new Response('conteúdo inválido', { status: 200 }),
    new Response(JSON.stringify({ response: 'texto' }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }),
  ])('rejeita resposta em formato inesperado', async (response) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response))

    await expect(sendChatMessage('Minha pergunta')).rejects.toThrow(
      'O assistente retornou uma resposta em formato inválido.',
    )
  })
})
