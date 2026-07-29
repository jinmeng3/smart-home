export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export interface RecentConversation {
  id: string
  title: string
  time: string
  icon: string
}
