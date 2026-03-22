import { useEffect, useState } from 'react'
import api from '../../services/api'
import { useAppStore } from '../../store/useAppStore'
import { useAuthStore } from '../../store/useAuthStore'

export default function ChannelList() {
  const [channels, setChannels] = useState([])
  const [serverName, setServerName] = useState('')
  const { activeServerId, activeChannelId, setActiveChannel } = useAppStore()
  const { token, user, logout } = useAuthStore()

  useEffect(() => {
    const fetchChannels = async () => {
      if (!activeServerId) {
        setChannels([])
        setServerName('')
        return
      }

      try {
        const response = await api.get(`/channels/server/${activeServerId}`)
        setChannels(response.data)
        
        // For now, just use a generic server name or fetch from API
        setServerName('Server')
        
        // Auto-select first channel if available and none selected
        if (response.data.length > 0 && !activeChannelId) {
          setActiveChannel(response.data[0].id, response.data[0].name)
        }
      } catch (err) {
        console.error('Failed to fetch channels:', err)
      }
    }

    if (token) {
      fetchChannels()
    }
  }, [activeServerId, token, activeChannelId, setActiveChannel])

  const handleLogout = () => {
    logout()
    window.location.href = '/auth'
  }

  return (
    <div className="h-full flex flex-col bg-[var(--surface)]">
      {/* Server Name Header */}
      <div className="p-4 border-b border-[var(--border)]">
        <h2 className="font-semibold text-[var(--text-primary)]">
          {activeServerId ? serverName : 'No Server Selected'}
        </h2>
      </div>
      
      {/* Channels List */}
      <div className="flex-1 overflow-y-auto p-2">
        <div className="px-2 py-1 text-xs font-semibold text-[var(--text-secondary)] uppercase">
          Text Channels
        </div>
        
        {!activeServerId ? (
          <div className="px-2 py-4 text-sm text-[var(--text-secondary)] text-center">
            Select a server to view channels
          </div>
        ) : channels.length === 0 ? (
          <div className="px-2 py-4 text-sm text-[var(--text-secondary)] text-center">
            No channels yet
          </div>
        ) : (
          channels.map((channel) => (
            <button
              key={channel.id}
              onClick={() => setActiveChannel(channel.id, channel.name)}
              className={`w-full px-2 py-1 rounded text-left flex items-center space-x-2 hover:bg-[var(--input)] transition-colors ${
                activeChannelId === channel.id ? 'bg-[var(--input)]' : ''
              }`}
            >
              <span className="text-space-cyan">#</span>
              <span className={`text-sm ${activeChannelId === channel.id ? 'text-[var(--text-primary)]' : 'text-[var(--text-secondary)]'}`}>
                {channel.name}
              </span>
            </button>
          ))
        )}
      </div>
      
      {/* User Info Footer */}
      <div className="p-4 border-t border-[var(--border)]">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-full bg-space-cyan flex items-center justify-center text-[var(--bg)] font-bold">
              {user?.username?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-medium text-[var(--text-primary)]">{user?.username || 'You'}</span>
              <span className="text-xs text-[var(--text-secondary)]">Online</span>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="text-[var(--text-secondary)] hover:text-red-400 transition-colors"
            title="Logout"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}