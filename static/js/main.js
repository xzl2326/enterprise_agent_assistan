// static/js/main.js

// 【修复点1】抽取API路径常量，避免硬编码，提升可维护性
const API_CONSTANTS = {
  CHAT: '/api/v1/chat',
  CHAT_STREAM: '/api/v1/chat/stream',
  HEALTH: '/api/v1/health',
  TOOLS: '/api/v1/tools',
  KNOWLEDGE_UPLOAD: '/api/v1/knowledge/upload',
  QDRANT_HEALTH: 'http://localhost:6333/health' // Qdrant健康检查正确接口
};

// 全局变量
let currentTab = 'chat';
let chatHistory = [];
let streamEventSource = null;
let isRequestPending = false; // 【修复点2】添加请求防抖标记
let activeStreamReader = null; // 【修复点3】流式响应中断标记

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
  // 初始化标签页
  switchTab('chat');

  // 检查系统健康状态
  checkAllHealth();

  // 加载工具列表
  loadTools();

  // 设置文件上传事件
  setupFileUpload();

  // 更新状态指示器
  updateStatusIndicator();

  // 【修复点4】绑定输入框按键事件（原缺失）
  bindInputEvents();

  // 【修复点5】绑定清空/导出聊天记录按钮事件（原缺失）
  bindChatActionEvents();

  // 【修复点6】从localStorage恢复聊天历史（持久化）
  restoreChatHistory();
});

// 【修复点7】绑定输入框按键事件
function bindInputEvents() {
  const chatInput = document.getElementById('chat-input');
  const streamInput = document.getElementById('stream-input');

  if (chatInput) {
    chatInput.addEventListener('keypress', handleChatKeyPress);
  }

  if (streamInput) {
    streamInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendStreamMessage();
      }
    });
  }
}

// 【修复点8】绑定清空/导出聊天按钮事件
function bindChatActionEvents() {
  const clearBtn = document.getElementById('clear-chat-btn');
  const exportBtn = document.getElementById('export-chat-btn');
  const abortStreamBtn = document.getElementById('abort-stream-btn'); // 流式中断按钮

  if (clearBtn) clearBtn.addEventListener('click', clearChat);
  if (exportBtn) exportBtn.addEventListener('click', exportChat);
  if (abortStreamBtn) abortStreamBtn.addEventListener('click', abortStreamResponse);
}

// 【修复点9】流式响应中断功能
function abortStreamResponse() {
  if (activeStreamReader) {
    activeStreamReader.cancel(); // 取消Reader读取
    activeStreamReader = null;
    const loadingMsg = document.querySelector('.message.loading');
    if (loadingMsg) {
      updateMessage(loadingMsg.id, '流式响应已手动中断');
    }
  }
}

// 切换标签页
function switchTab(tabName) {
  // 隐藏所有标签页
  document.querySelectorAll('.tab-content').forEach(tab => {
    tab.classList.remove('active');
  });

  // 移除所有按钮的激活状态
  document.querySelectorAll('.sidebar-btn').forEach(btn => {
    btn.classList.remove('active');
  });

  // 显示选中的标签页
  const tabElement = document.getElementById(tabName + '-tab');
  if (tabElement) {
    tabElement.classList.add('active');
  }

  // 激活对应的侧边栏按钮
  const activeBtn = document.querySelector(`.sidebar-btn[onclick*="${tabName}"]`);
  if (activeBtn) {
    activeBtn.classList.add('active');
  }

  currentTab = tabName;

  // 如果是流式聊天标签，确保之前的连接已关闭
  if (tabName !== 'stream-chat' && streamEventSource) {
    streamEventSource.close();
    streamEventSource = null;
  }
}

// 【修复点10】添加XSS防护函数，避免恶意注入
function escapeHtml(unsafe) {
  if (!unsafe) return '';
  return unsafe.replace(/[&<>"']/g, function(m) {
    return ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    })[m];
  });
}

