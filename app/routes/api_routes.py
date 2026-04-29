# API routes blueprint

from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
import re
import logging

from app.models import db, Project
from app.utils import validate_certificate_number, get_next_certificate_number, format_response

api = Blueprint('api', __name__, url_prefix='/api')

logger = logging.getLogger(__name__)


@api.route('/certificate/check')
def check_certificate():
    """Check if certificate number exists"""
    certificate = request.args.get('certificate', '')
    project_id = request.args.get('project_id', type=int)

    query = Project.query.filter_by(certificate_number=certificate)
    if project_id:
        query = query.filter(Project.id != project_id)

    exists = query.first() is not None
    return jsonify({'exists': exists})


@api.route('/certificate/next')
def get_next_certificate():
    """Get next available certificate number"""
    try:
        last_project = Project.query.filter(
            Project.certificate_number.like('市政____')
        ).order_by(Project.certificate_number.desc()).first()

        if last_project and last_project.certificate_number:
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
            'certificate_number': '市政 0001',
            'display_number': '0001'
        })
    except Exception as e:
        logger.error(f"Error getting next certificate number: {str(e)}")
        return jsonify({
            'success': False,
            'error': '获取参选证号码失败'
        })


@api.route('/evaluation/save', methods=['POST'])
def save_evaluation():
    """Save evaluation score for a project"""
    try:
        data = request.get_json()

        project_id = data.get('project_id')
        if not project_id:
            return jsonify({'success': False, 'error': '项目 ID 不能为空'})

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


@api.route('/verify-password', methods=['POST'])
def verify_password():
    """Verify sensitive operation password"""
    import bcrypt
    import os
    
    data = request.get_json()
    if not data or 'password' not in data:
        logger.warning("Password verification failed: No password provided")
        return jsonify({'success': False, 'error': '请输入密码'})

    password = data['password']
    sensitive_password_hash = os.getenv('SENSITIVE_PASSWORD_HASH')

    if not sensitive_password_hash:
        logger.error("SENSITIVE_PASSWORD_HASH not configured in environment")
        return jsonify({'success': False, 'error': '系统配置错误'})

    try:
        if bcrypt.checkpw(password.encode('utf-8'), sensitive_password_hash.encode('utf-8')):
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


@api.route('/check-sensitive-auth', methods=['GET'])
def check_sensitive_auth():
    """Check if user has sensitive auth"""
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


@api.route('/clear-sensitive-auth', methods=['POST'])
def clear_sensitive_auth():
    """Clear sensitive auth"""
    session.pop('sensitive_verified', None)
    session.pop('sensitive_verified_time', None)
    return jsonify({'success': True})


@api.route('/ocr', methods=['POST'])
def ocr_recognize():
    """OCR recognition for image"""
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

        # Lazy load OCR
        from rapidocr_onnxruntime import RapidOCR
        ocr = RapidOCR()
        result, elapse = ocr(img_array)

        if result is None or len(result) == 0:
            return jsonify({'success': False, 'error': '未能识别到任何文字，请确保图片清晰'})

        text_lines = []
        for item in result:
            if item and len(item) >= 2:
                text = item[1] if isinstance(item[1], str) else str(item[1])
                text_lines.append(text)

        full_text = '\n'.join(text_lines)

        # Extract project info from text
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
        return jsonify({'success': False, 'error': f'OCR 识别失败：{str(e)}'})


def extract_project_info(text_lines):
    """Extract project information from OCR text"""
    extracted = {}
    
    patterns = {
        'project_name': r'(申报工程 | 工程名称)[:：\s]*(.+?)(?:\n|$)',
        'declaring_company': r'(申报企业 | 建设单位)[:：\s]*(.+?)(?:\n|$)',
        'project_manager': r'(项目经理 | 负责人)[:：\s]*(.+?)(?:\n|$)',
        'contact_phone': r'(联系 (?:方式 | 电话)|手机|电话)[:：\s]*([\d\-]+)',
        'supervision_company': r'(监理企业 | 监理单位)[:：\s]*(.+?)(?:\n|$)',
        'project_director': r'(项目总监 | 总监)[:：\s]*(.+?)(?:\n|$)',
        'cost': r'(工程造价 | 投资额)[:：\s]*([\d.]+)',
        'area': r'(建筑面积 | 规模)[:：\s]*([\d.]+)',
        'start_date': r'(开工日期 | 开工时间)[:：\s]*(\d{4}[-./]\d{1,2}[-./]\d{1,2})',
        'end_date': r'(竣工日期 | 完工时间)[:：\s]*(\d{4}[-./]\d{1,2}[-./]\d{1,2})',
    }
    
    full_text = '\n'.join(text_lines)
    
    for key, pattern in patterns.items():
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            groups = match.groups()
            extracted[key] = groups[-1].strip() if groups else ''
    
    return extracted
