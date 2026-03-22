import { useState } from 'react'
import wsService from '../../services/websocket'
import { useAppStore } from '../../store/useAppStore'

export default function MessageInput() {
  const [message, setMessage] = useState('')
  const { activeChannelId } = useAppStore()

  const handleSubmit = (e) => {
    e.preventDefault()
    if (message.trim() && activeChannelId) {
      wsService.send(message.trim())
      setMessage('')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="p-4 border-t border-[var(--border)] bg-[var(--bg)]">
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder={!activeChannelId 
          ? 'Select a channel to start chatting' 
          : `Message #channel`}
        disabled={!activeChannelId}
        className="w-full px-4 py-2 bg-[var(--input)] rounded-lg text-[var(--text-primary)] placeholder-[var(--text-secondary)]/50 focus:outline-none focus:ring-2 focus:ring-space-cyan disabled:opacity-50"
      />
    </form>
  )
}