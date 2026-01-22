"""
MCP (Model Context Protocol) URL configuration.
"""
from django.urls import path
from . import mcp_views

app_name = 'mcp'

urlpatterns = [
    path('capabilities', mcp_views.mcp_capabilities, name='capabilities'),
    path('tools/invoke', mcp_views.mcp_tool_invoke, name='tool-invoke'),
]
