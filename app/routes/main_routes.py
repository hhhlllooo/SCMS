# Main routes blueprint

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models import db, Project
from app.services import ProjectService
from app.utils import REGION_CHOICES, STATUS_CHOICES, TARGET_CHOICES, validate_certificate_number

main = Blueprint('main', __name__)


def get_pagination_args():
    """Get pagination parameters from request"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    if per_page not in [10, 20, 30]:
        per_page = 20
    return page, per_page


@main.route('/')
def index():
    """Redirect to project list"""
    return redirect(url_for('main.project_list'))


@main.route('/dashboard')
def dashboard():
    """Dashboard view with statistics"""
    selected_year = request.args.get('year', None)
    if selected_year:
        selected_year = int(selected_year)
    
    stats = ProjectService.get_dashboard_stats(selected_year)
    
    # Get recent projects
    recent_projects = Project.query.order_by(Project.certificate_number.desc()).limit(5).all()
    
    # Generate available years
    from datetime import datetime
    available_years = list(range(2025, datetime.now().year + 2))
    
    return render_template('dashboard.html',
                         total_projects=stats['total_projects'],
                         status_stats=stats['status_stats'],
                         focus_total=stats['focus_total'],
                         region_stats=stats['region_stats'],
                         region_status_data=stats['region_status_data'],
                         region_choices=REGION_CHOICES,
                         recent_projects=recent_projects,
                         total_cost=stats['total_cost'],
                         selected_year=stats['selected_year'],
                         available_years=available_years,
                         monthly_new_projects=stats['monthly_new_projects'],
                         monthly_inspection_projects=stats['monthly_inspection_projects'],
                         quarterly_new_projects=stats['quarterly_new_projects'],
                         quarterly_inspection_projects=stats['quarterly_inspection_projects'],
                         total_new_projects=stats['total_new_projects'],
                         total_inspection_projects=stats['total_inspection_projects'])


@main.route('/projects')
def project_list():
    """Project list view with search and filtering"""
    page, per_page = get_pagination_args()
    
    search_keyword = request.args.get('search', '').strip()
    filter_region = request.args.get('filter_region', '')
    filter_status = request.args.get('filter_status', '')
    
    query = ProjectService.search_projects(
        search_keyword=search_keyword,
        filter_region=filter_region,
        filter_status=filter_status
    )
    
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


@main.route('/pending')
def pending_list():
    """Pending projects list"""
    page, per_page = get_pagination_args()
    
    search_keyword = request.args.get('search', '').strip()
    filter_region = request.args.get('filter_region', '')
    
    query = ProjectService.get_pending_projects(
        search_keyword=search_keyword,
        filter_region=filter_region
    )
    
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


@main.route('/evaluation-form/<int:id>')
def evaluation_form(id):
    """Evaluation form for a project"""
    project = Project.query.get_or_404(id)
    return render_template('evaluation_form.html', project=project)
