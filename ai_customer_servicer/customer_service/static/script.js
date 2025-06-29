// 全局变量
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const chatHistory = document.getElementById('chatHistory');
let isTyping = false;
let currentChatId = null;
let isSearchMode = false; // 新增：标记是否处于搜索模式

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    messageInput.focus();
    setupEventListeners();
    loadChatHistory();
    addWelcomeMessageWithFAQ(); // 新欢迎气泡
    // 退出按钮逻辑
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            fetch('/logout/', {
                method: 'GET',
                credentials: 'same-origin'
            }).then(function() {
                window.location.href = '/login/';
            });
        });
    }
});

// 设置事件监听器
function setupEventListeners() {
    // 输入框自动调整高度和按钮状态
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
        updateSendButtonState();
    });

    // 回车发送消息
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

// 更新发送按钮状态
function updateSendButtonState() {
    const hasContent = messageInput.value.trim().length > 0;
    sendButton.disabled = !hasContent || isTyping;
}

// 发送消息函数
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isTyping) return;

    try {
        // 添加用户消息到界面
        addMessage(message, 'user');
        clearInput();
        setTypingState(true);
        showTypingIndicator();
        
        // 发送请求到后端（Django接口）
        if (!currentChatId) {
            // 如果没有当前对话，先新建
            const chatResp = await fetch('/api/chats/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN},
                body: JSON.stringify({ title: '新对话' })
            });
            const chatData = await chatResp.json();
            currentChatId = chatData.id;
        }
        const response = await fetch(`/api/chats/${currentChatId}/send/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN},
            body: JSON.stringify({ message: message })
        });
        const data = await response.json();
        hideTypingIndicator();
        if (data.ai_reply) {
            showStreamingMessage(data.ai_reply, 'bot');
            loadChatHistory();
        } else {
            addMessage(data.error || '抱歉，出现了一些问题，请稍后再试。', 'bot');
        }
    } catch (error) {
        console.error('发送消息失败:', error);
        hideTypingIndicator();
        addMessage('抱歉，网络连接出现问题，请检查网络连接后重试。', 'bot');
    } finally {
        setTypingState(false);
        messageInput.focus();
    }
}

// 创建新聊天
async function startNewChat() {
    try {
        const response = await fetch('/api/chats/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN},
            body: JSON.stringify({ title: '新对话' })
        });
        const data = await response.json();
        if (data.id) {
            clearChatMessages();
            addMessage('您好！我是"聆析智服"AI客服，请问您需要什么帮助？', 'bot');
            currentChatId = data.id;
            loadChatHistory();
            messageInput.focus();
            showMessage('已开始新的对话', 'success');
        } else {
            showMessage('创建新聊天失败', 'error');
        }
    } catch (error) {
        console.error('创建新聊天失败:', error);
        showMessage('创建新聊天失败', 'error');
    }
}

// 搜索聊天记录
async function searchChats() {
    const searchButton = document.querySelector('.action-btn[onclick="searchChats()"]');
    if (isSearchMode) {
        exitSearchMode();
        return;
    }
    enterSearchMode(searchButton);
}

// 新增函数：进入搜索模式
function enterSearchMode(searchButton) {
    isSearchMode = true;
    
    // 保存原始内容
    const originalContent = searchButton.innerHTML;
    
    // 创建搜索输入框
    searchButton.innerHTML = `
        <div class="search-input-container">
            <input 
                type="text" 
                class="search-input" 
                placeholder="输入搜索关键词..."
                autocomplete="off"
            />
            <div class="search-actions">
                <button class="search-confirm-btn" title="搜索">🔍</button>
                <button class="search-cancel-btn" title="取消">✕</button>
            </div>
        </div>
    `;
    
    // 添加搜索模式样式
    searchButton.classList.add('search-mode');
    
    const searchInput = searchButton.querySelector('.search-input');
    const confirmBtn = searchButton.querySelector('.search-confirm-btn');
    const cancelBtn = searchButton.querySelector('.search-cancel-btn');
    
    // 聚焦到输入框
    setTimeout(() => {
        searchInput.focus();
    }, 100);
    
    // 执行搜索的函数
    const performSearch = async () => {
        const keyword = searchInput.value.trim();
        // 允许空关键词，空时查全部
        try {
            const response = await fetch(`/api/chats/search/?keyword=${encodeURIComponent(keyword)}`);
            const data = await response.json();
            if (Array.isArray(data)) {
                displayChatHistory(data);
                showMessage(`找到 ${data.length} 条相关记录`, 'info');
                exitSearchMode();
            } else {
                showMessage(data.error || '搜索失败', 'error');
            }
        } catch (error) {
            console.error('搜索失败:', error);
            showMessage('搜索失败', 'error');
        }
    };
    
    // 退出搜索模式的函数
    const exitSearch = () => {
        exitSearchMode();
    };
    
    // 绑定事件
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        } else if (e.key === 'Escape') {
            exitSearch();
        }
    });
    
    confirmBtn.addEventListener('click', performSearch);
    cancelBtn.addEventListener('click', exitSearch);
    
    // 点击其他地方退出搜索模式
    const handleClickOutside = (e) => {
        if (!searchButton.contains(e.target)) {
            exitSearch();
            document.removeEventListener('click', handleClickOutside);
        }
    };
    
    // 延迟添加全局点击监听，避免立即触发
    setTimeout(() => {
        document.addEventListener('click', handleClickOutside);
    }, 100);
    
    // 保存原始内容和清理函数
    searchButton._originalContent = originalContent;
    searchButton._clickOutsideHandler = handleClickOutside;
}

// 新增函数：退出搜索模式
function exitSearchMode() {
    const searchButton = document.querySelector('.action-btn.search-mode');
    if (!searchButton) return;
    
    isSearchMode = false;
    
    // 恢复原始内容
    if (searchButton._originalContent) {
        searchButton.innerHTML = searchButton._originalContent;
    } else {
        // 默认内容
        searchButton.innerHTML = `
            <span style="font-size: 16px;">🔍</span>
            查询聊天
        `;
    }
    
    // 移除搜索模式样式
    searchButton.classList.remove('search-mode');
    
    // 清理事件监听器
    if (searchButton._clickOutsideHandler) {
        document.removeEventListener('click', searchButton._clickOutsideHandler);
        delete searchButton._clickOutsideHandler;
    }
    
    delete searchButton._originalContent;
}

// 清空聊天记录
async function clearAllChats() {
    if (!confirm('确定要清空所有聊天记录吗？此操作不可恢复。')) return;
    if (isSearchMode) {
        exitSearchMode();
    }
    try {
        const response = await fetch('/api/chats/clear/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN}
        });
        const data = await response.json();
        if (data.message) {
            clearChatMessages();
            addMessage('您好！我是"聆析智服"AI客服，请问您需要什么帮助？', 'bot');
            chatHistory.innerHTML = '<div class="no-history">暂无聊天记录</div>';
            currentChatId = null;
            showMessage(data.message, 'success');
        } else {
            showMessage(data.error || '清空失败', 'error');
        }
    } catch (error) {
        console.error('清空失败:', error);
        showMessage('清空失败', 'error');
    }
}

// 加载聊天历史
async function loadChatHistory() {
    try {
        const response = await fetch('/api/chats/', {
            method: 'GET',
            headers: {'Content-Type': 'application/json'}
        });
        const data = await response.json();
        if (Array.isArray(data)) {
            displayChatHistory(data);
        } else {
            chatHistory.innerHTML = '<div class="no-history">暂无聊天记录</div>';
            console.error('加载聊天历史失败:', data.error);
        }
    } catch (error) {
        chatHistory.innerHTML = '<div class="no-history">暂无聊天记录</div>';
        console.error('加载聊天历史失败:', error);
    }
}

// 🔑 优化文本截断函数
function truncateText(text, maxLength) {
    if (!text) return '';
    
    // 清理文本：移除多余的空白字符和换行符
    const cleanText = text.replace(/\s+/g, ' ').trim();
    
    // 如果文本长度小于等于最大长度，直接返回
    if (cleanText.length <= maxLength) {
        return cleanText;
    }
    
    // 截取文本并添加省略号
    return cleanText.substring(0, maxLength) + '...';
}

// 🔑 获取智能预览文本
function getPreviewText(content) {
    if (!content) return '暂无消息';
    
    // 按行分割内容
    const lines = content.split(/\r?\n/).filter(line => line.trim().length > 0);
    
    if (lines.length === 0) return '暂无消息';
    
    // 获取第一行有效内容
    const firstLine = lines[0].trim();
    
    // 根据容器宽度动态调整截断长度
    const maxLength = window.innerWidth <= 768 ? 20 : 25;
    
    return truncateText(firstLine, maxLength);
}

// 🔑 获取智能标题
function getSmartTitle(content, defaultTitle = '新对话') {
    if (!content) return defaultTitle;
    
    // 清理并获取第一行内容作为标题
    const lines = content.split(/\r?\n/).filter(line => line.trim().length > 0);
    
    if (lines.length === 0) return defaultTitle;
    
    const firstLine = lines[0].trim();
    
    // 根据屏幕尺寸动态调整标题长度
    const maxLength = window.innerWidth <= 768 ? 15 : 20;
    
    return truncateText(firstLine, maxLength);
}

// 🔑 显示聊天历史 - 优化版本
function displayChatHistory(chats) {
    if (!chatHistory) return;
    
    if (chats.length === 0) {
        chatHistory.innerHTML = '<div class="no-history">暂无聊天记录</div>';
        return;
    }
    
    // 按日期分组
    const groupedChats = groupChatsByDate(chats);
    
    let html = '';
    for (const [date, chatList] of Object.entries(groupedChats)) {
        html += `<div class="history-group">
            <div class="history-group-title">${date}</div>`;
        
        chatList.forEach(chat => {
            const isActive = chat.id === currentChatId ? 'active' : '';
            const lastMessage = chat.last_message;
            
            // 🔑 优化标题显示
            const displayTitle = getSmartTitle(chat.title, '新对话');
            
            // 🔑 优化预览文本显示
            let preview = '暂无消息';
            if (lastMessage && lastMessage.content) {
                preview = getPreviewText(lastMessage.content);
            }
            
            // 🔑 优化时间显示
            const timeDisplay = lastMessage ? lastMessage.time : formatTime(chat.created_at);
            
            html += `
                <div class="history-item ${isActive}" onclick="loadChat('${chat.id}')">
                    <div class="history-item-content">
                        <div class="history-item-title" title="${escapeHtml(chat.title)}">${escapeHtml(displayTitle)}</div>
                        <div class="history-item-preview" title="${escapeHtml(lastMessage ? lastMessage.content : '')}">${escapeHtml(preview)}</div>
                        <div class="history-item-time">${escapeHtml(timeDisplay)}</div>
                    </div>
                    <div class="history-item-menu" onclick="showChatMenu(event, '${chat.id}')" title="更多操作">⋯</div>
                </div>`;
        });
        
        html += '</div>';
    }
    
    chatHistory.innerHTML = html;
}

// 按日期分组聊天
function groupChatsByDate(chats) {
    const grouped = {};
    const now = new Date();
    
    chats.forEach(chat => {
        const chatDate = new Date(chat.updated_at);
        const diffDays = Math.floor((now - chatDate) / (1000 * 60 * 60 * 24));
        
        let dateKey;
        if (diffDays === 0) {
            dateKey = '今天';
        } else if (diffDays === 1) {
            dateKey = '昨天';
        } else if (diffDays < 7) {
            dateKey = '本周';
        } else {
            dateKey = chatDate.toLocaleDateString('zh-CN', { 
                year: 'numeric', 
                month: 'long' 
            });
        }
        
        if (!grouped[dateKey]) {
            grouped[dateKey] = [];
        }
        grouped[dateKey].push(chat);
    });
    
    return grouped;
}

// 加载指定聊天
async function loadChat(chatId) {
    try {
        const response = await fetch(`/api/chats/${chatId}/messages/`);
        const data = await response.json();
        if (Array.isArray(data)) {
            currentChatId = chatId;
            clearChatMessages();
            data.forEach(msg => {
                addMessageWithTime(msg.content, msg.sender, formatTime(msg.created_at));
            });
            document.querySelectorAll('.history-item').forEach(item => {
                item.classList.remove('active');
            });
            const currentItem = document.querySelector(`.history-item[onclick="loadChat('${chatId}')"]`);
            if (currentItem) {
                currentItem.classList.add('active');
            }
            messageInput.focus();
            showMessage('聊天记录已加载', 'info');
        } else {
            showMessage(data.error || '加载失败', 'error');
        }
    } catch (error) {
        console.error('加载聊天失败:', error);
        showMessage('加载聊天失败', 'error');
    }
}

// 显示聊天菜单
function showChatMenu(event, chatId) {
    event.stopPropagation();
    
    if (confirm('确定要删除这个聊天记录吗？')) {
        deleteChat(chatId);
    }
}

// 删除聊天
async function deleteChat(chatId) {
    try {
        const response = await fetch(`/api/chats/${chatId}/`, {
            method: 'DELETE',
            headers: {'X-CSRFToken': window.CSRF_TOKEN}
        });
        const data = await response.json();
        if (data.message) {
            if (currentChatId === chatId) {
                clearChatMessages();
                addMessage('您好！我是"聆析智服"AI客服，请问您需要什么帮助？', 'bot');
                currentChatId = null;
            }
            loadChatHistory();
            showMessage('聊天记录已删除', 'success');
        } else {
            showMessage(data.error || '删除失败', 'error');
        }
    } catch (error) {
        console.error('删除聊天失败:', error);
        showMessage('删除失败', 'error');
    }
}

// 辅助函数
function addMessage(text, sender) {
    const time = new Date().toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    addMessageWithTime(text, sender, time);
}

function addMessageWithTime(text, sender, time) {
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const avatar = sender === 'bot' ? '🤖' : '👤';
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-text">${escapeHtml(text)}</div>
            <div class="message-time">${escapeHtml(time)}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function clearChatMessages() {
    if (chatMessages) {
        chatMessages.innerHTML = '';
    }
    hideTypingIndicator();
}

function clearInput() {
    messageInput.value = '';
    messageInput.style.height = 'auto';
    updateSendButtonState();
}

function setTypingState(typing) {
    isTyping = typing;
    updateSendButtonState();
}

function scrollToBottom() {
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

function showTypingIndicator() {
    hideTypingIndicator();
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot typing';
    typingDiv.id = 'typingIndicator';
    
    typingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="message-text">
                <div class="loading-dots">
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                </div>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(typingDiv);
    scrollToBottom();
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

function showMessage(text, type = 'info') {
    const colors = {
        success: '#34a853',
        error: '#ea4335',
        warning: '#fbbc04',
        info: '#4285f4'
    };
    
    const toast = document.createElement('div');
    toast.textContent = text;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${colors[type] || colors.info};
        color: white;
        padding: 12px 20px;
        border-radius: 6px;
        z-index: 10000;
        font-size: 14px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// 插入FAQ问题
function insertFAQ(question) {
    messageInput.value = question;
    messageInput.focus();
    messageInput.style.height = 'auto';
    messageInput.style.height = messageInput.scrollHeight + 'px';
    updateSendButtonState();
}

// 移动端菜单控制
function toggleMobileMenu() {
    const sidebar = document.getElementById('leftSidebar');
    const serviceCenter = document.getElementById('serviceCenter');
    const overlay = document.getElementById('mobileOverlay');
    
    sidebar.classList.toggle('open');
    serviceCenter.classList.toggle('open');
    overlay.classList.toggle('show');
}

// 点击遮罩层关闭菜单
document.addEventListener('DOMContentLoaded', function() {
    const overlay = document.getElementById('mobileOverlay');
    if (overlay) {
        overlay.addEventListener('click', function() {
            const sidebar = document.getElementById('leftSidebar');
            const serviceCenter = document.getElementById('serviceCenter');
            
            sidebar.classList.remove('open');
            serviceCenter.classList.remove('open');
            overlay.classList.remove('show');
        });
    }
});

// 🔑 新增：窗口大小改变时重新渲染历史记录
window.addEventListener('resize', function() {
    // 防抖处理
    clearTimeout(window.resizeTimer);
    window.resizeTimer = setTimeout(function() {
        // 重新加载聊天历史以适应新的屏幕尺寸
        loadChatHistory();
    }, 300);
});

// 新增：加载FAQ列表
async function loadFAQList() {
    try {
        const response = await fetch('/api/faqs/');
        const data = await response.json();
        if (Array.isArray(data)) {
            renderFAQGrid(data);
        }
    } catch (error) {
        console.error('加载FAQ失败:', error);
    }
}

// 新增：渲染FAQ区域
function renderFAQGrid(faqs) {
    const faqGrid = document.getElementById('faqGrid');
    if (!faqGrid) return;
    faqGrid.innerHTML = '';
    faqs.forEach(faq => {
        const faqItem = document.createElement('div');
        faqItem.className = 'faq-item';
        faqItem.onclick = () => sendFAQPolish(faq.id, faq.question);
        faqItem.innerHTML = `<div class="faq-question" title="${escapeHtml(faq.question)}">${escapeHtml(faq.question)}</div>`;
        faqGrid.appendChild(faqItem);
    });
}

// 新增：点击FAQ直接AI润色并显示
async function sendFAQPolish(faqId, question) {
    // 在对话区显示用户点击的问题
    addMessage(question, 'user');
    showTypingIndicator();
    setTypingState(true);
    try {
        const response = await fetch(`/api/faqs/${faqId}/polish/`);
        const data = await response.json();
        hideTypingIndicator();
        if (data.polished_answer) {
            showStreamingMessage(data.polished_answer, 'bot');
            loadChatHistory();
        } else {
            addMessage(data.error || 'AI润色失败', 'bot');
        }
    } catch (error) {
        hideTypingIndicator();
        addMessage('网络错误，AI润色失败', 'bot');
    } finally {
        setTypingState(false);
        messageInput.focus();
    }
}

// 流式输出AI回复
function showStreamingMessage(text, sender) {
    const time = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    if (!chatMessages) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    const avatar = sender === 'bot' ? '🤖' : '👤';

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-text"></div>
            <div class="message-time">${escapeHtml(time)}</div>
        </div>
    `;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();

    const messageTextDiv = messageDiv.querySelector('.message-text');
    let i = 0;
    function typeWriter() {
        if (i <= text.length) {
            messageTextDiv.innerHTML = escapeHtml(text.slice(0, i));
            i++;
            scrollToBottom();
            setTimeout(typeWriter, 15);
        }
    }
    typeWriter();
}

