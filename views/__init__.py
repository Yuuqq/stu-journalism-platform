# Pages module initialization
from .resume_builder import render_resume_builder
from .digital_twin import render_digital_twin
from .ai_copilot import render_ai_copilot
from .admin_dashboard import render_admin_dashboard

__all__ = [
    'render_resume_builder',
    'render_digital_twin',
    'render_ai_copilot',
    'render_admin_dashboard'
]
