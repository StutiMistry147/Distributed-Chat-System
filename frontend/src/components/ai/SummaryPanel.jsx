import { useState, useEffect, useRef } from 'react'
import { useAppStore } from '../../store/useAppStore'
import { useAuthStore } from '../../store/useAuthStore'

export default function SummaryPanel({ onClose }) {
  const [summary, setSummary] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const { activeChannelId } = useAppStore()
  const { token } = useAuthStore()
  const containerRef = useRef(null)

  useEffect(() => {
    // Handle Escape key
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [onClose])

  useEffect(() => {
    const fetchSummary = async () => {
      if (!activeChannelId) {
        setError('No channel selected')
        setIsLoading(false)
        return
      }

      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/api/ai/summarize/${activeChannelId}?limit=100`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (!response.ok) {
          throw new Error('Failed to generate summary')
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          
          const chunk = decoder.decode(value)
          setSummary(prev => prev + chunk)
          setIsLoading(false)
        }
      } catch (err) {
        console.error('Summary failed:', err)
        setError(err.message || 'Failed to generate summary')
        setIsLoading(false)
      }
    }

    fetchSummary()
  }, [activeChannelId, token])

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  // Format summary with bullet points
  const formatSummary = (text) => {
    if (!text) return []
    // Split by bullet points or newlines
    const lines = text.split(/\n|•/).filter(line => line.trim())
    return lines.map(line => line.trim()).filter(line => line.length > 0)
  }

  const summaryLines = formatSummary(summary)

  return (
    <div 
      className="fixed inset-0 bg-black/50 z-50 flex items-start justify-center"
      onClick={handleBackdropClick}
    >
      <div className="w-full max-w-2xl mt-20 mx-4 bg-[var(--surface)] rounded-lg shadow-xl border border-[var(--border)] animate-slide-down">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[var(--border)]">
          <h3 className="text-lg font-semibold text-[var(--text-primary)]">
            Channel Summary
          </h3>
          <button
            onClick={onClose}
            className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* Content */}
        <div className="max-h-[60vh] overflow-y-auto p-4">
          {error && (
            <div className="flex items-center justify-center py-8">
              <div className="text-red-500">{error}</div>
            </div>
          )}
          
          {isLoading && !summary && !error && (
            <div className="space-y-3">
              <div className="h-4 shimmer rounded w-3/4" />
              <div className="h-4 shimmer rounded w-full" />
              <div className="h-4 shimmer rounded w-5/6" />
              <div className="h-4 shimmer rounded w-2/3" />
              <div className="h-4 shimmer rounded w-4/5" />
            </div>
          )}
          
          {!isLoading && !error && summaryLines.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-start space-x-2 mb-4">
                <div className="w-8 h-8 rounded-full bg-space-cyan flex items-center justify-center text-[var(--bg)] font-bold">
                  🤖
                </div>
                <div className="flex-1">
                  <p className="text-sm text-[var(--text-secondary)] mb-1">
                    AI-generated summary of recent messages
                  </p>
                  <div className="space-y-2">
                    {summaryLines.map((line, index) => (
                      <div key={index} className="flex items-start space-x-2">
                        <span className="text-space-cyan text-sm mt-0.5">•</span>
                        <p className="text-sm text-[var(--text-primary)] leading-relaxed">
                          {line}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {!isLoading && !error && summaryLines.length === 0 && (
            <div className="flex items-center justify-center py-8">
              <div className="text-[var(--text-secondary)]">No summary available</div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}