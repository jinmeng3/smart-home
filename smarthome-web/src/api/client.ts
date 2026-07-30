const defaultUserId = '1'
const currentUserStorageKeys = ['smart-home-current-user-id', 'currentUserId', 'userId']

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message)
  }
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

const parseResponse = async <T>(response: Response): Promise<T> => {
  if (response.ok) {
    if (response.status === 204) {
      return undefined as T
    }

    return response.json() as Promise<T>
  }

  const data = await response.json().catch(() => ({ detail: '请求失败' }))
  throw new ApiError(data.detail ?? '请求失败', response.status)
}

export const apiRequest = async <T>(path: string, init: RequestInit = {}): Promise<T> => {
  const headers = new Headers(init.headers)

  if (!headers.has('X-User-Id')) {
    headers.set('X-User-Id', getCurrentUserId())
  }

  if (!(init.body instanceof FormData) && init.body !== undefined) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(path, {
    ...init,
    headers,
  })

  return parseResponse<T>(response)
}
