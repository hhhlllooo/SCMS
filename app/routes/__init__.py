# Routes package

from app.routes.main_routes import main
from app.routes.project_routes import projects
from app.routes.settings_routes import settings
from app.routes.api_routes import api

__all__ = ['main', 'projects', 'settings', 'api']
