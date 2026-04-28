(function() {
    'use strict';

    var Toast = {
        container: null,
        defaultDuration: 3000,

        init: function() {
            if (!this.container) {
                this.container = document.createElement('div');
                this.container.className = 'toast-container';
                document.body.appendChild(this.container);
            }
        },

        create: function(options) {
            this.init();

            var type = options.type || 'info';
            var title = options.title || '';
            var message = options.message || '';
            var duration = options.duration !== undefined ? options.duration : this.defaultDuration;

            var toast = document.createElement('div');
            toast.className = 'toast-item toast-' + type;

            var iconSvg = this.getIcon(type);

            toast.innerHTML = 
                '<div class="toast-icon">' + iconSvg + '</div>' +
                '<div class="toast-content">' +
                    (title ? '<div class="toast-title">' + this.escapeHtml(title) + '</div>' : '') +
                    '<div class="toast-message">' + this.escapeHtml(message) + '</div>' +
                '</div>' +
                '<button class="toast-close" type="button">' +
                    '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>' +
                '</button>';

            if (duration > 0) {
                var progress = document.createElement('div');
                progress.className = 'toast-progress';
                progress.style.animationDuration = duration + 'ms';
                toast.appendChild(progress);
            }

            this.container.appendChild(toast);

            var closeBtn = toast.querySelector('.toast-close');
            var self = this;
            closeBtn.addEventListener('click', function() {
                self.hide(toast);
            });

            setTimeout(function() {
                toast.classList.add('show');
            }, 10);

            if (duration > 0) {
                setTimeout(function() {
                    self.hide(toast);
                }, duration);
            }

            return toast;
        },

        hide: function(toast) {
            toast.classList.remove('show');
            toast.classList.add('hide');
            setTimeout(function() {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 350);
        },

        getIcon: function(type) {
            var icons = {
                success: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
                error: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>',
                warning: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
                info: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'
            };
            return icons[type] || icons.info;
        },

        escapeHtml: function(text) {
            var div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },

        success: function(message, title, duration) {
            return this.create({
                type: 'success',
                title: title || '成功',
                message: message,
                duration: duration
            });
        },

        error: function(message, title, duration) {
            return this.create({
                type: 'error',
                title: title || '错误',
                message: message,
                duration: duration
            });
        },

        warning: function(message, title, duration) {
            return this.create({
                type: 'warning',
                title: title || '警告',
                message: message,
                duration: duration
            });
        },

        info: function(message, title, duration) {
            return this.create({
                type: 'info',
                title: title || '提示',
                message: message,
                duration: duration
            });
        }
    };

    var Confirm = {
        overlay: null,
        currentResolve: null,

        create: function(options) {
            var self = this;

            return new Promise(function(resolve) {
                self.currentResolve = resolve;

                var title = options.title || '确认操作';
                var message = options.message || '确定要执行此操作吗？';
                var type = options.type || 'warning';
                var confirmText = options.confirmText || '确定';
                var cancelText = options.cancelText || '取消';
                var confirmBtnClass = options.confirmBtnClass || '';

                if (!self.overlay) {
                    self.overlay = document.createElement('div');
                    self.overlay.className = 'confirm-overlay';
                    document.body.appendChild(self.overlay);
                }

                var iconClass = 'confirm-icon-' + type;
                var iconSvg = self.getIcon(type);

                self.overlay.innerHTML = 
                    '<div class="confirm-dialog">' +
                        '<div class="confirm-header">' +
                            '<div class="confirm-icon ' + iconClass + '">' + iconSvg + '</div>' +
                            '<h5 class="confirm-title">' + self.escapeHtml(title) + '</h5>' +
                        '</div>' +
                        '<div class="confirm-body">' +
                            '<p class="confirm-message">' + self.escapeHtml(message) + '</p>' +
                        '</div>' +
                        '<div class="confirm-footer">' +
                            '<button class="confirm-btn confirm-btn-cancel" data-action="cancel">' +
                                '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>' +
                                cancelText +
                            '</button>' +
                            '<button class="confirm-btn confirm-btn-confirm ' + confirmBtnClass + '" data-action="confirm">' +
                                '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>' +
                                confirmText +
                            '</button>' +
                        '</div>' +
                    '</div>';

                self.overlay.addEventListener('click', function(e) {
                    var action = e.target.closest('[data-action]');
                    if (action) {
                        var result = action.dataset.action === 'confirm';
                        self.hide(result);
                    }
                });

                setTimeout(function() {
                    self.overlay.classList.add('show');
                }, 10);
            });
        },

        hide: function(result) {
            var self = this;
            this.overlay.classList.remove('show');
            setTimeout(function() {
                if (self.currentResolve) {
                    self.currentResolve(result);
                    self.currentResolve = null;
                }
            }, 250);
        },

        getIcon: function(type) {
            var icons = {
                warning: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
                danger: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>',
                info: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>',
                success: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>'
            };
            return icons[type] || icons.warning;
        },

        escapeHtml: function(text) {
            var div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },

        show: function(message, title, type) {
            return this.create({
                title: title,
                message: message,
                type: type || 'warning'
            });
        },

        delete: function(message, title) {
            return this.create({
                title: title || '删除确认',
                message: message || '确定要删除吗？此操作不可恢复！',
                type: 'danger',
                confirmText: '删除',
                confirmBtnClass: 'btn-danger'
            });
        },

        save: function(message, title) {
            return this.create({
                title: title || '保存确认',
                message: message || '确定要保存吗？',
                type: 'success',
                confirmText: '保存',
                confirmBtnClass: 'btn-success'
            });
        }
    };

    window.Toast = Toast;
    window.Confirm = Confirm;

})();