// 发送聊天消息（增加防抖）
async function sendChatMessage() {
  // 防抖：如果已有请求pending，直接返回
  if (isRequestPending) return;

  const input = document.getElementById('chat-input');
  const message = input.value.trim();

  if (!message) return;

  // 添加用户消息到界面（带XSS转义）
  addMessage('user', escapeHtml(message));
  input.value = '';

  // 显示加载状态
  const loadingId = addMessage('assistant', '思考中...', true);

  try {
    isRequestPending = true; // 标记请求开始

    // 检查是否启用流式响应
    const streamMode = document.getElementById('stream-mode').checked;

    if (streamMode) {
      // 流式响应
      await sendStreamChat(message, loadingId);
    } else {
      // 普通响应
      const response = await fetch(API_CONSTANTS.CHAT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: message })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // 更新消息内容（带XSS转义）
      updateMessage(loadingId, escapeHtml(data.data.answer));

      // 添加到历史记录
      addToChatHistory('user', message);
      addToChatHistory('assistant', data.data.answer);
    }
  } catch (error) {
    console.error('发送消息失败:', error);
    updateMessage(loadingId, `抱歉，发送消息时出现错误: ${escapeHtml(error.message)}`);
  } finally {
    isRequestPending = false; // 标记请求结束
  }
}

// 发送流式聊天消息（stream-chat标签页）
async function sendStreamMessage() {
  if (isRequestPending) return;

  const input = document.getElementById('stream-input');
  const message = input.value.trim();

  if (!message) return;

  // 添加用户消息到界面（带XSS转义）
  addMessage('user', escapeHtml(message), false, 'stream-messages');
  input.value = '';

  // 显示加载状态
  const loadingId = addMessage('assistant', '', true, 'stream-messages');

  try {
    isRequestPending = true;
    await handleStreamResponse(message, loadingId, 'stream-messages');
  } catch (error) {
    console.error('发送流式消息失败:', error);
    updateMessage(loadingId, `抱歉，发送消息时出现错误: ${escapeHtml(error.message)}`);
  } finally {
    isRequestPending = false;
  }
}

// 流式聊天（普通聊天界面的流式模式）
async function sendStreamChat(message, loadingId) {
  try {
    await handleStreamResponse(message, loadingId, 'chat-messages');
  } catch (error) {
    console.error('流式聊天失败:', error);
    updateMessage(loadingId, `抱歉，流式聊天时出现错误: ${escapeHtml(error.message)}`);
  }
}

// 【修复点11】抽取流式响应公共逻辑，消除代码重复
async function handleStreamResponse(message, loadingId, containerId) {
  const response = await fetch(API_CONSTANTS.CHAT_STREAM, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ message: message })
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  // 读取流式响应
  const reader = response.body.getReader();
  activeStreamReader = reader; // 绑定中断标记
  const decoder = new TextDecoder();
  let fullResponse = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.substring(6);
        if (data === '[DONE]') break;

        try {
          const parsed = JSON.parse(data);
          if (parsed.content) {
            fullResponse += parsed.content;
            // 带XSS转义更新消息
            updateMessage(loadingId, escapeHtml(fullResponse));
          }
        } catch (e) {
          // 忽略解析错误
        }
      }
    }
  }

  // 清空中断标记
  activeStreamReader = null;

  // 添加到历史记录
  addToChatHistory('user', message);
  addToChatHistory('assistant', fullResponse);
}

