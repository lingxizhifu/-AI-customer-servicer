// sidebar.js
// 侧边栏滑动隐藏/呼出+收缩功能

document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebarToggle');
    const toggleBtnCollapsed = document.getElementById('sidebarToggleCollapsed');
    const container = document.querySelector('.container');

    if (sidebar && toggleBtn && toggleBtnCollapsed && container) {
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.add('sidebar-collapsed');
            toggleBtn.style.display = 'none';
            toggleBtnCollapsed.style.display = 'flex';
        });
        toggleBtnCollapsed.addEventListener('click', function() {
            sidebar.classList.remove('sidebar-collapsed');
            toggleBtn.style.display = 'flex';
            toggleBtnCollapsed.style.display = 'none';
        });
    }

    // 只有 mainContent 和 sidebar 都存在时才绑定事件，防止报错
    const mainContent = document.querySelector('.main-content');
    if (mainContent && sidebar) {
        if (window.innerWidth < 900) {
            mainContent.addEventListener('click', function() {
                if (sidebar && !sidebar.classList.contains('sidebar-hidden')) {
                    sidebar.classList.add('sidebar-hidden');
                }
            });
        }
    }
}); 