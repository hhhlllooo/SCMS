# Service layer for business logic

from datetime import datetime
from sqlalchemy import extract, and_, or_, func
from app.models import Project


class ProjectService:
    """Service class for project-related business logic"""
    
    @staticmethod
    def get_all_projects():
        """Get all projects"""
        return Project.query.all()
    
    @staticmethod
    def get_project_by_id(project_id):
        """Get project by ID"""
        return Project.query.get(project_id)
    
    @staticmethod
    def search_projects(search_keyword=None, filter_region=None, filter_status=None, 
                       order_by='certificate_number', order='desc'):
        """Search and filter projects"""
        query = Project.query
        
        if search_keyword:
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
        
        # Apply ordering
        column = getattr(Project, order_by, Project.certificate_number)
        if order == 'desc':
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())
        
        return query
    
    @staticmethod
    def get_pending_projects(search_keyword=None, filter_region=None):
        """Get projects with pending status"""
        query = Project.query.filter_by(status='待考评')
        
        if search_keyword:
            query = query.filter(
                or_(
                    Project.project_name.ilike(f'%{search_keyword}%'),
                    Project.declaring_company.ilike(f'%{search_keyword}%'),
                    Project.certificate_number.ilike(f'%{search_keyword}%')
                )
            )
        
        if filter_region:
            query = query.filter_by(region=filter_region)
        
        return query.order_by(Project.certificate_number.desc())
    
    @staticmethod
    def create_project(form_data):
        """Create a new project from form data"""
        from app.utils import normalize_certificate_number, parse_date
        
        project = Project(
            project_name=form_data.get('project_name', ''),
            project_cost=float(form_data.get('project_cost', 0) or 0),
            declaring_company=form_data.get('declaring_company', ''),
            project_manager=form_data.get('project_manager', ''),
            contact_phone=form_data.get('contact_phone', ''),
            supervision_company=form_data.get('supervision_company', ''),
            project_director=form_data.get('project_director', ''),
            certificate_number=normalize_certificate_number(form_data.get('certificate_number', '')),
            participating_company=form_data.get('participating_company', ''),
            creation_target=form_data.get('creation_target', ''),
            region=form_data.get('region', ''),
            construction_unit=form_data.get('construction_unit', ''),
            start_date=parse_date(form_data.get('start_date')),
            end_date=parse_date(form_data.get('end_date')),
            standardization_application_date=parse_date(form_data.get('standardization_application_date')),
            construction_permit_date=parse_date(form_data.get('construction_permit_date')),
            city_standardization_inspection_date=parse_date(form_data.get('city_standardization_inspection_date')),
            inspectors=form_data.get('inspectors', ''),
            remarks=form_data.get('remarks', ''),
            status=form_data.get('status', '正常'),
            pre_score=float(form_data.get('pre_score', 0) or 0)
        )
        
        return project
    
    @staticmethod
    def update_project(project, form_data):
        """Update existing project with form data"""
        from app.utils import normalize_certificate_number, parse_date
        
        project.project_name = form_data.get('project_name', project.project_name)
        project.project_cost = float(form_data.get('project_cost', 0) or 0)
        project.declaring_company = form_data.get('declaring_company', project.declaring_company)
        project.project_manager = form_data.get('project_manager', project.project_manager)
        project.contact_phone = form_data.get('contact_phone', project.contact_phone)
        project.supervision_company = form_data.get('supervision_company', project.supervision_company)
        project.project_director = form_data.get('project_director', project.project_director)
        project.certificate_number = normalize_certificate_number(form_data.get('certificate_number', project.certificate_number))
        project.participating_company = form_data.get('participating_company', project.participating_company)
        project.creation_target = form_data.get('creation_target', project.creation_target)
        project.region = form_data.get('region', project.region)
        project.construction_unit = form_data.get('construction_unit', project.construction_unit)
        project.start_date = parse_date(form_data.get('start_date')) or project.start_date
        project.end_date = parse_date(form_data.get('end_date')) or project.end_date
        project.standardization_application_date = parse_date(form_data.get('standardization_application_date')) or project.standardization_application_date
        project.construction_permit_date = parse_date(form_data.get('construction_permit_date')) or project.construction_permit_date
        project.city_standardization_inspection_date = parse_date(form_data.get('city_standardization_inspection_date')) or project.city_standardization_inspection_date
        project.inspectors = form_data.get('inspectors', project.inspectors)
        project.remarks = form_data.get('remarks', project.remarks)
        project.status = form_data.get('status', project.status)
        project.pre_score = float(form_data.get('pre_score', 0) or 0)
        
        return project
    
    @staticmethod
    def delete_project(project):
        """Delete a project"""
        from app.models import db
        db.session.delete(project)
        db.session.commit()
    
    @staticmethod
    def save_evaluation(project_id, score, remarks=None):
        """Save evaluation score for a project"""
        project = Project.query.get(project_id)
        if not project:
            return False, 'Project not found'
        
        project.pre_score = float(score or 0)
        if remarks:
            project.remarks = remarks
        project.status = '已考评'
        
        from app.models import db
        db.session.commit()
        return True, 'Evaluation saved successfully'
    
    @staticmethod
    def get_dashboard_stats(selected_year=None):
        """Get dashboard statistics"""
        from app.models import db
        
        if selected_year is None:
            selected_year = datetime.now().year
        
        if selected_year < 2025:
            selected_year = 2025
        
        total_projects = Project.query.count()
        
        # Status statistics
        status_stats = {}
        for status in ['', '正常', '待考评', '已考评', '许可证'][1:]:
            status_stats[status] = Project.query.filter_by(status=status).count()
        
        # Focus statuses
        focus_statuses = ['正常', '待考评', '许可证']
        focus_total = sum(status_stats.get(s, 0) for s in focus_statuses)
        
        # Region statistics
        region_choices = ['', '市本级', '海曙区', '江北区', '鄞州区', '镇海区', '北仑区', '奉化区', '象山县', '宁海县', '余姚市', '慈溪市', '高新区', '前湾新区', '石化区'][1:]
        region_stats = {}
        for region in region_choices:
            region_stats[region] = Project.query.filter_by(region=region).count()
        
        # Region status data
        region_status_data = {}
        for region in region_choices:
            region_status_data[region] = {}
            for status in focus_statuses:
                count = Project.query.filter_by(region=region, status=status).count()
                region_status_data[region][status] = count
        
        # Total cost
        total_cost = db.session.query(func.sum(Project.project_cost)).scalar() or 0
        
        # Monthly new projects
        monthly_new_projects = {month: 0 for month in range(1, 13)}
        monthly_inspection_projects = {month: 0 for month in range(1, 13)}
        
        # New projects by application date
        new_projects = Project.query.filter(
            and_(
                extract('year', Project.standardization_application_date) == selected_year,
                Project.standardization_application_date.isnot(None)
            )
        ).all()
        
        for p in new_projects:
            month = p.standardization_application_date.month
            monthly_new_projects[month] = monthly_new_projects.get(month, 0) + 1
        
        # Inspection projects
        inspection_projects = Project.query.filter(
            and_(
                extract('year', Project.city_standardization_inspection_date) == selected_year,
                Project.city_standardization_inspection_date.isnot(None)
            )
        ).all()
        
        for p in inspection_projects:
            month = p.city_standardization_inspection_date.month
            monthly_inspection_projects[month] = monthly_inspection_projects.get(month, 0) + 1
        
        # Quarterly summaries
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
        
        return {
            'total_projects': total_projects,
            'status_stats': status_stats,
            'focus_total': focus_total,
            'region_stats': region_stats,
            'region_status_data': region_status_data,
            'total_cost': total_cost,
            'selected_year': selected_year,
            'monthly_new_projects': monthly_new_projects,
            'monthly_inspection_projects': monthly_inspection_projects,
            'quarterly_new_projects': quarterly_new_projects,
            'quarterly_inspection_projects': quarterly_inspection_projects,
            'total_new_projects': sum(monthly_new_projects.values()),
            'total_inspection_projects': sum(monthly_inspection_projects.values())
        }
