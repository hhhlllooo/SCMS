var ProjectModal = (function() {
    var modal = null;
    var modalContent = null;
    var currentMode = null;
    var currentProjectId = null;
    var isLoading = false;

    function createModal() {
        if (modal) return;

        modal = document.createElement('div');
        modal.className = 'project-modal-overlay';
        modal.id = 'projectModal';
        modal.innerHTML = `
            <div class="project-modal-container">
                <div class="project-modal-header">
                    <h5 class="project-modal-title" id="projectModalTitle">项目详情</h5>
                    <div class="project-modal-actions" id="projectModalActions"></div>
                    <button type="button" class="project-modal-close" id="projectModalClose" aria-label="关闭">
                        <i data-feather="x"></i>
                    </button>
                </div>
                <div class="project-modal-body" id="projectModalBody">
                    <div class="project-modal-loading">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">加载中...</span>
                        </div>
                        <span class="ms-2">加载中...</span>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        modalContent = document.getElementById('projectModalBody');

        document.getElementById('projectModalClose').addEventListener('click', close);

        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                close();
            }
        });

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && modal.classList.contains('show')) {
                close();
            }
        });
    }

    function open(mode, projectId) {
        createModal();
        currentMode = mode;
        currentProjectId = projectId;

        var title = '';
        var url = '';

        switch(mode) {
            case 'add':
                title = '添加项目';
                url = '/projects/add?modal=1';
                break;
            case 'edit':
                title = '编辑项目';
                url = '/projects/edit/' + projectId + '?modal=1';
                break;
            case 'view':
                title = '查看项目';
                url = '/projects/view/' + projectId + '?modal=1';
                break;
        }

        document.getElementById('projectModalTitle').textContent = title;

        modal.classList.add('show');
        document.body.style.overflow = 'hidden';

        loadContent(url);
    }

    function loadContent(url) {
        isLoading = true;
        modalContent.innerHTML = `
            <div class="project-modal-loading">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <span class="ms-2">加载中...</span>
            </div>
        `;

        fetch(url)
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('加载失败');
                }
                return response.text();
            })
            .then(function(html) {
                modalContent.innerHTML = html;
                if (window.feather) {
                    feather.replace();
                }
                initializeFormHandlers();
            })
            .catch(function(error) {
                modalContent.innerHTML = `
                    <div class="alert alert-danger">
                        <i data-feather="alert-circle"></i>
                        加载失败：${error.message}
                    </div>
                `;
                if (window.feather) {
                    feather.replace();
                }
            })
            .finally(function() {
                isLoading = false;
            });
    }

    function moveButtonsToHeader() {
        var actionsContainer = document.getElementById('projectModalActions');
        if (!actionsContainer) return;

        actionsContainer.innerHTML = '';

        var buttonRow = modalContent.querySelector('.row.mt-3 .col-12 .d-flex.justify-content-end');
        if (!buttonRow) {
            buttonRow = modalContent.querySelector('.d-flex.justify-content-end.gap-2');
        }

        if (buttonRow) {
            var buttons = buttonRow.querySelectorAll('button');
            buttons.forEach(function(btn) {
                var clone = btn.cloneNode(true);
                clone.classList.add('project-modal-header-btn');
                actionsContainer.appendChild(clone);

                btn.addEventListener('click', function(e) {
                    if (clone.click) {
                        clone.click();
                    }
                });
            });

            var rowContainer = buttonRow.closest('.row.mt-3');
            if (rowContainer) {
                rowContainer.style.display = 'none';
            } else {
                buttonRow.style.display = 'none';
            }
        }

        if (window.feather) {
            feather.replace();
        }

        rebindHeaderButtons();
    }

    function rebindHeaderButtons() {
        var actionsContainer = document.getElementById('projectModalActions');
        if (!actionsContainer) return;

        var form = modalContent.querySelector('#projectForm');
        var submitBtns = actionsContainer.querySelectorAll('button[type="submit"]');
        submitBtns.forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                if (form) {
                    form.dispatchEvent(new Event('submit', { cancelable: true }));
                }
            });
        });

        var closeBtns = actionsContainer.querySelectorAll('button[onclick*="ProjectModal.close"]');
        closeBtns.forEach(function(btn) {
            btn.removeAttribute('onclick');
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                close();
            });
        });

        var viewBtns = actionsContainer.querySelectorAll('button[onclick*="ProjectModal.view"]');
        viewBtns.forEach(function(btn) {
            var onclickAttr = btn.getAttribute('onclick');
            var match = onclickAttr && onclickAttr.match(/ProjectModal\.view\((\d+)\)/);
            if (match) {
                var projectId = match[1];
                btn.removeAttribute('onclick');
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    open('view', projectId);
                });
            }
        });

        var editBtns = actionsContainer.querySelectorAll('button[onclick*="ProjectModal.edit"]');
        editBtns.forEach(function(btn) {
            var onclickAttr = btn.getAttribute('onclick');
            var match = onclickAttr && onclickAttr.match(/ProjectModal\.edit\((\d+)\)/);
            if (match) {
                var projectId = match[1];
                btn.removeAttribute('onclick');
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    open('edit', projectId);
                });
            }
        });

        var deleteBtn = actionsContainer.querySelector('#deleteBtn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', function(e) {
                e.preventDefault();
                handleDelete();
            });
        }
    }

    function initializeFormHandlers() {
        var form = modalContent.querySelector('#projectForm');
        if (!form) return;

        moveButtonsToHeader();

        var action = form.getAttribute('action');

        form.addEventListener('submit', function(e) {
            e.preventDefault();

            var certificateInputHidden = document.getElementById('certificate_number');
            var certificateInputDisplay = document.getElementById('certificate_number_input');

            if (certificateInputHidden && certificateInputDisplay) {
                var value = certificateInputHidden.value.trim();
                if (!value || !/^市政\d{4}$/.test(value)) {
                    certificateInputDisplay.classList.add('is-invalid');
                    var errorDiv = document.getElementById('certificate_error');
                    if (errorDiv) {
                        errorDiv.textContent = '请输入四位有效数字';
                        errorDiv.style.display = 'block';
                    }
                    certificateInputDisplay.focus();
                    Toast.error('请正确填写参选证号码（四位数字）');
                    return;
                }
            }

            var formData = new FormData(form);

            fetch(action, {
                method: 'POST',
                body: formData
            })
            .then(function(response) {
                return response.text().then(function(html) {
                    return { html: html, redirected: response.redirected, url: response.url };
                });
            })
            .then(function(result) {
                if (result.redirected) {
                    close();
                    Toast.success(currentMode === 'add' ? '项目添加成功！' : '项目更新成功！');
                    setTimeout(function() {
                        window.location.reload();
                    }, 500);
                } else {
                    modalContent.innerHTML = result.html;
                    if (window.feather) {
                        feather.replace();
                    }
                    initializeFormHandlers();
                }
            })
            .catch(function(error) {
                Toast.error('保存失败：' + error.message);
            });
        });

        var backBtn = modalContent.querySelector('#backToListBtn');
        if (backBtn) {
            backBtn.addEventListener('click', function(e) {
                e.preventDefault();
                close();
            });
        }

        var cancelBtn = modalContent.querySelector('a[href*="/projects/view/"]');
        if (cancelBtn && currentMode === 'edit') {
            cancelBtn.addEventListener('click', function(e) {
                e.preventDefault();
                open('view', currentProjectId);
            });
        }

        var editBtn = modalContent.querySelector('a[href*="/projects/edit/"]');
        if (editBtn && currentMode === 'view') {
            editBtn.addEventListener('click', function(e) {
                e.preventDefault();
                open('edit', currentProjectId);
            });
        }

        var deleteBtn = modalContent.querySelector('#deleteBtn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', function(e) {
                e.preventDefault();
                handleDelete();
            });
        }

        initializeCertificateHandlers();
        initializeOcrHandlers();
    }

    function initializeCertificateHandlers() {
        var certificateInputDisplay = document.getElementById('certificate_number_input');
        var certificateInputHidden = document.getElementById('certificate_number');

        if (!certificateInputDisplay || !certificateInputHidden) return;

        function updateCertificateValue() {
            var digits = certificateInputDisplay.value.replace(/\D/g, '');
            certificateInputDisplay.value = digits;
            if (digits.length === 4) {
                certificateInputHidden.value = '市政' + digits;
            } else {
                certificateInputHidden.value = '';
            }
        }

        certificateInputDisplay.addEventListener('input', function(e) {
            var originalValue = this.value;
            var digits = originalValue.replace(/\D/g, '');

            if (digits !== originalValue) {
                this.value = digits;
            }

            updateCertificateValue();

            certificateInputDisplay.classList.remove('is-invalid');
            var errorDiv = document.getElementById('certificate_error');
            var serverErrorDiv = document.getElementById('certificate_server_error');
            if (errorDiv) {
                errorDiv.style.display = 'none';
            }
            if (serverErrorDiv) {
                serverErrorDiv.style.display = 'none';
            }
        });

        certificateInputDisplay.addEventListener('keypress', function(e) {
            var charCode = (e.which) ? e.which : e.keyCode;
            if (charCode > 31 && (charCode < 48 || charCode > 57)) {
                e.preventDefault();
                return false;
            }
        });

        certificateInputDisplay.addEventListener('paste', function(e) {
            e.preventDefault();
            var pastedText = (e.clipboardData || window.clipboardData).getData('text');
            var digits = pastedText.replace(/\D/g, '').substring(0, 4);
            this.value = digits;
            updateCertificateValue();
        });

        function checkCertificate() {
            var value = certificateInputHidden.value.trim();
            var errorDiv = document.getElementById('certificate_error');
            var serverErrorDiv = document.getElementById('certificate_server_error');

            if (serverErrorDiv) {
                serverErrorDiv.style.display = 'none';
            }

            if (!value) {
                certificateInputDisplay.classList.add('is-invalid');
                if (errorDiv) {
                    errorDiv.textContent = '请输入四位数字';
                    errorDiv.style.display = 'block';
                }
                return;
            }

            var pattern = /^市政\d{4}$/;

            if (!pattern.test(value)) {
                certificateInputDisplay.classList.add('is-invalid');
                if (errorDiv) {
                    errorDiv.textContent = '请输入四位有效数字';
                    errorDiv.style.display = 'block';
                }
                return;
            }

            var projectId = currentProjectId || 0;

            fetch('/api/certificate/check?certificate=' + encodeURIComponent(value) + '&project_id=' + projectId)
                .then(response => response.json())
                .then(data => {
                    if (data.exists) {
                        certificateInputDisplay.classList.add('is-invalid');
                        if (errorDiv) {
                            errorDiv.innerHTML = '<i class="align-middle me-1" data-feather="alert-triangle" style="width:14px;height:14px;"></i>该参选证号码已存在，请使用其他号码';
                            errorDiv.style.display = 'block';
                            if (window.feather) {
                                feather.replace();
                            }
                        }
                    } else {
                        certificateInputDisplay.classList.remove('is-invalid');
                        if (errorDiv) {
                            errorDiv.style.display = 'none';
                        }
                    }
                })
                .catch(function() {
                });
        }

        certificateInputDisplay.addEventListener('blur', checkCertificate);

        if (currentMode === 'add' && !certificateInputDisplay.value) {
            fetch('/api/certificate/next')
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.display_number) {
                        certificateInputDisplay.value = data.display_number;
                        certificateInputHidden.value = data.certificate_number;
                        certificateInputDisplay.classList.remove('is-invalid');
                        var errorDiv = document.getElementById('certificate_error');
                        var serverErrorDiv = document.getElementById('certificate_server_error');
                        if (errorDiv) {
                            errorDiv.style.display = 'none';
                        }
                        if (serverErrorDiv) {
                            serverErrorDiv.style.display = 'none';
                        }
                    }
                })
                .catch(function(error) {
                    console.error('Error fetching next certificate number:', error);
                });
        }
    }

    function initializeOcrHandlers() {
        var ocrImageInput = document.getElementById('ocrImageInput');
        var ocrUploadArea = document.getElementById('ocrUploadArea');

        if (!ocrImageInput || !ocrUploadArea) return;

        var ocrUploadPrompt = document.getElementById('ocrUploadPrompt');
        var ocrFilePreview = document.getElementById('ocrFilePreview');
        var ocrImageLink = document.getElementById('ocrImageLink');
        var ocrFileName = document.getElementById('ocrFileName');
        var ocrRemoveBtn = document.getElementById('ocrRemoveBtn');
        var ocrStatus = document.getElementById('ocrStatus');
        var ocrResult = document.getElementById('ocrResult');
        var ocrError = document.getElementById('ocrError');
        var ocrErrorMsg = document.getElementById('ocrErrorMsg');
        var ocrFilledCount = document.getElementById('ocrFilledCount');
        var ocrCurrentFile = null;
        var ocrCurrentDataUrl = null;

        ocrUploadArea.addEventListener('click', function(e) {
            if (e.target.closest('#ocrRemoveBtn') || e.target.closest('#ocrImageLink')) return;
            ocrImageInput.click();
        });

        ocrUploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.stopPropagation();
            ocrUploadArea.classList.add('border-primary', 'bg-light');
        });

        ocrUploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            e.stopPropagation();
            ocrUploadArea.classList.remove('border-primary', 'bg-light');
        });

        ocrUploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            ocrUploadArea.classList.remove('border-primary', 'bg-light');

            var files = e.dataTransfer.files;
            if (files.length > 0) {
                handleOcrFileSelect(files[0]);
            }
        });

        ocrImageInput.addEventListener('change', function(e) {
            if (this.files.length > 0) {
                handleOcrFileSelect(this.files[0]);
            }
        });

        function handleOcrFileSelect(file) {
            if (!file.type.startsWith('image/')) {
                Toast.error('请选择图片文件');
                return;
            }

            if (file.size > 16 * 1024 * 1024) {
                Toast.error('图片大小不能超过16MB');
                return;
            }

            ocrCurrentFile = file;

            var reader = new FileReader();
            reader.onload = function(e) {
                ocrCurrentDataUrl = e.target.result;
            };
            reader.readAsDataURL(file);

            ocrUploadPrompt.classList.add('d-none');
            ocrFilePreview.classList.remove('d-none');
            ocrFileName.textContent = file.name;
            ocrResult.classList.add('d-none');
            ocrError.classList.add('d-none');

            performOcr(file);
        }

        function performOcr(file) {
            ocrStatus.classList.remove('d-none');
            ocrError.classList.add('d-none');
            ocrResult.classList.add('d-none');

            var formData = new FormData();
            formData.append('image', file);

            fetch('/api/ocr', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                ocrStatus.classList.add('d-none');

                if (data.success && data.extracted) {
                    fillFormWithOcrData(data.extracted);
                    var filledCount = countFilledFields(data.extracted);
                    ocrFilledCount.textContent = filledCount;
                    ocrResult.classList.remove('d-none');
                    Toast.success('OCR识别完成，已填充 ' + filledCount + ' 个字段');
                } else {
                    ocrErrorMsg.textContent = data.error || '识别失败，请重试';
                    ocrError.classList.remove('d-none');
                    Toast.error('OCR识别失败');
                }
            })
            .catch(error => {
                ocrStatus.classList.add('d-none');
                ocrErrorMsg.textContent = '识别出错：' + error.message;
                ocrError.classList.remove('d-none');
                Toast.error('OCR识别出错');
            });
        }

        function fillFormWithOcrData(data) {
            var fieldMapping = {
                'project_name': 'project_name',
                'project_cost': 'project_cost',
                'declaring_company': 'declaring_company',
                'project_manager': 'project_manager',
                'contact_phone': 'contact_phone',
                'supervision_company': 'supervision_company',
                'project_director': 'project_director',
                'construction_unit': 'construction_unit',
                'start_date': 'start_date',
                'end_date': 'end_date'
            };

            for (var key in data) {
                if (data.hasOwnProperty(key) && fieldMapping[key]) {
                    var field = document.querySelector('[name="' + fieldMapping[key] + '"]');
                    if (field && data[key]) {
                        field.value = data[key];
                    }
                }
            }
        }

        function countFilledFields(data) {
            var count = 0;
            for (var key in data) {
                if (data.hasOwnProperty(key) && data[key]) {
                    count++;
                }
            }
            return count;
        }

        if (ocrRemoveBtn) {
            ocrRemoveBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                ocrCurrentFile = null;
                ocrCurrentDataUrl = null;
                ocrImageInput.value = '';
                ocrUploadPrompt.classList.remove('d-none');
                ocrFilePreview.classList.add('d-none');
                ocrResult.classList.add('d-none');
                ocrError.classList.add('d-none');
            });
        }

        if (ocrImageLink) {
            ocrImageLink.addEventListener('click', function(e) {
                e.stopPropagation();
                if (ocrCurrentDataUrl) {
                    var win = window.open();
                    win.document.write('<img src="' + ocrCurrentDataUrl + '" style="max-width:100%;">');
                }
            });
        }
    }

    function handleDelete() {
        if (typeof PasswordModal === 'undefined') {
            Toast.error('密码验证组件未加载');
            return;
        }

        var projectName = '';
        var nameField = modalContent.querySelector('[name="project_name"]');
        if (nameField) {
            projectName = nameField.value;
        }

        PasswordModal.requireAuth().then(function(authenticated) {
            if (authenticated) {
                if (typeof Confirm === 'undefined') {
                    if (confirm('确定要删除项目"' + projectName + '"吗？此操作不可恢复！')) {
                        performDelete();
                    }
                } else {
                    Confirm.delete('确定要删除项目"' + projectName + '"吗？此操作不可恢复！', '删除确认').then(function(result) {
                        if (result) {
                            performDelete();
                        }
                    });
                }
            }
        }).catch(function() {});
    }

    function performDelete() {
        var form = document.createElement('form');
        form.method = 'POST';
        form.action = '/projects/delete/' + currentProjectId;
        document.body.appendChild(form);
        form.submit();
    }

    function close() {
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }

    return {
        open: open,
        close: close,
        add: function() { open('add'); },
        edit: function(id) { open('edit', id); },
        view: function(id) { open('view', id); }
    };
})();
