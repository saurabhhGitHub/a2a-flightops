"""
Database models for the agents app.

NOTE: This backend is STATELESS with respect to business data.
Salesforce is the system of record for Flight and Passenger data.

AgentCallLog is for observability only - it logs API calls for demo visibility.
"""
from django.db import models
from django.utils import timezone


class AgentCallLog(models.Model):
    """
    Log model for tracking all agent API calls.
    
    This is for observability only - not business state.
    Salesforce owns all business data (flights, passengers, decisions).
    """
    agent_name = models.CharField(max_length=100)
    request_payload = models.JSONField()
    response_payload = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['agent_name']),
        ]

    def __str__(self):
        return f"{self.agent_name} - {self.created_at}"
