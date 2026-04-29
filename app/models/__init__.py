# Database Models

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Project(db.Model):
    """Project model for managing construction projects"""
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
    
    def to_dict(self):
        """Convert project to dictionary"""
        return {
            'id': self.id,
            'project_name': self.project_name,
            'project_cost': float(self.project_cost) if self.project_cost else 0,
            'declaring_company': self.declaring_company,
            'project_manager': self.project_manager,
            'contact_phone': self.contact_phone,
            'supervision_company': self.supervision_company,
            'project_director': self.project_director,
            'certificate_number': self.certificate_number,
            'participating_company': self.participating_company,
            'creation_target': self.creation_target,
            'region': self.region,
            'construction_unit': self.construction_unit,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'standardization_application_date': self.standardization_application_date.isoformat() if self.standardization_application_date else None,
            'construction_permit_date': self.construction_permit_date.isoformat() if self.construction_permit_date else None,
            'city_standardization_inspection_date': self.city_standardization_inspection_date.isoformat() if self.city_standardization_inspection_date else None,
            'inspectors': self.inspectors,
            'remarks': self.remarks,
            'status': self.status,
            'pre_score': float(self.pre_score) if self.pre_score else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class User:
    """Simple user class for authentication"""
    def __init__(self, user_id):
        self.id = user_id
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)
