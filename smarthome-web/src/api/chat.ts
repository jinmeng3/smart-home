import { ApiError } from './client'

const defaultUserId = '1'
const currentUserStorageKeys = ['smart-home-current-user-id', 'currentUserId', 'userId']

export interface ChatCompletionMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
}

const getCurrentUserId = () => {
  for (const key of currentUserStorageKeys) {
    const userId = window.sessionStorage.getItem(key) ?? window.localStorage.getItem(key)

    if (userId) {
      return userId
    }
  }

  return defaultUserId
}

const parseContentDelta = (line: string) => {
  if (!line.startsWith('data: ')) {
    return ''
  }

  const data = line.slice(6).trim()

  if (!data || data === '[DONE]') {
    return ''
  }

  const payload = JSON.parse(data)

  if (payload.error) {
    throw new Error(String(payload.error))
  }

  return payload.choices?.[0]?.delta?.content ?? ''
}

export const streamChatCompletion = async (
  messages: ChatCompletionMessage[],
  onDelta: (content: string) => void,
) => {
  const response = await fetch('/api/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': getCurrentUserId(),
    },
    body: JSON.stringify({ messages, stream: true }),
  })

  if (!response.ok || !response.body) {
    const data = await response.json().catch(() => ({ detail: '请求失败' }))
    throw new ApiError(data.detail ?? '请求失败', response.status)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()

    if (done) {
      break
    }

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      const delta = parseContentDelta(line.trim())

      if (delta) {
        onDelta(delta)
      }
    }
  }
}
