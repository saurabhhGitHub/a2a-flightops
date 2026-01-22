"""
URL configuration for flight_ops project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def root_view(request):
    """Root endpoint to show API information."""
    return JsonResponse({
        'message': 'Airline Disruption Control - Agent APIs & MCP Server',
        'version': '1.0',
        'endpoints': {
            'rest_apis': {
                'gemini_cost': '/api/agent/gemini-cost/',
                'compliance': '/api/agent/compliance/',
                'ops': '/api/agent/ops/',
            },
            'mcp_server': {
                'capabilities': '/mcp/capabilities',
                'tool_invoke': '/mcp/tools/invoke',
            }
        },
        'documentation': 'See README.md and MCP_README.md for API documentation'
    })

urlpatterns = [
    path('', root_view, name='root'),
    path('admin/', admin.site.urls),
    path('api/', include('agents.urls')),
    path('mcp/', include('agents.mcp_urls')),
]
