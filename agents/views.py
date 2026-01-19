"""
API views for agent endpoints.
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction

from .models import AgentCallLog
from .serializers import (
    GeminiCostRequestSerializer,
    ComplianceRequestSerializer,
    OpsRequestSerializer
)
from .services import GeminiCostService, ComplianceService, OpsService

logger = logging.getLogger(__name__)


def _log_agent_call(agent_name: str, request_data: dict, response_data: dict):
    """Helper function to log agent calls."""
    try:
        with transaction.atomic():
            AgentCallLog.objects.create(
                agent_name=agent_name,
                request_payload=request_data,
                response_payload=response_data
            )
    except Exception as e:
        logger.error(f"Failed to log agent call: {e}")


@api_view(['POST'])
def gemini_cost_agent(request):
    """
    Gemini Cost Optimization Agent endpoint.
    
    POST /api/agent/gemini-cost/
    """
    logger.info("")
    logger.info(">>> INCOMING REQUEST: Gemini Cost Optimization Agent")
    logger.info(f"Request Source: {request.META.get('REMOTE_ADDR', 'Unknown')}")
    # logger.info(f"Request Timestamp: {request.META.get('HTTP_DATE', 'N/A')}")
    
    serializer = GeminiCostRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        logger.error(f"Validation Failed: {serializer.errors}")
        return Response(
            {"error": "Invalid request", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validated_data = serializer.validated_data
    delay_hours = validated_data['delay_hours']
    total_passengers = validated_data['total_passengers']
    vip_passengers = validated_data['vip_passengers']
    
    logger.info("Request Validated Successfully")
    logger.info("Initiating Agent Processing...")
    
    # Get recommendation from service
    response_data = GeminiCostService.get_recommendation(
        delay_hours=delay_hours,
        total_passengers=total_passengers,
        vip_passengers=vip_passengers
    )
    
    logger.info("Preparing Response Payload...")
    
    # Log the call
    _log_agent_call(
        agent_name=GeminiCostService.AGENT_NAME,
        request_data=request.data,
        response_data=response_data
    )
    
    logger.info("Response Ready - Returning to caller")
    logger.info("")
    
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
def compliance_agent(request):
    """
    Compliance Agent endpoint (rule-based).
    
    POST /api/agent/compliance/
    """
    logger.info("")
    logger.info(">>> INCOMING REQUEST: Compliance Agent")
    logger.info(f"Request Source: {request.META.get('REMOTE_ADDR', 'Unknown')}")
    
    serializer = ComplianceRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        logger.error(f"Validation Failed: {serializer.errors}")
        return Response(
            {"error": "Invalid request", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    delay_hours = serializer.validated_data['delay_hours']
    
    logger.info("Request Validated Successfully")
    logger.info("Initiating Compliance Rule Evaluation...")
    
    # Get rule from service
    response_data = ComplianceService.get_rule(delay_hours=delay_hours)
    
    logger.info("Compliance Assessment Complete")
    logger.info("Preparing Response Payload...")
    
    # Log the call
    _log_agent_call(
        agent_name=ComplianceService.AGENT_NAME,
        request_data=request.data,
        response_data=response_data
    )
    
    logger.info("Response Ready - Returning to caller")
    logger.info("")
    
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
def ops_agent(request):
    """
    Ops Feasibility Agent endpoint (mock).
    
    POST /api/agent/ops/
    """
    logger.info("")
    logger.info(">>> INCOMING REQUEST: Ops Feasibility Agent")
    logger.info(f"Request Source: {request.META.get('REMOTE_ADDR', 'Unknown')}")
    
    # Request body is optional for this endpoint
    serializer = OpsRequestSerializer(data=request.data or {})
    
    if not serializer.is_valid():
        logger.error(f"Validation Failed: {serializer.errors}")
        return Response(
            {"error": "Invalid request", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    logger.info("Request Validated Successfully")
    logger.info("Initiating Operational Feasibility Check...")
    
    # Get feasibility from service
    response_data = OpsService.get_feasibility()
    
    logger.info("Feasibility Assessment Complete")
    logger.info("Preparing Response Payload...")
    
    # Log the call
    _log_agent_call(
        agent_name=OpsService.AGENT_NAME,
        request_data=request.data or {},
        response_data=response_data
    )
    
    logger.info("Response Ready - Returning to caller")
    logger.info("")
    
    return Response(response_data, status=status.HTTP_200_OK)
