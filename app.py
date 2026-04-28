import sys
import io
import json
import logging
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from urllib.parse import quote
import os
import csv
import shutil
import re
import bcrypt
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'project-management-secret-key-2026')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'scms.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PER_PAGE'] = 20
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['BACKUP_FOLDER'] = 'data/backups'

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'
login_manager.session_protection = 'strong'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SENSITIVE_PASSWORD_HASH = os.getenv('SENSITIVE_PASSWORD_HASH')

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == 'admin':
        return User(user_id)
    return None

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

REGION_CHOICES = ['', '市本级', '海曙区', '江北区', '鄞州区', '镇海区', '北仑区', '奉化区', '象山县', '宁海县', '余姚市', '慈溪市', '高新区', '前湾新区', '石化区']
STATUS_CHOICES = ['', '正常', '待考评', '已考评', '许可证']
TARGET_CHOICES = ['', '市标化', '市标化 省标化']


class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(500), nullable=False)
    project_cost = db.Column(db.Numeric(12, 4), default=0)
    declaring_company = db.Column(db.String(500))
    project_manager = db.Column(db.String(100))
    contact_phone = db.Column(db.String(200))
    supervision_company = db.Column(db.String(500))
    project_director = db.Column(db.String(100))
    certificate_number = db.Column(db.String(50), unique=True, nullable=False)
    participating_company = db.Column(db.String(500))
    creation_target = db.Column(db.String(100))
    region = db.Column(db.String(50))
    construction_unit = db.Column(db.String(500))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    standardization_application_date = db.Column(db.Date)
    construction_permit_date = db.Column(db.Date)
    city_standardization_inspection_date = db.Column(db.Date)
    inspectors = db.Column(db.String(200))
    remarks = db.Column(db.Text)
    status = db.Column(db.String(50), nullable=False, default='正常')
    pre_score = db.Column(db.Numeric(5, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Project {self.project_name}>'


def get_pagination_args():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', app.config['PER_PAGE'], type=int)
    if per_page not in [10, 20, 30]:
        per_page = app.config['PER_PAGE']
    return page, per_page


@app.route('/')
def index():
    return redirect(url_for('project_list'))


@app.route('/dashboard')
def dashboard():
    total_projects = Project.query.count()
    status_stats = {}
    for status in STATUS_CHOICES[1:]:
        status_stats[status] = Project.query.filter_by(status=status).count()
    
    focus_statuses = ['正常', '待考评', '许可证']
    focus_total = sum(status_stats.get(s, 0) for s in focus_statuses)
    
    region_stats = {}
    for region in REGION_CHOICES[1:]:
        region_stats[region] = Project.query.filter_by(region=region).count()
    
    region_status_data = {}
    for region in REGION_CHOICES[1:]:
        region_status_data[region] = {}
        for status in focus_statuses:
            count = Project.query.filter_by(region=region, status=status).count()
            region_status_data[region][status] = count
    
    recent_projects = Project.query.order_by(Project.certificate_number.desc()).limit(5).all()
    
    total_cost = db.session.query(db.func.sum(Project.project_cost)).scalar() or 0
    
    selected_year = request.args.get('year', datetime.now().year, type=int)
    if selected_year < 2025:
        selected_year = 2025
    
    available_years = []
    for y in range(2025, datetime.now().year + 2):
        available_years.append(y)
    
    monthly_new_projects = {}
    monthly_inspection_projects = {}
    for month in range(1, 13):
        monthly_new_projects[month] = 0
        monthly_inspection_projects[month] = 0
    
    from sqlalchemy import extract, and_
    
    new_projects = Project.query.filter(
        and_(
            extract('year', Project.standardization_application_date) == selected_year,
            Project.standardization_application_date.isnot(None)
        )
    ).all()
    
    for p in new_projects:
        month = p.standardization_application_date.month
        monthly_new_projects[month] = monthly_new_projects.get(month, 0) + 1
    
    inspection_projects = Project.query.filter(
        and_(
            extract('year', Project.city_standardization_inspection_date) == selected_year,
            Project.city_standardization_inspection_date.isnot(None)
        )
    ).all()
    
    for p in inspection_projects:
        month = p.city_standardization_inspection_date.month
        monthly_inspection_projects[month] = monthly_inspection_projects.get(month, 0) + 1
    
    quarterly_new_projects = {
        'Q1': monthly_new_projects[1] + monthly_new_projects[2] + monthly_new_projects[3],
        'Q2': monthly_new_projects[4] + monthly_new_projects[5] + monthly_new_projects[6],
        'Q3': monthly_new_projects[7] + monthly_new_projects[8] + monthly_new_projects[9],
        'Q4': monthly_new_projects[10] + monthly_new_projects[11] + monthly_new_projects[12]
    }
    
    quarterly_inspection_projects = {
        'Q1': monthly_inspection_projects[1] + monthly_inspection_projects[2] + monthly_inspection_projects[3],
        'Q2': monthly_inspection_projects[4] + monthly_inspection_projects[5] + monthly_inspection_projects[6],
        'Q3': monthly_inspection_projects[7] + monthly_inspection_projects[8] + monthly_inspection_projects[9],
        'Q4': monthly_inspection_projects[10] + monthly_inspection_projects[11] + monthly_inspection_projects[12]
    }
    
    total_new_projects = sum(monthly_new_projects.values())
    total_inspection_projects = sum(monthly_inspection_projects.values())
    
    return render_template('dashboard.html',
                         total_projects=total_projects,
                         status_stats=status_stats,
                         focus_total=focus_total,
                         region_stats=region_stats,
                         region_status_data=region_status_data,
                         region_choices=REGION_CHOICES,
                         recent_projects=recent_projects,
                         total_cost=total_cost,
                         selected_year=selected_year,
                         available_years=available_years,
                         monthly_new_projects=monthly_new_projects,
                         monthly_inspection_projects=monthly_inspection_projects,
                         quarterly_new_projects=quarterly_new_projects,
                         quarterly_inspection_projects=quarterly_inspection_projects,
                         total_new_projects=total_new_projects,
                         total_inspection_projects=total_inspection_projects)


@app.route('/projects')
def project_list():
    page, per_page = get_pagination_args()
    
    search_keyword = request.args.get('search', '').strip()
    filter_region = request.args.get('filter_region', '')
    filter_status = request.args.get('filter_status', '')
    
    query = Project.query
    
    if search_keyword:
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Project.project_name.ilike(f'%{search_keyword}%'),
                Project.declaring_company.ilike(f'%{search_keyword}%'),
                Project.certificate_number.ilike(f'%{search_keyword}%')
            )
        )
    if filter_region:
        query = query.filter_by(region=filter_region)
    if filter_status:
        query = query.filter_by(status=filter_status)
    
    query = query.order_by(Project.certificate_number.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    projects = pagination.items
    
    start_index = (page - 1) * per_page + 1
    
    return render_template('project_list.html',
                         projects=projects,
                         pagination=pagination,
                         start_index=start_index,
                         search=search_keyword,
                         filter_region=filter_region,
                         filter_status=filter_status,
                         per_page=per_page,
                         region_choices=REGION_CHOICES,
                         status_choices=STATUS_CHOICES)


@app.route('/pending')
def pending_list():
    page, per_page = get_pagination_args()
    
    search_keyword = request.args.get('search', '').strip()
    filter_region = request.args.get('filter_region', '')
    
    query = Project.query.filter_by(status='待考评')
    
    if search_keyword:
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Project.project_name.ilike(f'%{search_keyword}%'),
                Project.declaring_company.ilike(f'%{search_keyword}%'),
                Project.certificate_number.ilike(f'%{search_keyword}%')
            )
        )
    if filter_region:
        query = query.filter_by(region=filter_region)
    
    query = query.order_by(Project.certificate_number.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    projects = pagination.items
    
    start_index = (page - 1) * per_page + 1
    
    return render_template('pending_list.html',
                         projects=projects,
                         pagination=pagination,
                         start_index=start_index,
                         search=search_keyword,
                         filter_region=filter_region,
                         per_page=per_page,
                         region_choices=REGION_CHOICES)


@app.route('/evaluation-form/<int:id>')
def evaluation_form(id):
    project = Project.query.get_or_404(id)
    return render_template('evaluation_form.html', project=project)


def validate_certificate_number(certificate_number, exclude_id=None):
    import re
    if not certificate_number:
        return {'valid': False, 'error': '参选证号码不能为空'}
    
    if not re.match(r'^市政\d{4}$', certificate_number):
        return {'valid': False, 'error': '参选证号码格式不正确，应为"市政"加四位数字（如：市政0001）'}
    
    query = Project.query.filter_by(certificate_number=certificate_number)
    if exclude_id:
        query = query.filter(Project.id != exclude_id)
    
    if query.first():
        return {'valid': False, 'error': f'参选证号码"{certificate_number}"已存在，请使用其他号码'}
    
    return {'valid': True, 'error': None}


def normalize_certificate_number(certificate_input):
    import re
    if not certificate_input:
        return ''
    
    certificate_input = certificate_input.strip()
    
    if re.match(r'^市政\d{4}$', certificate_input):
        return certificate_input
    
    digits = re.sub(r'\D', '', certificate_input)
    if len(digits) == 4:
        return '市政' + digits
    
    return certificate_input


def create_project_from_form(form_data):
    certificate_number = form_data.get('certificate_number', '')
    certificate_number = normalize_certificate_number(certificate_number)
    
    return {
        'project_name': form_data.get('project_name', ''),
        'project_cost': form_data.get('project_cost', ''),
        'declaring_company': form_data.get('declaring_company', ''),
        'project_manager': form_data.get('project_manager', ''),
        'contact_phone': form_data.get('contact_phone', ''),
        'supervision_company': form_data.get('supervision_company', ''),
        'project_director': form_data.get('project_director', ''),
        'certificate_number': certificate_number,
        'participating_company': form_data.get('participating_company', ''),
        'creation_target': form_data.get('creation_target', ''),
        'region': form_data.get('region', ''),
        'construction_unit': form_data.get('construction_unit', ''),
        'start_date': form_data.get('start_date', ''),
        'end_date': form_data.get('end_date', ''),
        'standardization_application_date': form_data.get('standardization_application_date', ''),
        'construction_permit_date': form_data.get('construction_permit_date', ''),
        'city_standardization_inspection_date': form_data.get('city_standardization_inspection_date', ''),
        'inspectors': form_data.get('inspectors', ''),
        'remarks': form_data.get('remarks', ''),
        'status': form_data.get('status', '正常'),
        'pre_score': form_data.get('pre_score', '')
    }


@app.route('/projects/add', methods=['GET', 'POST'])
def project_add():
    form_data = None
    form_errors = {}
    is_modal = request.args.get('modal') == '1'
    template_name = 'project_form_modal.html' if is_modal else 'project_form.html'
    
    if request.method == 'POST':
        form_data = create_project_from_form(request.form)
        
        if not form_data['project_name']:
            form_errors['project_name'] = '申报工程名称不能为空'
        
        cert_validation = validate_certificate_number(form_data['certificate_number'])
        if not cert_validation['valid']:
            form_errors['certificate_number'] = cert_validation['error']
        
        if not form_data['status']:
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
            project = Project(
                project_name=form_data['project_name'],
                project_cost=float(form_data['project_cost'] or 0),
                declaring_company=form_data['declaring_company'],
                project_manager=form_data['project_manager'],
                contact_phone=form_data['contact_phone'],
                supervision_company=form_data['supervision_company'],
                project_director=form_data['project_director'],
                certificate_number=form_data['certificate_number'],
                participating_company=form_data['participating_company'],
                creation_target=form_data['creation_target'],
                region=form_data['region'],
                construction_unit=form_data['construction_unit'],
                start_date=datetime.strptime(form_data['start_date'], '%Y-%m-%d').date() if form_data['start_date'] else None,
                end_date=datetime.strptime(form_data['end_date'], '%Y-%m-%d').date() if form_data['end_date'] else None,
                standardization_application_date=datetime.strptime(form_data['standardization_application_date'], '%Y-%m-%d').date() if form_data['standardization_application_date'] else None,
                construction_permit_date=datetime.strptime(form_data['construction_permit_date'], '%Y-%m-%d').date() if form_data['construction_permit_date'] else None,
                city_standardization_inspection_date=datetime.strptime(form_data['city_standardization_inspection_date'], '%Y-%m-%d').date() if form_data['city_standardization_inspection_date'] else None,
                inspectors=form_data['inspectors'],
                remarks=form_data['remarks'],
                status=form_data['status'],
                pre_score=float(form_data['pre_score'] or 0)
            )
            
            db.session.add(project)
            db.session.commit()
            flash('项目添加成功！', 'success')
            if is_modal:
                return redirect(url_for('project_list'))
            return redirect(url_for('project_list'))
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


@app.route('/projects/view/<int:id>')
def project_view(id):
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


@app.route('/projects/edit/<int:id>', methods=['GET', 'POST'])
def project_edit(id):
    project = Project.query.get_or_404(id)
    form_errors = {}
    is_modal = request.args.get('modal') == '1'
    template_name = 'project_form_modal.html' if is_modal else 'project_form.html'
    
    if request.method == 'POST':
        form_data = create_project_from_form(request.form)
        
        if not form_data['project_name']:
            form_errors['project_name'] = '申报工程名称不能为空'
        
        cert_validation = validate_certificate_number(form_data['certificate_number'], exclude_id=id)
        if not cert_validation['valid']:
            form_errors['certificate_number'] = cert_validation['error']
        
        if not form_data['status']:
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
            project.project_name = form_data['project_name']
            project.project_cost = float(form_data['project_cost'] or 0)
            project.declaring_company = form_data['declaring_company']
            project.project_manager = form_data['project_manager']
            project.contact_phone = form_data['contact_phone']
            project.supervision_company = form_data['supervision_company']
            project.project_director = form_data['project_director']
            project.certificate_number = form_data['certificate_number']
            project.participating_company = form_data['participating_company']
            project.creation_target = form_data['creation_target']
            project.region = form_data['region']
            project.construction_unit = form_data['construction_unit']
            project.start_date = datetime.strptime(form_data['start_date'], '%Y-%m-%d').date() if form_data['start_date'] else None
            project.end_date = datetime.strptime(form_data['end_date'], '%Y-%m-%d').date() if form_data['end_date'] else None
            project.standardization_application_date = datetime.strptime(form_data['standardization_application_date'], '%Y-%m-%d').date() if form_data['standardization_application_date'] else None
            project.construction_permit_date = datetime.strptime(form_data['construction_permit_date'], '%Y-%m-%d').date() if form_data['construction_permit_date'] else None
            project.city_standardization_inspection_date = datetime.strptime(form_data['city_standardization_inspection_date'], '%Y-%m-%d').date() if form_data['city_standardization_inspection_date'] else None
            project.inspectors = form_data['inspectors']
            project.remarks = form_data['remarks']
            project.status = form_data['status']
            project.pre_score = float(form_data['pre_score'] or 0)
            
            db.session.commit()
            flash('项目更新成功！', 'success')
            if is_modal:
                return redirect(url_for('project_list'))
            return redirect(url_for('project_view', id=id))
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


@app.route('/projects/delete/<int:id>', methods=['POST'])
def project_delete(id):
    project = Project.query.get_or_404(id)
    try:
        db.session.delete(project)
        db.session.commit()
        flash('项目删除成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{str(e)}', 'danger')
    return redirect(url_for('project_list'))


@app.route('/settings')
def settings():
    import platform
    backup_dir = app.config['BACKUP_FOLDER']
    recent_backups = []
    if os.path.exists(backup_dir):
        backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
        backup_files.sort(reverse=True)
        for f in backup_files[:5]:
            file_path = os.path.join(backup_dir, f)
            file_stat = os.stat(file_path)
            recent_backups.append({
                'name': f,
                'size': round(file_stat.st_size / 1024, 2),
                'date': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
    
    auto_backup_config = load_auto_backup_config()
    
    return render_template('settings.html', 
                         region_choices=REGION_CHOICES, 
                         status_choices=STATUS_CHOICES,
                         recent_backups=recent_backups,
                         auto_backup_config=auto_backup_config,
                         python_version=platform.python_version())


@app.route('/settings/export', methods=['POST'])
def export_csv():
    filter_region = request.form.get('export_region', '')
    filter_status = request.form.get('export_status', '')
    date_from = request.form.get('date_from', '')
    date_to = request.form.get('date_to', '')
    
    query = Project.query
    
    if filter_region:
        query = query.filter_by(region=filter_region)
    if filter_status:
        query = query.filter_by(status=filter_status)
    if date_from:
        query = query.filter(Project.standardization_application_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        query = query.filter(Project.standardization_application_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    
    projects = query.order_by(Project.certificate_number.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = ['申报工程名称', '工程造价(万元)', '申报企业名称', '项目经理姓名', '联系人及电话',
               '监理企业名称', '项目总监姓名', '参选证号码', '参建企业名称', '创建目标',
               '区域', '建设单位', '开工日期', '竣工日期', '标化工地申报时间',
               '施工许可证取得日期', '市标化检查时间', '检查人员', '备注', '状态', '预打分']
    writer.writerow(headers)
    
    for p in projects:
        writer.writerow([
            p.project_name,
            p.project_cost,
            p.declaring_company,
            p.project_manager,
            p.contact_phone,
            p.supervision_company,
            p.project_director,
            p.certificate_number,
            p.participating_company,
            p.creation_target,
            p.region,
            p.construction_unit,
            p.start_date.strftime('%Y-%m-%d') if p.start_date else '',
            p.end_date.strftime('%Y-%m-%d') if p.end_date else '',
            p.standardization_application_date.strftime('%Y-%m-%d') if p.standardization_application_date else '',
            p.construction_permit_date.strftime('%Y-%m-%d') if p.construction_permit_date else '',
            p.city_standardization_inspection_date.strftime('%Y-%m-%d') if p.city_standardization_inspection_date else '',
            p.inspectors,
            p.remarks,
            p.status,
            p.pre_score
        ])
    
    output.seek(0)
    response = make_response(output.getvalue())
    filename = f'projects_export_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv'
    encoded_filename = quote(filename)
    response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"
    response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
    
    return response


@app.route('/settings/import', methods=['POST'])
def import_csv():
    if 'csv_file' not in request.files:
        flash('请选择要导入的CSV文件', 'danger')
        return redirect(url_for('settings'))
    
    file = request.files['csv_file']
    if file.filename == '':
        flash('请选择要导入的CSV文件', 'danger')
        return redirect(url_for('settings'))
    
    if not file.filename.endswith('.csv'):
        flash('请选择CSV格式的文件', 'danger')
        return redirect(url_for('settings'))
    
    def parse_date(date_str):
        if not date_str or not str(date_str).strip():
            return None
        date_str = str(date_str).strip()
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return None
    
    def parse_cost(cost_str):
        if not cost_str or not str(cost_str).strip():
            return 0
        cost_str = re.sub(r'[^\d.]', '', str(cost_str).strip())
        try:
            return float(cost_str) if cost_str else 0
        except ValueError:
            return 0
    
    try:
        content = file.stream.read()
        if content.startswith(b'\xef\xbb\xbf'):
            content = content[3:]
        stream = io.StringIO(content.decode("UTF-8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        imported_count = 0
        error_count = 0
        error_details = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                project = Project(
                    project_name=row.get('申报工程名称', ''),
                    project_cost=parse_cost(row.get('工程造价(万元)')),
                    declaring_company=row.get('申报企业名称', ''),
                    project_manager=row.get('项目经理姓名', ''),
                    contact_phone=row.get('联系人及电话', ''),
                    supervision_company=row.get('监理企业名称', ''),
                    project_director=row.get('项目总监姓名', ''),
                    certificate_number=row.get('参选证号码', ''),
                    participating_company=row.get('参建企业名称', ''),
                    creation_target=row.get('创建目标', ''),
                    region=row.get('区域', ''),
                    construction_unit=row.get('建设单位', ''),
                    start_date=parse_date(row.get('开工日期')),
                    end_date=parse_date(row.get('竣工日期')),
                    standardization_application_date=parse_date(row.get('标化工地申报时间')),
                    construction_permit_date=parse_date(row.get('施工许可证取得日期')),
                    city_standardization_inspection_date=parse_date(row.get('市标化检查时间')),
                    inspectors=row.get('检查人员', ''),
                    remarks=row.get('备注', ''),
                    status=row.get('状态', '正常'),
                    pre_score=parse_cost(row.get('预打分'))
                )
                db.session.add(project)
                imported_count += 1
            except Exception as e:
                error_count += 1
                if len(error_details) < 5:
                    error_details.append(f'行{row_num}: {str(e)}')
                continue
        
        db.session.commit()
        msg = f'导入完成！成功导入 {imported_count} 条记录'
        if error_count > 0:
            msg += f'，失败 {error_count} 条'
            if error_details:
                msg += f'\n错误详情: {"; ".join(error_details)}'
        flash(msg, 'success' if error_count == 0 else 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'导入失败：{str(e)}', 'danger')
    
    return redirect(url_for('settings'))


@app.route('/settings/backup', methods=['POST'])
def backup_database():
    try:
        backup_dir = app.config['BACKUP_FOLDER']
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'scms.db')
        
        backup_filename = f'backup_{datetime.now().strftime("%Y%m%d%H%M%S")}.db'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        shutil.copy2(db_path, backup_path)
        flash(f'数据库备份成功！备份文件：{backup_filename}', 'success')
    except Exception as e:
        flash(f'备份失败：{str(e)}', 'danger')
    
    return redirect(url_for('settings'))


@app.route('/settings/restore', methods=['POST'])
def restore_database():
    backup_filename = request.form.get('backup_filename', '')
    
    if backup_filename:
        backup_path = os.path.join(app.config['BACKUP_FOLDER'], backup_filename)
        if not os.path.exists(backup_path):
            flash('备份文件不存在', 'danger')
            return redirect(url_for('settings'))
    else:
        if 'backup_file' not in request.files:
            flash('请选择要恢复的备份文件', 'danger')
            return redirect(url_for('settings'))
        
        file = request.files['backup_file']
        if file.filename == '':
            flash('请选择要恢复的备份文件', 'danger')
            return redirect(url_for('settings'))
        
        try:
            db_path = os.path.join(os.path.dirname(__file__), 'data', 'scms.db')
            
            db.session.close()
            
            file.save(db_path)
            
            flash('数据库恢复成功！', 'success')
        except Exception as e:
            flash(f'恢复失败：{str(e)}', 'danger')
        
        return redirect(url_for('settings'))
    
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'scms.db')
        
        db.session.close()
        
        shutil.copy2(backup_path, db_path)
        
        flash('数据库恢复成功！', 'success')
    except Exception as e:
        flash(f'恢复失败：{str(e)}', 'danger')
    
    return redirect(url_for('settings'))


AUTO_BACKUP_CONFIG_FILE = 'config/auto_backup_config.json'

def get_config_path():
    return os.path.join(os.path.dirname(__file__), AUTO_BACKUP_CONFIG_FILE)

def load_auto_backup_config():
    config_path = get_config_path()
    default_config = {
        'enabled': False,
        'period': 'daily',
        'time': '02:00',
        'day': 1,
        'month_day': 1,
        'retention': 10,
        'next_backup': None
    }
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                default_config.update(config)
    except Exception:
        pass
    
    if default_config['enabled']:
        default_config['next_backup'] = calculate_next_backup_time(default_config)
    
    return default_config

def save_auto_backup_config(config):
    config_path = get_config_path()
    config_to_save = {k: v for k, v in config.items() if k != 'next_backup'}
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_to_save, f, ensure_ascii=False, indent=2)

def calculate_next_backup_time(config):
    if not config.get('enabled'):
        return None
    
    now = datetime.now()
    time_str = config.get('time', '02:00')
    hour, minute = map(int, time_str.split(':'))
    
    period = config.get('period', 'daily')
    
    if period == 'daily':
        next_backup = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_backup <= now:
            next_backup += timedelta(days=1)
    elif period == 'weekly':
        target_day = config.get('day', 1)
        days_ahead = target_day - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_backup = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_ahead)
        if next_backup <= now:
            next_backup += timedelta(days=7)
    elif period == 'monthly':
        target_day = config.get('month_day', 1)
        next_backup = now.replace(day=target_day, hour=hour, minute=minute, second=0, microsecond=0)
        if next_backup <= now:
            if now.month == 12:
                next_backup = next_backup.replace(year=now.year + 1, month=1)
            else:
                next_backup = next_backup.replace(month=now.month + 1)
    else:
        return None
    
    return next_backup.strftime('%Y-%m-%d %H:%M:%S')

def cleanup_old_backups(retention):
    if retention <= 0:
        return
    
    backup_dir = app.config['BACKUP_FOLDER']
    if not os.path.exists(backup_dir):
        return
    
    auto_backup_files = [f for f in os.listdir(backup_dir) if f.startswith('auto_backup_') and f.endswith('.db')]
    auto_backup_files.sort(reverse=True)
    
    for f in auto_backup_files[retention:]:
        try:
            os.remove(os.path.join(backup_dir, f))
        except Exception:
            pass


@app.route('/settings/auto-backup/config', methods=['POST'])
def update_auto_backup_config():
    try:
        data = request.get_json()
        
        config = {
            'enabled': data.get('enabled', False),
            'period': data.get('period', 'daily'),
            'time': data.get('time', '02:00'),
            'day': data.get('day', 1),
            'month_day': data.get('month_day', 1),
            'retention': data.get('retention', 10)
        }
        
        save_auto_backup_config(config)
        
        next_backup = calculate_next_backup_time(config) if config['enabled'] else None
        
        return jsonify({
            'success': True,
            'next_backup': next_backup
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/settings/auto-backup', methods=['POST'])
def toggle_auto_backup():
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)
        
        config = load_auto_backup_config()
        config['enabled'] = enabled
        save_auto_backup_config(config)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/certificate/check')
def check_certificate():
    certificate = request.args.get('certificate', '')
    project_id = request.args.get('project_id', type=int)
    
    query = Project.query.filter_by(certificate_number=certificate)
    if project_id:
        query = query.filter(Project.id != project_id)
    
    exists = query.first() is not None
    return jsonify({'exists': exists})


@app.route('/api/certificate/next')
def get_next_certificate():
    try:
        last_project = Project.query.filter(
            Project.certificate_number.like('市政____')
        ).order_by(Project.certificate_number.desc()).first()
        
        if last_project and last_project.certificate_number:
            import re
            match = re.search(r'市政(\d{4})', last_project.certificate_number)
            if match:
                last_number = int(match.group(1))
                next_number = last_number + 1
                next_certificate = f"市政{next_number:04d}"
                return jsonify({
                    'success': True,
                    'certificate_number': next_certificate,
                    'display_number': f"{next_number:04d}"
                })
        
        return jsonify({
            'success': True,
            'certificate_number': '市政0001',
            'display_number': '0001'
        })
    except Exception as e:
        logger.error(f"Error getting next certificate number: {str(e)}")
        return jsonify({
            'success': False,
            'error': '获取参选证号码失败'
        })


@app.route('/api/evaluation/save', methods=['POST'])
def save_evaluation():
    try:
        data = request.get_json()
        
        project_id = data.get('project_id')
        if not project_id:
            return jsonify({'success': False, 'error': '项目ID不能为空'})
        
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'success': False, 'error': '项目不存在'})
        
        inspection_date = data.get('city_standardization_inspection_date')
        if inspection_date:
            project.city_standardization_inspection_date = datetime.strptime(inspection_date, '%Y-%m-%d').date()
        
        inspectors = data.get('inspectors', '')
        if inspectors:
            project.inspectors = inspectors
        
        pre_score = data.get('pre_score')
        if pre_score:
            project.pre_score = float(pre_score)
        
        project.status = '已考评'
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': '考评录入成功'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving evaluation: {str(e)}")
        return jsonify({'success': False, 'error': f'保存失败：{str(e)}'})


_ocr_instance = None

def get_ocr_instance():
    global _ocr_instance
    if _ocr_instance is None:
        from rapidocr_onnxruntime import RapidOCR
        _ocr_instance = RapidOCR()
    return _ocr_instance

@app.route('/api/verify-password', methods=['POST'])
def verify_password():
    data = request.get_json()
    if not data or 'password' not in data:
        logger.warning("Password verification failed: No password provided")
        return jsonify({'success': False, 'error': '请输入密码'})
    
    password = data['password']
    
    if not SENSITIVE_PASSWORD_HASH:
        logger.error("SENSITIVE_PASSWORD_HASH not configured in environment")
        return jsonify({'success': False, 'error': '系统配置错误'})
    
    try:
        if bcrypt.checkpw(password.encode('utf-8'), SENSITIVE_PASSWORD_HASH.encode('utf-8')):
            session['sensitive_verified'] = True
            session['sensitive_verified_time'] = datetime.now().isoformat()
            logger.info("Password verification successful")
            return jsonify({'success': True})
        else:
            logger.warning("Password verification failed: Incorrect password")
            return jsonify({'success': False, 'error': '密码错误'})
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return jsonify({'success': False, 'error': '验证失败，请重试'})

@app.route('/api/check-sensitive-auth', methods=['GET'])
def check_sensitive_auth():
    verified = session.get('sensitive_verified', False)
    if verified:
        verified_time = session.get('sensitive_verified_time')
        if verified_time:
            try:
                verified_dt = datetime.fromisoformat(verified_time)
                if datetime.now() - verified_dt > timedelta(minutes=10):
                    session.pop('sensitive_verified', None)
                    session.pop('sensitive_verified_time', None)
                    return jsonify({'verified': False})
            except:
                pass
    return jsonify({'verified': verified})

@app.route('/api/clear-sensitive-auth', methods=['POST'])
def clear_sensitive_auth():
    session.pop('sensitive_verified', None)
    session.pop('sensitive_verified_time', None)
    return jsonify({'success': True})

@app.route('/api/ocr', methods=['POST'])
def ocr_recognize():
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': '请选择要上传的图片文件'})
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'error': '请选择要上传的图片文件'})
    
    allowed_extensions = {'jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff', 'webp'}
    file_ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if file_ext not in allowed_extensions:
        return jsonify({'success': False, 'error': '不支持的图片格式，请上传 JPG、PNG 等常见图片格式'})
    
    try:
        import numpy as np
        from PIL import Image
        
        image = Image.open(file.stream)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        max_width = 1280
        max_height = 1280
        original_size = f"{image.width}x{image.height}"
        resized = False
        
        if image.width > max_width or image.height > max_height:
            ratio = min(max_width / image.width, max_height / image.height)
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.LANCZOS)
            resized = True
        
        img_array = np.array(image)
        
        ocr = get_ocr_instance()
        result, elapse = ocr(img_array)
        
        if result is None or len(result) == 0:
            return jsonify({'success': False, 'error': '未能识别到任何文字，请确保图片清晰'})
        
        text_lines = []
        for item in result:
            if item and len(item) >= 2:
                text = item[1] if isinstance(item[1], str) else str(item[1])
                text_lines.append(text)
        
        full_text = '\n'.join(text_lines)
        
        extracted_info = extract_project_info(text_lines)
        
        return jsonify({
            'success': True,
            'full_text': full_text,
            'extracted': extracted_info,
            'debug': {
                'original_size': original_size,
                'resized': resized,
                'text_count': len(text_lines)
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'OCR识别失败：{str(e)}'})


def extract_project_info(text_lines):
    import re
    
    info = {
        'project_name': '',
        'project_cost': '',
        'declaring_company': '',
        'project_manager': '',
        'contact_phone': '',
        'supervision_company': '',
        'project_director': '',
        'construction_unit': '',
        'start_date': '',
        'end_date': ''
    }
    
    for i, line in enumerate(text_lines):
        line_clean = line.strip()
        
        if line_clean == '工程名称' and i + 1 < len(text_lines):
            project_name_parts = []
            for j in range(i + 1, min(i + 4, len(text_lines))):
                next_line = text_lines[j].strip()
                if next_line and '工程详细地址' not in next_line and '工程类别' not in next_line:
                    if '工程' in next_line[:4] or '地址' in next_line:
                        break
                    project_name_parts.append(next_line)
                    if next_line.endswith('）') or next_line.endswith('工程'):
                        break
                    if next_line.endswith('、'):
                        continue
                    if next_line.endswith('-') or next_line.endswith('（'):
                        continue
                    if j + 1 < len(text_lines):
                        peek_line = text_lines[j + 1].strip()
                        if peek_line and ('路' in peek_line[:2] or '道' in peek_line[:2] or peek_line.startswith('）') or peek_line.startswith('路')):
                            continue
                    break
                else:
                    break
            if project_name_parts:
                info['project_name'] = ''.join(project_name_parts)
            break
    
    for i, line in enumerate(text_lines):
        line_clean = line.strip()
        if '万元' in line_clean and len(line_clean) < 30:
            if '建安工程' in line_clean or '满足' in line_clean or '以上' in line_clean:
                continue
            cost_match = re.search(r'([\d.]+)\s*万元', line_clean)
            if cost_match:
                cost_val = cost_match.group(1)
                if len(cost_val) < 3:
                    continue
                if '.' not in cost_val and len(cost_val) > 6:
                    cost_val = cost_val[:4] + '.' + cost_val[4:]
                if '.' in cost_val and len(cost_val.split('.')[1]) > 4:
                    parts = cost_val.split('.')
                    cost_val = parts[0] + '.' + parts[1][:4]
                info['project_cost'] = cost_val
                break
    
    if not info['project_cost']:
        for i, line in enumerate(text_lines):
            line_clean = line.strip()
            
            if '工程造价' in line_clean or '工程规模' in line_clean:
                cost_match = re.search(r'([\d.]+)\s*万?', line_clean)
                if cost_match:
                    info['project_cost'] = cost_match.group(1)
                    break
                elif i + 1 < len(text_lines):
                    for j in range(i + 1, min(i + 5, len(text_lines))):
                        next_line = text_lines[j].strip()
                        if '开竣工' in next_line or '竣工日' in next_line or '并竣工' in next_line:
                            break
                        cost_match = re.search(r'^([\d.]+)', next_line)
                        if cost_match:
                            info['project_cost'] = cost_match.group(1)
                            break
                        cost_match = re.search(r'([\d.]+)\s*万元', next_line)
                        if cost_match:
                            info['project_cost'] = cost_match.group(1)
                            break
                    if info['project_cost']:
                        break
    
    if not info['project_cost']:
        for line in text_lines:
            cost_match = re.search(r'工程造价[：:\s]*([\d.]+)\s*万?', line)
            if cost_match:
                info['project_cost'] = cost_match.group(1)
                break
    
    for i, line in enumerate(text_lines):
        line_clean = line.strip()
        
        if line_clean == '施工单位' and i + 1 < len(text_lines):
            next_line = text_lines[i + 1].strip()
            if next_line == '建设单位':
                for j in range(i - 1, max(0, i - 6), -1):
                    candidate = text_lines[j].strip()
                    if candidate.endswith('公司') and '单位' not in candidate and len(candidate) > 4:
                        if '监理' not in candidate and '建设' not in candidate[:2]:
                            info['declaring_company'] = candidate
                            break
                    if candidate == '有限公司' and j > 0:
                        prev_line = text_lines[j - 1].strip()
                        if prev_line and '单位' not in prev_line and '监理' not in prev_line:
                            if prev_line.endswith('有限公司'):
                                info['declaring_company'] = prev_line
                            else:
                                combined = prev_line + '有限公司'
                                if '建设' not in combined[:2]:
                                    info['declaring_company'] = combined
                            break
            elif next_line and '单位' not in next_line and '建设' not in next_line[:2]:
                info['declaring_company'] = next_line
            break
    
    if not info['declaring_company']:
        for i, line in enumerate(text_lines):
            line_clean = line.strip()
            if line_clean == '施工单位' and i > 0:
                for j in range(i - 1, max(0, i - 6), -1):
                    candidate = text_lines[j].strip()
                    if candidate.endswith('公司') and '单位' not in candidate and len(candidate) > 4:
                        if '监理' not in candidate and '建设' not in candidate[:2]:
                            info['declaring_company'] = candidate
                            break
                    if candidate == '有限公司' and j > 0:
                        prev_line = text_lines[j - 1].strip()
                        if prev_line and '单位' not in prev_line and '监理' not in prev_line:
                            if prev_line.endswith('有限公司'):
                                info['declaring_company'] = prev_line
                            else:
                                combined = prev_line + '有限公司'
                                if '建设' not in combined[:2]:
                                    info['declaring_company'] = combined
                            break
                break
    
    if not info['declaring_company']:
        for i, line in enumerate(text_lines):
            line_clean = line.strip()
            if '施工单位' in line_clean and '联系人' not in line_clean:
                match = re.search(r'施工单位[：:\s]*(.+)', line_clean)
                if match:
                    company = match.group(1).strip()
                    if company and '单位' not in company:
                        info['declaring_company'] = company
                        break
    
    for i, line in enumerate(text_lines):
        line_clean = line.strip()
        
        if line_clean == '建设单位' and i + 1 < len(text_lines):
            next_line = text_lines[i + 1].strip()
            if next_line and '单位' not in next_line and '监理' not in next_line:
                info['construction_unit'] = next_line
            break
    
    for i, line in enumerate(text_lines):
        line_clean = line.strip()
        
        if ('监理单位' in line_clean or '监理单' in line_clean) and i + 1 < len(text_lines):
            next_line = text_lines[i + 1].strip()
            if next_line and '监理' not in next_line and '工程' not in next_line[:2] and '单位' not in next_line:
                info['supervision_company'] = next_line
            elif not info['supervision_company'] and i > 0:
                for j in range(i - 1, max(0, i - 3), -1):
                    candidate = text_lines[j].strip()
                    if candidate and '监理' in candidate and '公司' in candidate:
                        info['supervision_company'] = candidate
                        break
            break
    
    if not info['supervision_company']:
        for i, line in enumerate(text_lines):
            line_clean = line.strip()
            if '监理' in line_clean and '公司' in line_clean and '单位' not in line_clean:
                info['supervision_company'] = line_clean
                break
    
    for i, line in enumerate(text_lines):
        line_clean = line.strip()
        
        if '开竣工' in line_clean or '开工竣工' in line_clean or '竣工日' in line_clean or '竣工白' in line_clean or '并竣工' in line_clean or '开竣工日' in line_clean:
            date_match = re.search(r'(\d{4})[.\-/年:：,\s]+(\d{1,2})[.\-/月:：,\s]+(\d{1,2})', line_clean)
            if date_match:
                info['start_date'] = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"
            
            end_match = re.search(r'[-~至,]+\s*(\d{4})[.\-/年:：,\s]+(\d{1,2})[.\-/月:：,\s]+(\d{1,2})', line_clean)
            if end_match:
                info['end_date'] = f"{end_match.group(1)}-{end_match.group(2).zfill(2)}-{end_match.group(3).zfill(2)}"
            
            if not info['start_date']:
                partial_match = re.search(r'(\d{1,2})[-\s]+(\d{4})[.\-/年:：,\s]+(\d{1,2})[.\-/月:：,\s]+(\d{1,2})', line_clean)
                if partial_match:
                    year = partial_match.group(2)
                    month = partial_match.group(1)
                    if len(month) == 1:
                        month = '0' + month
                    year_prefix = year[:2]
                    year_suffix = year[2:]
                    start_year = year_prefix + month + year_suffix[:2] if int(month) <= 12 else year
                    info['start_date'] = f"{start_year}-{partial_match.group(3).zfill(2)}-{partial_match.group(4).zfill(2)}"
            
            if not info['start_date'] or not info['end_date']:
                for j in range(i + 1, min(i + 4, len(text_lines))):
                    next_line = text_lines[j].strip()
                    
                    if not info['start_date']:
                        date_match = re.search(r'(\d{4})[.\-/年:：,\s]+(\d{1,2})[.\-/月:：,\s]+(\d{1,2})', next_line)
                        if date_match:
                            info['start_date'] = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"
                    
                    if not info['end_date']:
                        end_match = re.search(r'[-~至,]+\s*(\d{4})[.\-/年:：,\s]+(\d{1,2})[.\-/月:：,\s]+(\d{1,2})', next_line)
                        if end_match:
                            info['end_date'] = f"{end_match.group(1)}-{end_match.group(2).zfill(2)}-{end_match.group(3).zfill(2)}"
                    
                    if not info['end_date']:
                        end_match = re.search(r'(\d{4})[.\-/年:：,\s]+(\d{1,2})[.\-/月:：,\s]+(\d{1,2})', next_line)
                        if end_match and info['start_date']:
                            info['end_date'] = f"{end_match.group(1)}-{end_match.group(2).zfill(2)}-{end_match.group(3).zfill(2)}"
            
            if info['start_date'] or info['end_date']:
                break
    
    if not info['start_date'] or not info['end_date']:
        for i, line in enumerate(text_lines):
            line_clean = line.strip()
            
            if '开工日' in line_clean and '竣工' not in line_clean:
                date_match = re.search(r'(\d{4})[.\-/年:：,\s]+(\d{1,2})[.\-/月:：,\s]+(\d{1,2})', line_clean)
                if date_match:
                    info['start_date'] = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"
                elif i + 1 < len(text_lines):
                    for j in range(i + 1, min(i + 3, len(text_lines))):
                        next_line = text_lines[j].strip()
                        date_match = re.search(r'(\d{4})[.\-/年:：,\s]+(\d{1,2})[.\-/月:：,\s]+(\d{1,2})', next_line)
                        if date_match:
                            info['start_date'] = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"
                            break
                break
        
        for i, line in enumerate(text_lines):
            line_clean = line.strip()
            
            if '竣工日' in line_clean and '开工' not in line_clean:
                date_match = re.search(r'(\d{4})[.\-/年:：,\s]+(\d{1,2})[.\-/月:：,\s]+(\d{1,2})', line_clean)
                if date_match:
                    info['end_date'] = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"
                elif i + 1 < len(text_lines):
                    for j in range(i + 1, min(i + 3, len(text_lines))):
                        next_line = text_lines[j].strip()
                        date_match = re.search(r'(\d{4})[.\-/年:：,\s]+(\d{1,2})[.\-/月:：,\s]+(\d{1,2})', next_line)
                        if date_match:
                            info['end_date'] = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"
                            break
                break
    
    for i, line in enumerate(text_lines):
        line_clean = line.strip()
        
        if ('项目经' in line_clean or '项目经理' in line_clean) and '项目总监' not in line_clean:
            name_in_line = re.search(r'项目经[理理球]?[\u4e00-\u9fa5]{0,2}([\u4e00-\u9fa5]{2,4})', line_clean)
            if name_in_line:
                info['project_manager'] = name_in_line.group(1)
            elif i + 1 < len(text_lines):
                for k in range(i + 1, min(i + 3, len(text_lines))):
                    next_line = text_lines[k].strip()
                    if next_line and len(next_line) <= 10 and '项目总监' not in next_line and '联系人' not in next_line and '施工单位' not in next_line and '开工' not in next_line and '竣工' not in next_line:
                        name_match = re.search(r'^[\u4e00-\u9fa5]{2,4}$', next_line)
                        if name_match:
                            info['project_manager'] = name_match.group()
                            break
            break
    
    for i, line in enumerate(text_lines):
        line_clean = line.strip()
        
        if '项目总监' in line_clean:
            name_in_line = re.search(r'项目总监[\u4e00-\u9fa5]{0,2}([\u4e00-\u9fa5]{2,4})', line_clean)
            if name_in_line:
                info['project_director'] = name_in_line.group(1)
            elif i + 1 < len(text_lines):
                for k in range(i + 1, min(i + 3, len(text_lines))):
                    next_line = text_lines[k].strip()
                    if next_line and len(next_line) <= 10 and '施工' not in next_line and '联系人' not in next_line and '项目经' not in next_line and '开工' not in next_line:
                        name_match = re.search(r'^[\u4e00-\u9fa5]{2,4}$', next_line)
                        if name_match:
                            info['project_director'] = name_match.group()
                            break
            break
    
    if not info['project_director'] and info['project_manager']:
        for i, line in enumerate(text_lines):
            line_clean = line.strip()
            if line_clean == info['project_manager'] and i + 1 < len(text_lines):
                next_line = text_lines[i + 1].strip()
                if next_line and len(next_line) <= 10 and '联系人' not in next_line and '施工单位' not in next_line and '项目经' not in next_line:
                    name_match = re.search(r'^[\u4e00-\u9fa5]{2,4}$', next_line)
                    if name_match and next_line != info['project_manager']:
                        info['project_director'] = next_line
                        break
    
    for i, line in enumerate(text_lines):
        line_clean = line.strip()
        
        if '联系电话' in line_clean and i + 1 < len(text_lines):
            next_line = text_lines[i + 1].strip()
            phone_match = re.search(r'(1[3-9]\d{9}|\d{3,4}[\-]?\d{7,8})', next_line)
            if phone_match:
                info['contact_phone'] = phone_match.group(1)
            break
    
    if not info['contact_phone']:
        for line in text_lines:
            phone_match = re.search(r'(1[3-9]\d{9})', line)
            if phone_match:
                info['contact_phone'] = phone_match.group(1)
                break
    
    return info


import threading
import time

_backup_scheduler_thread = None
_backup_scheduler_stop = threading.Event()

def backup_scheduler():
    while not _backup_scheduler_stop.is_set():
        try:
            config = load_auto_backup_config()
            if config.get('enabled'):
                now = datetime.now()
                time_str = config.get('time', '02:00')
                hour, minute = map(int, time_str.split(':'))
                period = config.get('period', 'daily')
                
                should_backup = False
                
                if period == 'daily':
                    if now.hour == hour and now.minute == minute:
                        should_backup = True
                elif period == 'weekly':
                    target_day = config.get('day', 1)
                    if now.weekday() == target_day and now.hour == hour and now.minute == minute:
                        should_backup = True
                elif period == 'monthly':
                    target_day = config.get('month_day', 1)
                    if now.day == target_day and now.hour == hour and now.minute == minute:
                        should_backup = True
                
                if should_backup:
                    try:
                        backup_dir = app.config['BACKUP_FOLDER']
                        if not os.path.exists(backup_dir):
                            os.makedirs(backup_dir)
                        
                        db_path = os.path.join(os.path.dirname(__file__), 'data', 'scms.db')
                        
                        backup_filename = f'auto_backup_{now.strftime("%Y%m%d%H%M%S")}.db'
                        backup_path = os.path.join(backup_dir, backup_filename)
                        
                        shutil.copy2(db_path, backup_path)
                        print(f'[{now.strftime("%Y-%m-%d %H:%M:%S")}] 自动备份完成: {backup_filename}')
                        
                        retention = config.get('retention', 10)
                        cleanup_old_backups(retention)
                    except Exception as e:
                        print(f'[{now.strftime("%Y-%m-%d %H:%M:%S")}] 自动备份失败: {str(e)}')
        except Exception as e:
            print(f'备份调度器错误: {str(e)}')
        
        time.sleep(60)

def start_backup_scheduler():
    global _backup_scheduler_thread
    if _backup_scheduler_thread is None or not _backup_scheduler_thread.is_alive():
        _backup_scheduler_stop.clear()
        _backup_scheduler_thread = threading.Thread(target=backup_scheduler, daemon=True)
        _backup_scheduler_thread.start()


with app.app_context():
    db.create_all()


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['BACKUP_FOLDER']):
        os.makedirs(app.config['BACKUP_FOLDER'])
    
    start_backup_scheduler()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