// 添加消息到界面（优化XSS防护）
function addMessage(role, content, isLoading = false, containerId = 'chat-messages') {
  const messagesContainer = document.getElementById(containerId);
  if (!messagesContainer) return '';

  const messageId = 'msg-' + Date.now();

  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${role} ${isLoading ? 'loading' : ''}`;
  messageDiv.id = messageId;

  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';

  if (isLoading) {
    contentDiv.innerHTML = `<strong>🤖 智能助手</strong><p><i class="fas fa-spinner fa-spin"></i> ${escapeHtml(content)}</p>`;
  } else {
    const roleName = role === 'user' ? '👤 您' : '🤖 智能助手';
    contentDiv.innerHTML = `<strong>${roleName}</strong><p>${content}</p>`; // content已转义
  }

  messageDiv.appendChild(contentDiv);
  messagesContainer.appendChild(messageDiv);

  // 滚动到底部
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  return messageId;
}

// 更新消息内容（优化XSS防护）
function updateMessage(messageId, newContent) {
  const messageElement = document.getElementById(messageId);
  if (messageElement) {
    const contentElement = messageElement.querySelector('.message-content');
    if (contentElement) {
      contentElement.innerHTML = `<strong>🤖 智能助手</strong><p>${newContent}</p>`; // newContent已转义

      // 滚动到底部
      const messagesContainer = messageElement.closest('.messages');
      if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      }
    }
  }
}

// 处理聊天输入框按键
function handleChatKeyPress(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendChatMessage();
  }
}

// 清空聊天记录
function clearChat() {
  if (confirm('确定要清空当前对话记录吗？')) {
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.innerHTML = `
      <div class="message welcome">
        <div class="message-content">
          <strong>🤖 智能助手</strong>
          <p>对话记录已清空！请开始新的对话。</p>
        </div>
      </div>
    `;
    chatHistory = [];
    // 【修复点12】清空localStorage
    localStorage.removeItem('chatHistory');
  }
}

// 导出聊天记录
function exportChat() {
  if (chatHistory.length === 0) {
    alert('没有聊天记录可以导出');
    return;
  }

  const exportData = {
    timestamp: new Date().toISOString(),
    history: chatHistory
  };

  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `chat-history-${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// 【修复点13】聊天历史持久化（添加到历史+存localStorage）
function addToChatHistory(role, content) {
  chatHistory.push({ role, content });
  localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
}

// 【修复点14】从localStorage恢复聊天历史
function restoreChatHistory() {
  const savedHistory = localStorage.getItem('chatHistory');
  if (savedHistory) {
    chatHistory = JSON.parse(savedHistory);
    // 重新渲染历史消息
    const messagesContainer = document.getElementById('chat-messages');
    if (messagesContainer) {
      messagesContainer.innerHTML = '';
      chatHistory.forEach(item => {
        addMessage(item.role, escapeHtml(item.content));
      });
    }
  }
}

// 设置文件上传
function setupFileUpload() {
  const dropArea = document.getElementById('drop-area');
  const fileInput = document.getElementById('file-input');

  if (!dropArea || !fileInput) return;

  // 点击上传区域触发文件选择
  dropArea.addEventListener('click', () => {
    fileInput.click();
  });

  // 文件选择变化
  fileInput.addEventListener('change', handleFileSelect);

  // 拖放事件
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  ['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, highlight, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, unhighlight, false);
  });

  function highlight() {
    dropArea.style.borderColor = '#667eea';
    dropArea.style.backgroundColor = '#f8f9ff';
  }

  function unhighlight() {
    dropArea.style.borderColor = '#ddd';
    dropArea.style.backgroundColor = '';
  }

  // 处理文件放置
  dropArea.addEventListener('drop', handleDrop, false);

  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
  }
}

// 处理文件选择
function handleFileSelect(e) {
  const files = e.target.files;
  handleFiles(files);
  // 【修复点15】文件上传后重置input，支持重复选择同一文件
  e.target.value = '';
}