// 新增：欢迎气泡内渲染FAQ分组和主FAQ按钮组
async function addWelcomeMessageWithFAQ() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot';
    messageDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content welcome-message">
            <div class="ai-illustration-welcome"></div>
            <div class="welcome-title">聆析旗舰店</div>
            <div class="faq-groups" id="faqInBubble"></div>
            <div class="welcome-description">不知您有什么需要我帮忙的，你是想了解什么问题？还是想购买的咨询？</div>
        </div>
    `;
    chatMessages.appendChild(messageDiv);
    try {
        const response = await fetch('/api/chats/faq_groups/');
        const data = await response.json();
        // 渲染分组FAQ，li带data-faq-id
        const faqInBubble = messageDiv.querySelector('#faqInBubble');
        if (data.groups) {
            faqInBubble.innerHTML = data.groups.map(group => `
                <div class="faq-group">
                    <div class="faq-group-title">${group.group}</div>
                    <ul class="faq-list">
                        ${group.questions.map(q => `<li class="faq-list-item" data-faq-id="${q.id}">${q.question}</li>`).join('')}
                    </ul>
                </div>
            `).join('');
        }
        // 绑定点击事件：点击后直接请求AI润色接口并显示bot回复
        faqInBubble.querySelectorAll('.faq-list-item').forEach(item => {
            item.addEventListener('click', async function() {
                const faqId = this.getAttribute('data-faq-id');
                const question = this.textContent;
                addMessage(question, 'user');
                showTypingIndicator();
                setTypingState(true);
                try {
                    const resp = await fetch(`/api/faqs/${faqId}/polish/`);
                    const data = await resp.json();
                    hideTypingIndicator();
                    if (data.polished_answer) {
                        showStreamingMessage(data.polished_answer, 'bot');
                        loadChatHistory();
                    } else {
                        addMessage(data.error || 'AI润色失败', 'bot');
                    }
                } catch (e) {
                    hideTypingIndicator();
                    addMessage('网络错误，AI润色失败', 'bot');
                } finally {
                    setTypingState(false);
                    messageInput.focus();
                }
            });
        });
    } catch (e) {
        // 可选：显示FAQ加载失败提示
    }
    scrollToBottom();
}