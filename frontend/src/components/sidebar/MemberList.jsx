import { useEffect, useState } from 'react'
import api from '../../services/api'
import { useAppStore } from '../../store/useAppStore'
import { useAuthStore } from '../../store/useAuthStore'

export default function MemberList() {
  const [members, setMembers] = useState([])
  const { activeServerId } = useAppStore()
  const { token } = useAuthStore()

  useEffect(() => {
    const fetchMembers = async () => {
      if (!activeServerId) {
        setMembers([])
        return
      }

      try {
        const response = await api.get(`/servers/${activeServerId}/members`)
        // Sort members: online first, then offline
        const sorted = response.data.sort((a, b) => {
          if (a.presence_status === 'online' && b.presence_status !== 'online') return -1
          if (a.presence_status !== 'online' && b.presence_status === 'online') return 1
          return 0
        })
        setMembers(sorted)
      } catch (err) {
        console.error('Failed to fetch members:', err)
      }
    }

    if (token && activeServerId) {
      fetchMembers()
    }
  }, [activeServerId, token])

  const getRoleBadge = (role) => {
    switch (role) {
      case 'owner':
        return <span className="text-xs text-space-cyan ml-1">👑</span>
      case 'admin':
        return <span className="text-xs text-space-purple ml-1">⚡</span>
      default:
        return null
    }
  }

  const getStatusDot = (status) => {
    switch (status) {
      case 'online':
        return <div className="w-2 h-2 rounded-full bg-green-500 mr-2" />
      case 'idle':
        return <div className="w-2 h-2 rounded-full bg-yellow-500 mr-2" />
      case 'offline':
      default:
        return <div className="w-2 h-2 rounded-full bg-gray-500 mr-2" />
    }
  }

  return (
    <div className="h-full flex flex-col bg-[var(--surface)]">
      {/* Header */}
      <div className="p-4 border-b border-[var(--border)]">
        <h2 className="font-semibold text-[var(--text-primary)]">
          Members — {members.length}
        </h2>
      </div>
      
      {/* Members List */}
      <div className="flex-1 overflow-y-auto p-2">
        {members.length === 0 ? (
          <div className="px-2 py-4 text-sm text-[var(--text-secondary)] text-center">
            No members found
          </div>
        ) : (
          members.map((member) => (
            <div
              key={member.id}
              className="flex items-center space-x-2 px-2 py-2 rounded hover:bg-[var(--input)] transition-colors"
            >
              <div className="relative">
                <div className="w-8 h-8 rounded-full bg-space-cyan flex items-center justify-center text-[var(--bg)] font-bold text-sm">
                  {member.username.charAt(0).toUpperCase()}
                </div>
                <div className="absolute -bottom-0.5 -right-0.5">
                  {getStatusDot(member.presence_status)}
                </div>
              </div>
              <div className="flex-1 flex items-center">
                <span className="text-sm text-[var(--text-primary)]">
                  {member.username}
                </span>
                {getRoleBadge(member.role)}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}