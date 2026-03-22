import { useState } from 'react'
import ServerList from '../components/sidebar/ServerList'
import ChannelList from '../components/sidebar/ChannelList'
import MemberList from '../components/sidebar/MemberList'
import MessageFeed from '../components/chat/MessageFeed'
import MessageInput from '../components/chat/MessageInput'
import ChatHeader from '../components/chat/ChatHeader'
import AIPill from '../components/ai/AIPill'
import SearchPanel from '../components/ai/SearchPanel'
import SummaryPanel from '../components/ai/SummaryPanel'
import { useWebSocket } from '../hooks/useWebSocket'
import { useTheme } from '../hooks/useTheme'
import { useAppStore } from '../store/useAppStore'

export default function MainView() {
  const { activeChannelId, isMemberListOpen } = useAppStore()
  const [isSearchOpen, setIsSearchOpen] = useState(false)
  const [isSummaryOpen, setIsSummaryOpen] = useState(false)
  
  // Initialize theme
  useTheme()
  
  // Initialize WebSocket connection for the active channel
  useWebSocket(activeChannelId)

  return (
    <div className="flex h-screen bg-[var(--bg)]">
      {/* Column 1 - Server List (72px) */}
      <div className="w-[72px] bg-[var(--bg)]">
        <ServerList />
      </div>
      
      {/* Column 2 - Channel List (240px) */}
      <div className="w-60 bg-[var(--surface)]">
        <ChannelList />
      </div>
      
      {/* Column 3 - Chat Area (flexible width) */}
      <div className="flex-1 bg-[var(--bg)]">
        {activeChannelId ? (
          <div className="flex flex-col h-full">
            {/* Chat Header */}
            <ChatHeader />
            {/* Message Feed */}
            <MessageFeed />
            {/* Message Input */}
            <MessageInput />
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-2">Welcome to Space Chat</h2>
              <p className="text-[var(--text-secondary)]">Select a server and channel to start chatting</p>
            </div>
          </div>
        )}
      </div>
      
      {/* Column 4 - Member List (optional, 240px) */}
      {isMemberListOpen && activeChannelId && (
        <div className="w-60 bg-[var(--surface)] border-l border-[var(--border)]">
          <MemberList />
        </div>
      )}
      
      {/* AI Pill Button */}
      <AIPill 
        onSearchClick={() => setIsSearchOpen(true)} 
        onSummarizeClick={() => setIsSummaryOpen(true)} 
      />
      
      {/* Search Panel Modal */}
      {isSearchOpen && <SearchPanel onClose={() => setIsSearchOpen(false)} />}
      
      {/* Summary Panel Modal */}
      {isSummaryOpen && <SummaryPanel onClose={() => setIsSummaryOpen(false)} />}
    </div>
  )
}