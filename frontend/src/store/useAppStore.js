import { create } from 'zustand'

export const useAppStore = create((set) => ({
  activeServerId: null,
  activeChannelId: null,
  activeChannelName: '',
  isMemberListOpen: false,
  
  setActiveServer: (serverId) => set({ 
    activeServerId: serverId, 
    activeChannelId: null,
    activeChannelName: ''
  }),
  
  setActiveChannel: (channelId, channelName) => set({ 
    activeChannelId: channelId,
    activeChannelName: channelName || ''
  }),
  
  setActiveChannelName: (channelName) => set({ activeChannelName: channelName }),
  
  toggleMemberList: () => set((state) => ({ 
    isMemberListOpen: !state.isMemberListOpen 
  })),
}))