import { format } from 'date-fns'
import { useAuthStore } from '../../store/useAuthStore'

export default function MessageBubble({ message, showAvatar }) {
  const { user } = useAuthStore()
  const isOwnMessage = user?.id === message.user_id

  const formattedTime = message.timestamp 
    ? format(new Date(message.timestamp), 'HH:mm')
    : ''

  return (
    <div className={`flex ${isOwnMessage ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex max-w-[70%] ${isOwnMessage ? 'flex-row-reverse' : 'flex-row'}`}>
        {showAvatar && !isOwnMessage && (
          <div className="w-10 h-10 rounded-full bg-space-cyan flex items-center justify-center text-[var(--bg)] font-bold flex-shrink-0 mr-3">
            {message.username.charAt(0).toUpperCase()}
          </div>
        )}
        
        {showAvatar && isOwnMessage && (
          <div className="w-10 flex-shrink-0 ml-3" />
        )}
        
        <div className={`flex flex-col ${isOwnMessage ? 'items-end' : 'items-start'}`}>
          {showAvatar && (
            <div className={`flex items-baseline space-x-2 mb-1 ${isOwnMessage ? 'justify-end' : 'justify-start'}`}>
              <span className="text-sm font-semibold text-[var(--text-primary)]">
                {message.username}
              </span>
              <span className="text-xs text-[var(--text-secondary)]">
                {formattedTime}
              </span>
            </div>
          )}
          
          <div className={`px-3 py-2 rounded-lg ${
            isOwnMessage 
              ? 'bg-[var(--own-bubble)] text-[var(--own-bubble-text)]' 
              : 'bg-[var(--other-bubble)] text-[var(--other-bubble-text)]'
          }`}>
            <p className="text-sm break-words">{message.content}</p>
          </div>
        </div>
        
        {!showAvatar && !isOwnMessage && (
          <div className="w-10 flex-shrink-0 mr-3" />
        )}
      </div>
    </div>
  )
}