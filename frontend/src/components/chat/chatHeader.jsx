import { useAppStore } from '../../store/useAppStore'
import ThemeToggle from '../ui/ThemeToggle'

export default function ChatHeader() {
  const { activeChannelName, toggleMemberList, isMemberListOpen } = useAppStore()

  return (
    <div className="h-12 px-4 border-b border-[var(--border)] flex items-center justify-between">
      <h2 className="font-semibold text-[var(--text-primary)]">
        #{activeChannelName || 'Loading...'}
      </h2>
      <div className="flex items-center space-x-2">
        <ThemeToggle />
        <button
          onClick={toggleMemberList}
          className={`px-3 py-1 text-sm rounded transition-colors ${
            isMemberListOpen 
              ? 'bg-space-cyan text-white' 
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--input)]'
          }`}
        >
          Members
        </button>
      </div>
    </div>
  )
}