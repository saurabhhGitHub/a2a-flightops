from django.contrib import admin
from .models import AgentCallLog


@admin.register(AgentCallLog)
class AgentCallLogAdmin(admin.ModelAdmin):
    list_display = ['agent_name', 'created_at']
    list_filter = ['agent_name', 'created_at']
    readonly_fields = ['created_at']
    search_fields = ['agent_name']
