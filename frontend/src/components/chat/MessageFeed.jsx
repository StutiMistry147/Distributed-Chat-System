import { useEffect, useRef } from 'react'
import { useChatStore } from '../../store/useChatStore'
import MessageBubble from './MessageBubble'

export default function MessageFeed() {
  const { messages, isLoading } = useChatStore()
  const bottomRef = useRef(null)

  useEffect(() => {
    // Auto-scroll to bottom when messages change
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[var(--bg)]">
        <div className="text-[var(--text-secondary)]">Loading messages...</div>
      </div>
    )
  }

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[var(--bg)]">
        <div className="text-center">
          <div className="text-[var(--text-secondary)] text-lg mb-2">✨ Welcome to the channel!</div>
          <div className="text-[var(--text-secondary)]/60 text-sm">Be the first to send a message</div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-2 bg-[var(--bg)]">
      {messages.map((message, index) => {
        const prevMessage = messages[index - 1]
        const showAvatar = !prevMessage || prevMessage.user_id !== message.user_id
        
        return (
          <MessageBubble
            key={message.id}
            message={message}
            showAvatar={showAvatar}
          />
        )
      })}
      <div ref={bottomRef} />
    </div>
  )
}