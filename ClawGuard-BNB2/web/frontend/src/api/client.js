import axios from 'axios'
import { ElMessage } from 'element-plus'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 10000
})

// 请求拦截器
apiClient.interceptors.request.use(
  config => {
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  response => {
    return response
  },
  error => {
    console.error('响应错误:', error)

    let message = '请求失败'
    if (error.response) {
      message = error.response.data.error || `错误: ${error.response.status}`
    } else if (error.request) {
      message = '网络错误，请检查连接'
    }

    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export { apiClient }
