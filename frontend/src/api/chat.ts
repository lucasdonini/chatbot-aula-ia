const CHAT_ENDPOINT = '/api/chat'

type ChatRequest = {
  message: string
}

export async function sendChatMessage(
  sessionId: string,
  message: string,
): Promise<string> {
  let apiResponse: Response

  try {
    apiResponse = await fetch(
      `${CHAT_ENDPOINT}/${encodeURIComponent(sessionId)}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message } satisfies ChatRequest),
      },
    )
  } catch {
    throw new Error('Não foi possível conectar ao assistente.')
  }

  if (!apiResponse.ok) {
    throw new Error('Não foi possível obter uma resposta do assistente.')
  }

  let responseBody: unknown

  try {
    responseBody = await apiResponse.json()
  } catch {
    throw new Error('O assistente retornou uma resposta em formato inválido.')
  }

  if (typeof responseBody !== 'string') {
    throw new Error('O assistente retornou uma resposta em formato inválido.')
  }

  return responseBody
}
