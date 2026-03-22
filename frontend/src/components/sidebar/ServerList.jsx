import { useEffect, useState } from 'react'
import api from '../../services/api'
import { useAppStore } from '../../store/useAppStore'
import { useAuthStore } from '../../store/useAuthStore'

export default function ServerList() {
  const [servers, setServers] = useState([])
  const { activeServerId, setActiveServer } = useAppStore()
  const { token } = useAuthStore()

  useEffect(() => {
    const fetchServers = async () => {
      try {
        const response = await api.get('/servers')
        setServers(response.data)
        // Auto-select first server if available and none selected
        if (response.data.length > 0 && !activeServerId) {
          setActiveServer(response.data[0].id)
        }
      } catch (err) {
        console.error('Failed to fetch servers:', err)
      }
    }

    if (token) {
      fetchServers()
    }
  }, [token, setActiveServer, activeServerId])

  const handleCreateServer = () => {
    alert('Create server feature coming soon!')
  }

  return (
    <div className="h-full flex flex-col items-center py-3 space-y-2 overflow-y-auto">
      {servers.map((server) => (
        <button
          key={server.id}
          onClick={() => setActiveServer(server.id)}
          className={`relative w-12 h-12 rounded-full transition-all duration-200 flex items-center justify-center text-white font-bold hover:rounded-2xl ${
            activeServerId === server.id
              ? 'bg-space-cyan text-space-bg rounded-2xl'
              : 'bg-space-surface hover:bg-space-cyan/20'
          }`}
        >
          {server.name.charAt(0).toUpperCase()}
          {activeServerId === server.id && (
            <div className="absolute left-0 w-1 h-8 bg-space-cyan rounded-r -ml-3" />
          )}
        </button>
      ))}
      
      <button
        onClick={handleCreateServer}
        className="w-12 h-12 rounded-full bg-space-surface hover:bg-space-cyan/20 transition-colors flex items-center justify-center text-space-cyan text-2xl font-bold"
      >
        +
      </button>
    </div>
  )
}