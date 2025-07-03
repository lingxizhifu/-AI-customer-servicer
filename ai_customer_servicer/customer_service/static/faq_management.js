// FAQ管理模块JavaScript代码 - 完整修复版
class FAQManager {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 10;
        this.currentFAQId = null;
        this.selectedFAQs = new Set();
        this.init();
    }

    init() {
        this.loadFAQs();
        this.bindEvents();
        this.loadCategories();
    }

    // 绑定事件
    bindEvents() {
        // 搜索按钮
        const searchBtn = document.querySelector('.search-btn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                this.currentPage = 1;
                this.loadFAQs();
            });
        }

        // 回车搜索
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.currentPage = 1;
                    this.loadFAQs();
                }
            });
        }

        // 筛选条件改变
        const categoryFilter = document.getElementById('categoryFilter');
        const statusFilter = document.getElementById('statusFilter');
        
        if (categoryFilter) {
            categoryFilter.addEventListener('change', () => {
                this.currentPage = 1;
                this.loadFAQs();
            });
        }
        
        if (statusFilter) {
            statusFilter.addEventListener('change', () => {
                this.currentPage = 1;
                this.loadFAQs();
            });
        }
    }

    // 获取CSRF Token - 修复版
    getCSRFToken() {
        // 优先从meta标签获取
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) {
            return metaToken.getAttribute('content');
        }
        
        // 从cookie获取
        const cookieValue = document.cookie.split(';')
            .find(row => row.trim().startsWith('csrftoken='));
        if (cookieValue) {
            return cookieValue.split('=')[1];
        }
        
        // 从DOM中的hidden input获取
        const hiddenInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (hiddenInput) {
            return hiddenInput.value;
        }
        
        console.warn('CSRF token not found');
        return '';
    }

    // 加载FAQ列表
    async loadFAQs() {
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                page_size: this.pageSize,
                search: document.querySelector('.search-input')?.value || '',
                category: document.getElementById('categoryFilter')?.value || '',
                status: document.getElementById('statusFilter')?.value || ''
            });

            const response = await fetch(`/api/faqs/?${params}`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('请先登录');
                }
                if (response.status === 403) {
                    throw new Error('权限不足');
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.renderFAQTable(data.faqs || []);
            this.renderPagination(data);
            this.updateStats(data.total || 0);
        } catch (error) {
            console.error('加载FAQ失败:', error);
            this.showMessage(error.message || '加载FAQ列表失败，请重试', 'error');
            
            // 如果是权限问题，显示空状态
            if (error.message.includes('登录') || error.message.includes('权限')) {
                this.renderFAQTable([]);
                this.updateStats(0);
            }
        }
    }

    // 渲染FAQ表格
    renderFAQTable(faqs) {
        const tbody = document.querySelector('.faq-table tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (faqs.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; padding: 40px; color: #64748b;">
                        暂无数据
                    </td>
                </tr>
            `;
            return;
        }

        faqs.forEach(faq => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <div style="font-weight: 500; margin-bottom: 4px;">${this.escapeHtml(faq.question)}</div>
                    <div style="font-size: 12px; color: #64748b; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${this.escapeHtml(faq.answer)}</div>
                </td>
                <td><span class="category-tag">${this.escapeHtml(faq.category)}</span></td>
                <td><span class="status-badge ${faq.is_main ? 'status-active' : 'status-inactive'}">●${faq.status_text}</span></td>
                <td>${faq.created_time}</td>
                <td>${faq.updated_time}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-icon btn-edit" title="编辑" onclick="faqManager.editFAQ(${faq.id})">✏️</button>
                        <button class="btn-icon btn-toggle" title="切换状态" onclick="faqManager.toggleFAQStatus(${faq.id})">${faq.is_main ? '🔒' : '🔓'}</button>
                        <button class="btn-icon btn-delete" title="删除" onclick="faqManager.deleteFAQ(${faq.id})">🗑️</button>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    // 渲染分页
    renderPagination(data) {
        const paginationControls = document.querySelector('.pagination-controls');
        const paginationInfo = document.querySelector('.pagination-info');
        
        if (!paginationControls) return;

        paginationControls.innerHTML = '';

        // 更新分页信息
        if (paginationInfo && data.total > 0) {
            const start = (data.current_page - 1) * this.pageSize + 1;
            const end = Math.min(data.current_page * this.pageSize, data.total);
            paginationInfo.textContent = `显示第 ${start}-${end} 条，共 ${data.total} 条记录`;
        } else if (paginationInfo) {
            paginationInfo.textContent = '显示第 0-0 条，共 0 条记录';
        }

        if (!data.total_pages || data.total_pages <= 1) return;

        // 上一页按钮
        const prevBtn = document.createElement('button');
        prevBtn.className = 'pagination-btn';
        prevBtn.textContent = '上一页';
        prevBtn.disabled = !data.has_previous;
        prevBtn.onclick = () => {
            if (data.has_previous) {
                this.currentPage--;
                this.loadFAQs();
            }
        };
        paginationControls.appendChild(prevBtn);

        // 页码按钮
        const startPage = Math.max(1, data.current_page - 2);
        const endPage = Math.min(data.total_pages, data.current_page + 2);

        for (let i = startPage; i <= endPage; i++) {
            const pageBtn = document.createElement('button');
            pageBtn.className = `pagination-btn ${i === data.current_page ? 'active' : ''}`;
            pageBtn.textContent = i;
            pageBtn.onclick = () => {
                this.currentPage = i;
                this.loadFAQs();
            };
            paginationControls.appendChild(pageBtn);
        }

        // 下一页按钮
        const nextBtn = document.createElement('button');
        nextBtn.className = 'pagination-btn';
        nextBtn.textContent = '下一页';
        nextBtn.disabled = !data.has_next;
        nextBtn.onclick = () => {
            if (data.has_next) {
                this.currentPage++;
                this.loadFAQs();
            }
        };
        paginationControls.appendChild(nextBtn);
    }

    // 更新统计信息
    updateStats(total) {
        const statsSpan = document.getElementById('total-count');
        if (statsSpan) {
            statsSpan.textContent = total;
        }
    }

    // 显示FAQ模态框
    showFAQModal(faqData = null) {
        const isEdit = !!faqData;
        this.currentFAQId = isEdit ? faqData.id : null;

        const modalHTML = `
            <div class="modal-overlay" id="faqModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>${isEdit ? '编辑FAQ' : '添加FAQ'}</h3>
                        <button class="modal-close" onclick="faqManager.closeFAQModal()">×</button>
                    </div>
                    <div class="modal-body">
                        <form id="faqForm">
                            <div class="form-group">
                                <label>问题 *</label>
                                <input type="text" id="faqQuestion" class="form-control" 
                                       value="${isEdit ? this.escapeHtml(faqData.question) : ''}" required>
                            </div>
                            <div class="form-group">
                                <label>答案 *</label>
                                <textarea id="faqAnswer" class="form-control" rows="4" required>${isEdit ? this.escapeHtml(faqData.answer) : ''}</textarea>
                            </div>
                            <div class="form-group">
                                <label>分类</label>
                                <select id="faqCategory" class="form-control">
                                    <option value="常见问题" ${isEdit && faqData.category === '常见问题' ? 'selected' : ''}>常见问题</option>
                                    <option value="注册问题" ${isEdit && faqData.category === '注册问题' ? 'selected' : ''}>注册问题</option>
                                    <option value="支付问题" ${isEdit && faqData.category === '支付问题' ? 'selected' : ''}>支付问题</option>
                                    <option value="账户问题" ${isEdit && faqData.category === '账户问题' ? 'selected' : ''}>账户问题</option>
                                    <option value="技术问题" ${isEdit && faqData.category === '技术问题' ? 'selected' : ''}>技术问题</option>
                                    <option value="其他问题" ${isEdit && faqData.category === '其他问题' ? 'selected' : ''}>其他问题</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="faqStatus" ${isEdit ? (faqData.is_main ? 'checked' : '') : 'checked'}>
                                    启用此FAQ
                                </label>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="faqManager.closeFAQModal()">取消</button>
                        <button class="btn btn-primary" onclick="faqManager.saveFAQ()">${isEdit ? '更新' : '创建'}</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // 添加点击背景关闭模态框的功能
        const modal = document.getElementById('faqModal');
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeFAQModal();
            }
        });

        // 添加ESC键关闭模态框
        const handleEsc = (e) => {
            if (e.key === 'Escape') {
                this.closeFAQModal();
                document.removeEventListener('keydown', handleEsc);
            }
        };
        document.addEventListener('keydown', handleEsc);
    }

    // 关闭FAQ模态框
    closeFAQModal() {
        const modal = document.getElementById('faqModal');
        if (modal) {
            modal.remove();
        }
    }

    // 保存FAQ
    async saveFAQ() {
        const question = document.getElementById('faqQuestion')?.value.trim();
        const answer = document.getElementById('faqAnswer')?.value.trim();
        const category = document.getElementById('faqCategory')?.value;
        const is_main = document.getElementById('faqStatus')?.checked;

        if (!question || !answer) {
            this.showMessage('问题和答案不能为空', 'error');
            return;
        }

        try {
            const url = this.currentFAQId ? 
                `/api/faqs/${this.currentFAQId}/update/` : 
                '/api/faqs/create/';
            
            const method = this.currentFAQId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    question,
                    answer,
                    category,
                    is_main
                })
            });

            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('请先登录');
                }
                if (response.status === 403) {
                    throw new Error('权限不足');
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                this.showMessage(result.message, 'success');
                this.closeFAQModal();
                this.loadFAQs();
            } else {
                this.showMessage(result.error || '操作失败', 'error');
            }
        } catch (error) {
            console.error('保存FAQ失败:', error);
            this.showMessage(error.message || '保存失败，请重试', 'error');
        }
    }

    // 编辑FAQ
    async editFAQ(id) {
        try {
            const response = await fetch(`/api/faqs/${id}/`, {
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('请先登录');
                }
                if (response.status === 403) {
                    throw new Error('权限不足');
                }
                throw new Error('获取FAQ详情失败');
            }

            const faqData = await response.json();
            this.showFAQModal(faqData);
        } catch (error) {
            console.error('获取FAQ详情失败:', error);
            this.showMessage(error.message || '获取FAQ详情失败，请重试', 'error');
        }
    }

    // 切换FAQ状态
    async toggleFAQStatus(id) {
        try {
            const response = await fetch(`/api/faqs/${id}/toggle-status/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('请先登录');
                }
                if (response.status === 403) {
                    throw new Error('权限不足');
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                this.showMessage(result.message, 'success');
                this.loadFAQs();
            } else {
                this.showMessage(result.error || '操作失败', 'error');
            }
        } catch (error) {
            console.error('切换状态失败:', error);
            this.showMessage(error.message || '操作失败，请重试', 'error');
        }
    }

    // 删除FAQ
    async deleteFAQ(id) {
        if (!confirm('确定要删除这个FAQ吗？删除后无法恢复！')) return;

        try {
            const response = await fetch(`/api/faqs/${id}/delete/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('请先登录');
                }
                if (response.status === 403) {
                    throw new Error('权限不足');
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                this.showMessage(result.message, 'success');
                this.loadFAQs();
            } else {
                this.showMessage(result.error || '删除失败', 'error');
            }
        } catch (error) {
            console.error('删除FAQ失败:', error);
            this.showMessage(error.message || '删除失败，请重试', 'error');
        }
    }

    // 导出FAQ
    async exportFAQs() {
        try {
            this.showMessage('正在导出数据...', 'info');
            
            const response = await fetch('/api/faqs/export/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('请先登录');
                }
                if (response.status === 403) {
                    throw new Error('权限不足');
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success && result.data && result.data.length > 0) {
                this.downloadCSV(result.data, 'faq_export.csv');
                this.showMessage('导出成功', 'success');
            } else {
                this.showMessage('没有数据可导出', 'warning');
            }
        } catch (error) {
            console.error('导出FAQ失败:', error);
            this.showMessage(error.message || '导出失败，请重试', 'error');
        }
    }

    // 下载CSV文件
    downloadCSV(data, filename) {
        if (!data || !data.length) {
            this.showMessage('没有数据可导出', 'error');
            return;
        }

        try {
            const headers = Object.keys(data[0]);
            const csvContent = [
                headers.join(','),
                ...data.map(row => headers.map(header => {
                    const value = (row[header] || '').toString().replace(/"/g, '""');
                    return `"${value}"`;
                }).join(','))
            ].join('\n');

            const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            
            if (link.download !== undefined) {
                const url = URL.createObjectURL(blob);
                link.setAttribute('href', url);
                link.setAttribute('download', filename);
                link.style.visibility = 'hidden';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
            }
        } catch (error) {
            console.error('下载文件失败:', error);
            this.showMessage('下载文件失败', 'error');
        }
    }

    // 加载分类列表
    async loadCategories() {
        try {
            const response = await fetch('/api/faqs/categories/', {
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                },
                credentials: 'same-origin'
            });

            if (response.ok) {
                const result = await response.json();
                if (result.categories) {
                    this.updateCategorySelect(result.categories);
                }
            }
        } catch (error) {
            console.error('加载分类失败:', error);
        }
    }

    // 更新分类选择框
    updateCategorySelect(categories) {
        const select = document.getElementById('categoryFilter');
        if (!select) return;
        
        const currentValue = select.value;
        
        // 保留第一个选项"全部分类"
        const firstOption = select.querySelector('option[value=""]');
        select.innerHTML = '';
        if (firstOption) {
            select.appendChild(firstOption);
        } else {
            const allOption = document.createElement('option');
            allOption.value = '';
            allOption.textContent = '全部分类';
            select.appendChild(allOption);
        }
        
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            if (category === currentValue) option.selected = true;
            select.appendChild(option);
        });
    }

    // 显示消息提示
    showMessage(message, type = 'info') {
        // 移除已存在的消息
        const existingMessage = document.querySelector('.message-toast');
        if (existingMessage) {
            existingMessage.remove();
        }

        // 创建消息元素
        const messageDiv = document.createElement('div');
        messageDiv.className = `message-toast message-${type}`;
        messageDiv.textContent = message;

        // 添加到页面
        document.body.appendChild(messageDiv);

        // 3秒后自动移除
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 3000);
    }

    // HTML转义
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 在页面加载完成后初始化FAQ管理器
document.addEventListener('DOMContentLoaded', function() {
    // 创建全局FAQ管理器实例
    window.faqManager = new FAQManager();
});

// 如果页面已经加载完成（例如异步加载脚本的情况）
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        if (!window.faqManager) {
            window.faqManager = new FAQManager();
        }
    });
} else {
    // 页面已经加载完成
    if (!window.faqManager) {
        window.faqManager = new FAQManager();
    }
}