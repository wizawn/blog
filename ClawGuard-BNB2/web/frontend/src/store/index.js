import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const tradingMode = ref('paper')
  const apiConnected = ref(false)
  const totalBalance = ref(0)
  const todayPnl = ref(0)

  const setTradingMode = (mode) => {
    tradingMode.value = mode
  }

  const setApiConnected = (status) => {
    apiConnected.value = status
  }

  const setBalance = (balance) => {
    totalBalance.value = balance
  }

  const setPnl = (pnl) => {
    todayPnl.value = pnl
  }

  return {
    tradingMode,
    apiConnected,
    totalBalance,
    todayPnl,
    setTradingMode,
    setApiConnected,
    setBalance,
    setPnl
  }
})