// 处理文件上传
async function handleFiles(files) {
  if (!files || files.length === 0) return;

  const uploadedFilesDiv = document.getElementById('uploaded-files');
  const progressDiv = document.getElementById('upload-progress');
  const progressFill = document.getElementById('progress-fill');
  const progressText = document.getElementById('progress-text');

  if (!uploadedFilesDiv || !progressDiv || !progressFill || !progressText) return;

  // 显示进度条
  progressDiv.style.display = 'block';

  let uploadedCount = 0;
  const totalFiles = files.length;

  for (let i = 0; i < files.length; i++) {
    const file = files[i];

    // 更新进度
    progressFill.style.width = `${(i / totalFiles) * 100}%`;
    progressText.textContent = `正在上传 ${i + 1}/${totalFiles}: ${escapeHtml(file.name)}`;

    try {
      // 创建FormData
      const formData = new FormData();
      formData.append('file', file);

      // 发送到服务器
      const response = await fetch(API_CONSTANTS.KNOWLEDGE_UPLOAD, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`上传失败: ${response.status}`);
      }

      const result = await response.json();
      uploadedCount++;

      // 添加到已上传文件列表（带XSS转义）
      const fileItem = document.createElement('div');
      fileItem.className = 'file-item';
      fileItem.innerHTML = `
        <div class="file-info">
          <i class="fas fa-file-alt"></i>
          <div>
            <strong>${escapeHtml(file.name)}</strong>
            <p>大小: ${formatFileSize(file.size)} | 状态: 上传成功</p>
          </div>
        </div>
      `;
      uploadedFilesDiv.appendChild(fileItem);

    } catch (error) {
      console.error('文件上传失败:', error);

      // 显示错误（带XSS转义）
      const errorItem = document.createElement('div');
      errorItem.className = 'file-item error';
      errorItem.innerHTML = `
        <div class="file-info">
          <i class="fas fa-exclamation-circle"></i>
          <div>
            <strong>${escapeHtml(file.name)}</strong>
            <p>上传失败: ${escapeHtml(error.message)}</p>
          </div>
        </div>
      `;
      uploadedFilesDiv.appendChild(errorItem);
    }
  }

  // 完成上传
  progressFill.style.width = '100%';
  progressText.textContent = `上传完成！成功上传 ${uploadedCount}/${totalFiles} 个文件`;

  // 3秒后隐藏进度条
  setTimeout(() => {
    progressDiv.style.display = 'none';
    progressFill.style.width = '0%';
  }, 3000);
}

// 格式化文件大小
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 加载工具列表
async function loadTools() {
  const toolsGrid = document.getElementById('tools-grid');
  if (!toolsGrid) return;

  try {
    const response = await fetch(API_CONSTANTS.TOOLS);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    if (data.success && data.data.tools) {
      toolsGrid.innerHTML = '';

      Object.entries(data.data.tools).forEach(([toolName, toolInfo]) => {
        const toolCard = document.createElement('div');
        toolCard.className = 'tool-card';

        // 根据工具类型选择图标
        const icon = getToolIcon(toolName);

        // 格式化参数显示（带XSS转义）
        const paramsHtml = Object.entries(toolInfo.parameters || {})
          .map(([paramName, paramDesc]) =>
            `<div><strong>${escapeHtml(paramName)}:</strong> ${escapeHtml(paramDesc)}</div>`
          )
          .join('');

        toolCard.innerHTML = `
          <div class="tool-icon">
            <i class="${icon}"></i>
          </div>
          <h3>${escapeHtml(toolName)}</h3>
          <p>${escapeHtml(toolInfo.description)}</p>
          <div class="tool-params">
            ${paramsHtml || '无参数'}
          </div>
        `;

        toolsGrid.appendChild(toolCard);
      });
    }
  } catch (error) {
    console.error('加载工具列表失败:', error);
    toolsGrid.innerHTML = `
      <div class="error">
        <i class="fas fa-exclamation-triangle"></i>
        <p>加载工具列表失败: ${escapeHtml(error.message)}</p>
      </div>
    `;
  }
}

// 获取工具图标
function getToolIcon(toolName) {
  const iconMap = {
    'web_search': 'fas fa-search',
    'search_and_summarize': 'fas fa-search-plus',
    'read_file': 'fas fa-file-alt',
    'write_file': 'fas fa-file-export',
    'list_files': 'fas fa-folder-open',
    'analyze_file': 'fas fa-chart-bar',
    'call_api': 'fas fa-exchange-alt',
    'get_weather': 'fas fa-cloud-sun',
    'get_exchange_rate': 'fas fa-money-bill-wave'
  };

  return iconMap[toolName] || 'fas fa-toolbox';
}

// 检查所有健康状态
async function checkAllHealth() {
  await checkAPIHealth();
  await checkQdrantHealth();
  await checkModelHealth();
}

