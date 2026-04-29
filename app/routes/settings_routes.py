# Settings and admin routes blueprint

from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, send_file
import os
import csv
import io
import shutil
import re
from datetime import datetime
from urllib.parse import quote

from app.models import db, Project
from app.utils import REGION_CHOICES, STATUS_CHOICES

settings = Blueprint('settings', __name__, url_prefix='/settings')


def load_auto_backup_config():
    """Load auto backup configuration"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'auto_backup.json')
    default_config = {
        'enabled': False,
        'frequency': 'daily',
        'time': '02:00',
        'retention': 30,
        'last_run': None,
        'next_run': None
    }
    
    if not os.path.exists(config_path):
        return default_config
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            import json
            config = json.load(f)
            return {**default_config, **config}
    except:
        return default_config


def save_auto_backup_config(config):
    """Save auto backup configuration"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'auto_backup.json')
    config_dir = os.path.dirname(config_path)
    
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        import json
        json.dump(config, f, ensure_ascii=False, indent=2)


@settings.route('/')
def settings_view():
    """Settings page"""
    import platform
    
    backup_dir = 'data/backups'
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


@settings.route('/export', methods=['POST'])
def export_csv():
    """Export projects to CSV"""
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

    headers = ['申报工程名称', '工程造价 (万元)', '申报企业名称', '项目经理姓名', '联系人及电话',
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


@settings.route('/import', methods=['POST'])
def import_csv():
    """Import projects from CSV"""
    if 'csv_file' not in request.files:
        flash('请选择要导入的 CSV 文件', 'danger')
        return redirect(url_for('settings.settings_view'))

    file = request.files['csv_file']
    if file.filename == '':
        flash('请选择要导入的 CSV 文件', 'danger')
        return redirect(url_for('settings.settings_view'))

    if not file.filename.endswith('.csv'):
        flash('请选择 CSV 格式的文件', 'danger')
        return redirect(url_for('settings.settings_view'))

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
                    project_cost=parse_cost(row.get('工程造价 (万元)')),
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
                msg += f'\\n错误详情：{"; ".join(error_details)}'
        flash(msg, 'success' if error_count == 0 else 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'导入失败：{str(e)}', 'danger')

    return redirect(url_for('settings.settings_view'))


@settings.route('/backup', methods=['POST'])
def backup_database():
    """Backup database"""
    try:
        backup_dir = 'data/backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        db_path = 'data/scms.db'

        backup_filename = f'backup_{datetime.now().strftime("%Y%m%d%H%M%S")}.db'
        backup_path = os.path.join(backup_dir, backup_filename)

        shutil.copy2(db_path, backup_path)
        flash(f'数据库备份成功！备份文件：{backup_filename}', 'success')
    except Exception as e:
        flash(f'备份失败：{str(e)}', 'danger')

    return redirect(url_for('settings.settings_view'))


@settings.route('/restore', methods=['POST'])
def restore_database():
    """Restore database from backup"""
    backup_filename = request.form.get('backup_filename', '')

    if not backup_filename:
        flash('请选择要恢复的备份文件', 'danger')
        return redirect(url_for('settings.settings_view'))

    try:
        backup_dir = 'data/backups'
        db_path = 'data/scms.db'
        backup_path = os.path.join(backup_dir, backup_filename)

        if not os.path.exists(backup_path):
            flash('备份文件不存在', 'danger')
            return redirect(url_for('settings.settings_view'))

        # Create temporary backup before restore
        if os.path.exists(db_path):
            temp_backup = f'{db_path}.backup_{datetime.now().strftime("%Y%m%d%H%M%S")}'
            shutil.copy2(db_path, temp_backup)

        shutil.copy2(backup_path, db_path)
        flash('数据库恢复成功！', 'success')
    except Exception as e:
        flash(f'恢复失败：{str(e)}', 'danger')

    return redirect(url_for('settings.settings_view'))


@settings.route('/auto-backup/config', methods=['POST'])
def update_auto_backup_config():
    """Update auto backup configuration"""
    config = load_auto_backup_config()
    
    config['frequency'] = request.form.get('frequency', 'daily')
    config['time'] = request.form.get('time', '02:00')
    config['retention'] = int(request.form.get('retention', 30))
    
    # Calculate next run time
    from datetime import timedelta
    hour, minute = map(int, config['time'].split(':'))
    now = datetime.now()
    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    if next_run <= now:
        next_run += timedelta(days=1)
    
    config['next_run'] = next_run.strftime('%Y-%m-%d %H:%M:%S')
    
    save_auto_backup_config(config)
    flash('自动备份配置已保存', 'success')
    
    return redirect(url_for('settings.settings_view'))


@settings.route('/auto-backup', methods=['POST'])
def toggle_auto_backup():
    """Toggle auto backup enabled status"""
    config = load_auto_backup_config()
    config['enabled'] = not config.get('enabled', False)
    
    if config['enabled']:
        # Calculate next run time when enabling
        from datetime import timedelta
        hour, minute = map(int, config.get('time', '02:00').split(':'))
        now = datetime.now()
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if next_run <= now:
            next_run += timedelta(days=1)
        
        config['next_run'] = next_run.strftime('%Y-%m-%d %H:%M:%S')
    
    save_auto_backup_config(config)
    
    status = '已启用' if config['enabled'] else '已禁用'
    flash(f'自动备份{status}', 'success')
    
    return redirect(url_for('settings.settings_view'))
