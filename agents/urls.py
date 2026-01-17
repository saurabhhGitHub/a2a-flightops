"""
URL configuration for agents app.
"""
from django.urls import path
from . import views

app_name = 'agents'

urlpatterns = [
    path('agent/gemini-cost/', views.gemini_cost_agent, name='gemini-cost'),
    path('agent/compliance/', views.compliance_agent, name='compliance'),
    path('agent/ops/', views.ops_agent, name='ops'),
]
