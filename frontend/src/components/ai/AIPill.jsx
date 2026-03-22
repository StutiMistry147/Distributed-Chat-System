import { useState } from 'react'
import { useAppStore } from '../../store/useAppStore'

export default function AIPill({ onSearchClick, onSummarizeClick }) {
  const { activeChannelId } = useAppStore()
  const [isHovered, setIsHovered] = useState(false)

  if (!activeChannelId) return null

  return (
    <div 
      className="fixed bottom-24 left-6 z-50"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="flex shadow-lg transition-transform duration-200 hover:scale-105">
        {/* Search Button */}
        <button
          onClick={onSearchClick}
          className={`flex items-center space-x-2 px-4 py-2 rounded-l-full transition-colors ${
            isHovered ? 'bg-space-cyan text-white' : 'bg-[var(--surface)] text-[var(--text-secondary)]'
          } border border-[var(--border)]`}
          aria-label="Search messages"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <span className="text-sm font-medium">Search</span>
        </button>
        
        {/* Divider */}
        <div className="w-px bg-[var(--border)]" />
        
        {/* Summarize Button */}
        <button
          onClick={onSummarizeClick}
          className={`flex items-center space-x-2 px-4 py-2 rounded-r-full transition-colors ${
            isHovered ? 'bg-space-cyan text-white' : 'bg-[var(--surface)] text-[var(--text-secondary)]'
          } border border-[var(--border)]`}
          aria-label="Summarize channel"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span className="text-sm font-medium">Summarize</span>
        </button>
      </div>
    </div>
  )
}