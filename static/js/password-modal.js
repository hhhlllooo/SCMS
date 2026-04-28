var PasswordModal = (function() {
    var overlay = null;
    var resolveCallback = null;
    var rejectCallback = null;

    function init() {
        if (overlay) return;
        
        overlay = document.createElement('div');
        overlay.className = 'confirm-overlay';
        overlay.id = 'passwordModalOverlay';
        
        overlay.innerHTML = 
            '<div class="confirm-dialog" style="max-width: 420px;">' +
                '<div class="confirm-header">' +
                    '<div class="confirm-icon confirm-icon-warning">' +
                        '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>' +
                    '</div>' +
                    '<h5 class="confirm-title">安全验证</h5>' +
                '</div>' +
                '<div class="confirm-body">' +
                    '<p class="confirm-message" style="margin-bottom: 1rem;">此操作需要验证身份，请输入管理密码：</p>' +
                    '<div class="password-input-group">' +
                        '<div class="password-input-wrapper">' +
                            '<span class="password-input-icon">' +
                                '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"></path></svg>' +
                            '</span>' +
                            '<input type="password" class="password-input" id="passwordInput" placeholder="请输入密码" autocomplete="off">' +
                            '<button type="button" class="password-toggle-btn" id="togglePasswordBtn" title="显示/隐藏密码">' +
                                '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="eye-icon"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>' +
                                '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="eye-off-icon" style="display:none;"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>' +
                            '</button>' +
                        '</div>' +
                        '<div class="password-error" id="passwordError"></div>' +
                    '</div>' +
                    '<div class="password-security-hint">' +
                        '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>' +
                        '<span>密码验证有效期为10分钟，超时需重新验证</span>' +
                    '</div>' +
                '</div>' +
                '<div class="confirm-footer">' +
                    '<button class="confirm-btn confirm-btn-cancel" id="passwordCancelBtn">' +
                        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>' +
                        '取消' +
                    '</button>' +
                    '<button class="confirm-btn confirm-btn-confirm btn-warning" id="confirmPasswordBtn">' +
                        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>' +
                        '确认验证' +
                    '</button>' +
                '</div>' +
            '</div>';
        
        document.body.appendChild(overlay);
        
        var passwordInput = document.getElementById('passwordInput');
        var confirmPasswordBtn = document.getElementById('confirmPasswordBtn');
        var togglePasswordBtn = document.getElementById('togglePasswordBtn');
        var passwordError = document.getElementById('passwordError');
        var cancelBtn = document.getElementById('passwordCancelBtn');
        
        confirmPasswordBtn.addEventListener('click', verifyPassword);
        cancelBtn.addEventListener('click', function() {
            hide(false);
        });
        
        passwordInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                verifyPassword();
            }
        });
        
        passwordInput.addEventListener('input', function() {
            this.classList.remove('is-invalid');
            passwordError.textContent = '';
            passwordError.style.display = 'none';
        });
        
        togglePasswordBtn.addEventListener('click', function() {
            var type = passwordInput.type === 'password' ? 'text' : 'password';
            passwordInput.type = type;
            var eyeIcon = this.querySelector('.eye-icon');
            var eyeOffIcon = this.querySelector('.eye-off-icon');
            if (type === 'password') {
                eyeIcon.style.display = 'block';
                eyeOffIcon.style.display = 'none';
            } else {
                eyeIcon.style.display = 'none';
                eyeOffIcon.style.display = 'block';
            }
        });
        
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) {
                hide(false);
            }
        });
    }

    function verifyPassword() {
        var passwordInput = document.getElementById('passwordInput');
        var passwordError = document.getElementById('passwordError');
        var confirmPasswordBtn = document.getElementById('confirmPasswordBtn');
        var password = passwordInput.value.trim();
        
        if (!password) {
            passwordInput.classList.add('is-invalid');
            passwordError.textContent = '请输入密码';
            passwordError.style.display = 'block';
            return;
        }
        
        confirmPasswordBtn.disabled = true;
        confirmPasswordBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>验证中...';
        
        fetch('/api/verify-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ password: password })
        })
        .then(response => response.json())
        .then(data => {
            confirmPasswordBtn.disabled = false;
            confirmPasswordBtn.innerHTML = 
                '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>' +
                '确认验证';
            
            if (data.success) {
                hide(true);
            } else {
                passwordInput.classList.add('is-invalid');
                passwordError.textContent = data.error || '密码错误';
                passwordError.style.display = 'block';
                passwordInput.value = '';
                passwordInput.focus();
            }
        })
        .catch(function(error) {
            confirmPasswordBtn.disabled = false;
            confirmPasswordBtn.innerHTML = 
                '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>' +
                '确认验证';
            passwordInput.classList.add('is-invalid');
            passwordError.textContent = '验证失败，请重试';
            passwordError.style.display = 'block';
        });
    }

    function hide(result) {
        if (!overlay) return;
        
        overlay.classList.remove('show');
        
        var passwordInput = document.getElementById('passwordInput');
        var passwordError = document.getElementById('passwordError');
        
        if (passwordInput) {
            passwordInput.value = '';
            passwordInput.classList.remove('is-invalid');
        }
        if (passwordError) {
            passwordError.textContent = '';
            passwordError.style.display = 'none';
        }
        
        setTimeout(function() {
            if (result) {
                if (resolveCallback) {
                    resolveCallback(true);
                    resolveCallback = null;
                }
            } else {
                if (rejectCallback) {
                    rejectCallback(new Error('Modal closed'));
                    rejectCallback = null;
                }
            }
        }, 250);
    }

    function show() {
        init();
        return new Promise(function(resolve, reject) {
            resolveCallback = resolve;
            rejectCallback = reject;
            overlay.classList.add('show');
            setTimeout(function() {
                var passwordInput = document.getElementById('passwordInput');
                if (passwordInput) passwordInput.focus();
            }, 100);
        });
    }

    function checkAuth() {
        return fetch('/api/check-sensitive-auth')
            .then(response => response.json())
            .then(data => data.verified);
    }

    function requireAuth() {
        return checkAuth().then(function(verified) {
            if (verified) {
                return true;
            }
            return show();
        });
    }

    return {
        show: show,
        checkAuth: checkAuth,
        requireAuth: requireAuth
    };
})();
