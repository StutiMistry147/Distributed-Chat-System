class WebSocketService {
  constructor() {
    this.socket = null
    this.messageHandler = null
  }

  connect(channelId, token, onMessage) {
    const url = `${import.meta.env.VITE_WS_URL}/api/ws/${channelId}?token=${token}`
    
    this.socket = new WebSocket(url)
    this.messageHandler = onMessage

    this.socket.onopen = () => {
      console.log('WebSocket connected')
    }

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (this.messageHandler) {
          this.messageHandler(data)
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    this.socket.onclose = () => {
      console.log('WebSocket disconnected')
    }

    return this.socket
  }

  disconnect() {
    if (this.socket) {
      this.socket.close()
      this.socket = null
      this.messageHandler = null
    }
  }

  send(content) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ content }))
    } else {
      console.warn('WebSocket is not connected')
    }
  }

  isConnected() {
    return this.socket && this.socket.readyState === WebSocket.OPEN
  }
}

export default new WebSocketService()