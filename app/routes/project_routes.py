# Project CRUD routes blueprint

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models import db, Project
from app.services import ProjectService
from app.utils import REGION_CHOICES, STATUS_CHOICES, TARGET_CHOICES, validate_certificate_number, normalize_certificate_number

projects = Blueprint('projects', __name__, url_prefix='/projects')


@projects.route('/add', methods=['GET', 'POST'])
def project_add():
    """Add a new project"""
    form_data = None
    form_errors = {}
    is_modal = request.args.get('modal') == '1'
    template_name = 'project_form_modal.html' if is_modal else 'project_form.html'

    if request.method == 'POST':
        # Extract form data
        form_data = {key: value for key, value in request.form.items()}
        
        # Validate
        if not form_data.get('project_name'):
            form_errors['project_name'] = '申报工程名称不能为空'

        cert_validation = validate_certificate_number(form_data.get('certificate_number', ''))
        if not cert_validation['valid']:
            form_errors['certificate_number'] = cert_validation['error']

        if not form_data.get('status'):
            form_errors['status'] = '状态不能为空'

        if form_errors:
            return render_template(template_name,
                                 project=form_data,
                                 mode='add',
                                 region_choices=REGION_CHOICES,
                                 status_choices=STATUS_CHOICES,
                                 target_choices=TARGET_CHOICES,
                                 form_errors=form_errors)

        try:
            # Create project using service
            project = ProjectService.create_project(form_data)
            db.session.add(project)
            db.session.commit()
            
            flash('项目添加成功！', 'success')
            return redirect(url_for('projects.project_list'))
        except Exception as e:
            db.session.rollback()
            form_errors['general'] = f'添加失败：{str(e)}'
            return render_template(template_name,
                                 project=form_data,
                                 mode='add',
                                 region_choices=REGION_CHOICES,
                                 status_choices=STATUS_CHOICES,
                                 target_choices=TARGET_CHOICES,
                                 form_errors=form_errors)

    return render_template(template_name,
                         project=None,
                         mode='add',
                         region_choices=REGION_CHOICES,
                         status_choices=STATUS_CHOICES,
                         target_choices=TARGET_CHOICES,
                         form_errors=form_errors)


@projects.route('/view/<int:id>')
def project_view(id):
    """View project details"""
    project = Project.query.get_or_404(id)
    is_modal = request.args.get('modal') == '1'
    template_name = 'project_form_modal.html' if is_modal else 'project_form.html'
    
    return render_template(template_name,
                         project=project,
                         mode='view',
                         region_choices=REGION_CHOICES,
                         status_choices=STATUS_CHOICES,
                         target_choices=TARGET_CHOICES,
                         project_id=id)


@projects.route('/edit/<int:id>', methods=['GET', 'POST'])
def project_edit(id):
    """Edit an existing project"""
    project = Project.query.get_or_404(id)
    form_errors = {}
    is_modal = request.args.get('modal') == '1'
    template_name = 'project_form_modal.html' if is_modal else 'project_form.html'

    if request.method == 'POST':
        form_data = {key: value for key, value in request.form.items()}

        # Validate
        if not form_data.get('project_name'):
            form_errors['project_name'] = '申报工程名称不能为空'

        cert_validation = validate_certificate_number(form_data.get('certificate_number', ''), exclude_id=id)
        if not cert_validation['valid']:
            form_errors['certificate_number'] = cert_validation['error']

        if not form_data.get('status'):
            form_errors['status'] = '状态不能为空'

        if form_errors:
            return render_template(template_name,
                                 project=form_data,
                                 mode='edit',
                                 region_choices=REGION_CHOICES,
                                 status_choices=STATUS_CHOICES,
                                 target_choices=TARGET_CHOICES,
                                 form_errors=form_errors,
                                 project_id=id)

        try:
            # Update project using service
            ProjectService.update_project(project, form_data)
            db.session.commit()
            
            flash('项目更新成功！', 'success')
            if is_modal:
                return redirect(url_for('projects.project_list'))
            return redirect(url_for('projects.project_view', id=id))
        except Exception as e:
            db.session.rollback()
            form_errors['general'] = f'更新失败：{str(e)}'
            return render_template(template_name,
                                 project=form_data,
                                 mode='edit',
                                 region_choices=REGION_CHOICES,
                                 status_choices=STATUS_CHOICES,
                                 target_choices=TARGET_CHOICES,
                                 form_errors=form_errors,
                                 project_id=id)

    return render_template(template_name,
                         project=project,
                         mode='edit',
                         region_choices=REGION_CHOICES,
                         status_choices=STATUS_CHOICES,
                         target_choices=TARGET_CHOICES,
                         form_errors=form_errors,
                         project_id=id)


@projects.route('/delete/<int:id>', methods=['POST'])
def project_delete(id):
    """Delete a project"""
    project = Project.query.get_or_404(id)
    try:
        db.session.delete(project)
        db.session.commit()
        flash('项目删除成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{str(e)}', 'danger')
    
    return redirect(url_for('projects.project_list'))
