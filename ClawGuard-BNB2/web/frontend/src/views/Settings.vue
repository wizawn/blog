<template>
  <div class="settings">
    <el-tabs type="border-card">
      <!-- 交易模式 -->
      <el-tab-pane label="交易模式">
        <el-card shadow="never">
          <el-form label-width="120px">
            <el-form-item label="当前模式">
              <el-radio-group v-model="tradingMode" @change="changeTradingMode">
                <el-radio label="paper">
                  <el-tag type="info">模拟盘</el-tag>
                  <span style="margin-left: 10px">本地模拟，无需API</span>
                </el-radio>
                <el-radio label="testnet">
                  <el-tag type="warning">测试网</el-tag>
                  <span style="margin-left: 10px">币安测试网络</span>
                </el-radio>
                <el-radio label="live">
                  <el-tag type="danger">实盘</el-tag>
                  <span style="margin-left: 10px">真实交易，谨慎使用</span>
                </el-radio>
              </el-radio-group>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 代理设置 -->
      <el-tab-pane label="代理设置">
        <el-card shadow="never">
          <el-form :model="proxyConfig" label-width="120px">
            <el-form-item label="启用代理">
              <el-switch v-model="proxyConfig.enabled" />
            </el-form-item>
            <el-form-item label="代理类型">
              <el-select v-model="proxyConfig.type" :disabled="!proxyConfig.enabled">
                <el-option label="HTTP" value="http" />
                <el-option label="HTTPS" value="https" />
                <el-option label="SOCKS5" value="socks5" />
              </el-select>
            </el-form-item>
            <el-form-item label="主机">
              <el-input v-model="proxyConfig.host" :disabled="!proxyConfig.enabled" />
            </el-form-item>
            <el-form-item label="端口">
              <el-input-number v-model="proxyConfig.port" :disabled="!proxyConfig.enabled" />
            </el-form-item>
            <el-form-item label="用户名">
              <el-input v-model="proxyConfig.username" :disabled="!proxyConfig.enabled" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="proxyConfig.password" type="password" :disabled="!proxyConfig.enabled" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveProxyConfig">保存配置</el-button>
              <el-button @click="testProxy" :disabled="!proxyConfig.enabled">测试连接</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 系统配置 -->
      <el-tab-pane label="系统配置">
        <el-card shadow="never">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="版本">1.0.0</el-descriptions-item>
            <el-descriptions-item label="Python">3.8+</el-descriptions-item>
            <el-descriptions-item label="配置目录">~/.clawguard</el-descriptions-item>
            <el-descriptions-item label="日志级别">INFO</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-tab-pane>

      <!-- NLP 测试 -->
      <el-tab-pane label="NLP 测试">
        <el-card shadow="never">
          <el-form label-width="120px">
            <el-form-item label="自然语言输入">
              <el-input
                v-model="nlpInput"
                type="textarea"
                :rows="3"
                placeholder="例如：用1000 USDT买入BTC"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="parseNLP">解析</el-button>
            </el-form-item>
            <el-form-item v-if="nlpResult" label="解析结果">
              <pre>{{ JSON.stringify(nlpResult, null, 2) }}</pre>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiClient } from '@/api/client'
import { ElMessage } from 'element-plus'

const tradingMode = ref('paper')
const proxyConfig = ref({
  enabled: false,
  type: 'http',
  host: '127.0.0.1',
  port: 7890,
  username: '',
  password: ''
})
const nlpInput = ref('')
const nlpResult = ref(null)

const loadTradingMode = async () => {
  try {
    const res = await apiClient.get('/api/settings/trading-mode')
    if (res.data.success) {
      tradingMode.value = res.data.data.current_mode
    }
  } catch (error) {
    console.error('加载交易模式失败:', error)
  }
}

const changeTradingMode = async (mode) => {
  try {
    const res = await apiClient.post('/api/settings/trading-mode', { mode })
    if (res.data.success) {
      ElMessage.success(`已切换到${mode}模式`)
    }
  } catch (error) {
    console.error('切换交易模式失败:', error)
  }
}

const loadProxyConfig = async () => {
  try {
    const res = await apiClient.get('/api/settings/proxy')
    if (res.data.success) {
      proxyConfig.value = res.data.data
    }
  } catch (error) {
    console.error('加载代理配置失败:', error)
  }
}

const saveProxyConfig = async () => {
  try {
    const res = await apiClient.post('/api/settings/proxy', proxyConfig.value)
    if (res.data.success) {
      ElMessage.success('代理配置已保存')
    }
  } catch (error) {
    console.error('保存代理配置失败:', error)
  }
}

const testProxy = async () => {
  try {
    const res = await apiClient.post('/api/settings/proxy/test')
    if (res.data.success) {
      ElMessage.success('代理连接成功')
    }
  } catch (error) {
    console.error('测试代理失败:', error)
  }
}

const parseNLP = async () => {
  try {
    const res = await apiClient.post('/api/settings/nlp/parse', {
      text: nlpInput.value
    })
    if (res.data.success) {
      nlpResult.value = res.data.data
    }
  } catch (error) {
    console.error('NLP解析失败:', error)
  }
}

onMounted(() => {
  loadTradingMode()
  loadProxyConfig()
})
</script>

<style scoped>
pre {
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  overflow-x: auto;
}
</style>