// 检查API健康状态
async function checkAPIHealth() {
  const healthCard = document.getElementById('api-health');
  if (!healthCard) return;

  const statusElement = healthCard.querySelector('.health-status');
  if (!statusElement) return;

  try {
    const response = await fetch(API_CONSTANTS.HEALTH);
    if (response.ok) {
      const data = await response.json();
      statusElement.textContent = '健康';
      statusElement.className = 'health-status healthy';
      healthCard.querySelector('.health-detail').textContent = `服务: ${escapeHtml(data.service)}, 版本: ${escapeHtml(data.version)}`;
    } else {
      throw new Error(`HTTP ${response.status}`);
    }
  } catch (error) {
    statusElement.textContent = '异常';
    statusElement.className = 'health-status unhealthy';
    healthCard.querySelector('.health-detail').textContent = `错误: ${escapeHtml(error.message)}`;
  }
}

// 【修复点16】补全Qdrant健康检查（修复截断+no-cors问题）
async function checkQdrantHealth() {
  const healthCard = document.getElementById('qdrant-health');
  if (!healthCard) return;

  const statusElement = healthCard.querySelector('.health-status');
  if (!statusElement) return;

  try {
    // 修复：使用Qdrant官方健康检查接口，移除no-cors（否则无法读取响应）
    const response = await fetch(API_CONSTANTS.QDRANT_HEALTH, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      },
      // 若跨域需后端配置CORS，此处移除no-cors以获取真实状态
    });

    if (response.ok) {
      const healthData = await response.json();
      statusElement.textContent = '运行中';
      statusElement.className = 'health-status healthy';
      healthCard.querySelector('.health-detail').textContent = `状态: ${escapeHtml(healthData.status)} | 版本: ${escapeHtml(healthData.version || '未知')}`;
    } else {
      throw new Error(`Qdrant响应异常: ${response.status}`);
    }
  } catch (error) {
    statusElement.textContent = '异常';
    statusElement.className = 'health-status unhealthy';
    healthCard.querySelector('.health-detail').textContent = `错误: ${escapeHtml(error.message)}`;
  }
}

// 【修复点17】实现缺失的checkModelHealth函数
async function checkModelHealth() {
  const healthCard = document.getElementById('model-health');
  if (!healthCard) return;

  const statusElement = healthCard.querySelector('.health-status');
  if (!statusElement) return;

  try {
    // 假设模型健康检查接口为/api/v1/health/model，需根据实际后端调整
    const response = await fetch('/api/v1/health/model');
    if (response.ok) {
      const data = await response.json();
      statusElement.textContent = '加载完成';
      statusElement.className = 'health-status healthy';
      healthCard.querySelector('.health-detail').textContent = `模型: ${escapeHtml(data.model_name)}, 状态: ${escapeHtml(data.status)}`;
    } else {
      throw new Error(`HTTP ${response.status}`);
    }
  } catch (error) {
    statusElement.textContent = '未加载';
    statusElement.className = 'health-status unhealthy';
    healthCard.querySelector('.health-detail').textContent = `错误: ${escapeHtml(error.message)}`;
  }
}

// 【修复点18】实现缺失的updateStatusIndicator函数
function updateStatusIndicator() {
  const statusIndicator = document.getElementById('system-status-indicator');
  if (!statusIndicator) return;

  // 检查核心服务状态
  const apiStatus = document.querySelector('#api-health .health-status');
  const qdrantStatus = document.querySelector('#qdrant-health .health-status');
  const modelStatus = document.querySelector('#model-health .health-status');

  // 所有核心服务健康则显示绿色，否则红色
  if (apiStatus?.classList.contains('healthy') &&
      qdrantStatus?.classList.contains('healthy') &&
      modelStatus?.classList.contains('healthy')) {
    statusIndicator.className = 'status-indicator online';
    statusIndicator.title = '系统所有服务正常运行';
  } else {
    statusIndicator.className = 'status-indicator offline';
    statusIndicator.title = '部分服务异常，请检查';
  }
}