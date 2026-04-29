# Utility functions

import re
from datetime import datetime


REGION_CHOICES = ['', '市本级', '海曙区', '江北区', '鄞州区', '镇海区', '北仑区', '奉化区', '象山县', '宁海县', '余姚市', '慈溪市', '高新区', '前湾新区', '石化区']
STATUS_CHOICES = ['', '正常', '待考评', '已考评', '许可证']
TARGET_CHOICES = ['', '市标化', '市标化 省标化']


def validate_certificate_number(certificate_number, exclude_id=None):
    """Validate certificate number format and uniqueness"""
    if not certificate_number:
        return {'valid': False, 'error': '参选证号码不能为空'}
    
    if not re.match(r'^市政\d{4}$', certificate_number):
        return {'valid': False, 'error': '参选证号码格式不正确，应为"市政"加四位数字（如：市政 0001）'}
    
    from app.models import Project
    query = Project.query.filter_by(certificate_number=certificate_number)
    if exclude_id:
        query = query.filter(Project.id != exclude_id)
    
    if query.first():
        return {'valid': False, 'error': f'参选证号码"{certificate_number}"已存在，请使用其他号码'}
    
    return {'valid': True, 'error': None}


def normalize_certificate_number(certificate_input):
    """Normalize certificate number to standard format"""
    if not certificate_input:
        return ''
    
    certificate_input = certificate_input.strip()
    
    if re.match(r'^市政\d{4}$', certificate_input):
        return certificate_input
    
    digits = re.sub(r'\D', '', certificate_input)
    if len(digits) == 4:
        return '市政' + digits
    
    return certificate_input


def get_next_certificate_number():
    """Generate next available certificate number"""
    from app.models import Project
    
    # Get all certificate numbers
    projects = Project.query.filter(
        Project.certificate_number.like('市政%')
    ).all()
    
    max_num = 0
    for p in projects:
        match = re.match(r'^市政(\d{4})$', p.certificate_number)
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num
    
    return f'市政{str(max_num + 1).zfill(4)}'


def parse_date(date_string):
    """Parse date string to date object"""
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        return None


def format_response(success=True, message='', data=None):
    """Format API response"""
    return {
        'success': success,
        'message': message,
        'data': data or {}
    }
