import { useEffect, useRef } from 'react'
import wsService from '../services/websocket'
import api from '../services/api'
import { useAuthStore } from '../store/useAuthStore'
import { useChatStore } from '../store/useChatStore'

export function useWebSocket(channelId) {
  const { token } = useAuthStore()
  const { setMessages, addMessage, setLoading } = useChatStore()
  const connectedRef = useRef(false)

  useEffect(() => {
    if (!channelId || !token) {
      return
    }

    // Fetch message history
    const fetchMessages = async () => {
      setLoading(true)
      try {
        const response = await api.get(`/messages/${channelId}?limit=50`)
        setMessages(response.data)
      } catch (err) {
        console.error('Failed to fetch messages:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchMessages()

    // Connect WebSocket
    const handleMessage = (data) => {
      if (data.type === 'message' && data.event === 'new') {
        addMessage(data.message)
      } else if (data.type === 'presence') {
        console.log('Presence update:', data)
      }
    }

    wsService.connect(channelId, token, handleMessage)
    connectedRef.current = true

    // Cleanup on unmount or channel change
    return () => {
      if (connectedRef.current) {
        wsService.disconnect()
        connectedRef.current = false
      }
    }
  }, [channelId, token, setMessages, addMessage, setLoading])
}