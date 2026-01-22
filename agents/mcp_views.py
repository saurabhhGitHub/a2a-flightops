"""
MCP (Model Context Protocol) Views.

Implements MCP semantics: capability discovery and tool invocation.
"""
import logging
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .mcp_weather_service import WeatherDisruptionService

logger = logging.getLogger('agents')


@csrf_exempt
@require_http_methods(["GET"])
def mcp_capabilities(request):
    """
    MCP Capability Discovery Endpoint.
    
    Returns discoverable tools and their schemas.
    This is how MCP clients discover available capabilities.
    
    GET /mcp/capabilities
    """
    logger.info("=" * 60)
    logger.info("MCP CAPABILITY DISCOVERY - REQUESTED")
    logger.info("=" * 60)
    
    capabilities = {
        "mcp_version": "1.0",
        "server_name": "airline_disruption_context",
        "server_version": "1.0.0",
        "tools": [
            {
                "name": "weather_disruption_context",
                "description": "Provides weather severity and cascading delay risk for an airport. Returns external weather context to inform disruption decision-making.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "airport_code": {
                            "type": "string",
                            "description": "IATA airport code (e.g., 'DEL', 'BOM', 'BLR')",
                            "pattern": "^[A-Z]{3}$",
                            "examples": ["DEL", "BOM", "BLR", "MAA"]
                        }
                    },
                    "required": ["airport_code"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "severity": {
                            "type": "string",
                            "enum": ["LOW", "MEDIUM", "HIGH"],
                            "description": "Weather severity level"
                        },
                        "expected_duration_hours": {
                            "type": "number",
                            "description": "Expected disruption duration in hours"
                        },
                        "cascading_delay_risk": {
                            "type": "string",
                            "enum": ["LOW", "MEDIUM", "HIGH"],
                            "description": "Risk of delays cascading to other flights"
                        },
                        "source": {
                            "type": "string",
                            "enum": ["v1", "v2"],
                            "description": "Data source indicator"
                        }
                    },
                    "required": ["severity", "expected_duration_hours", "cascading_delay_risk", "source"]
                }
            }
        ]
    }
    
    logger.info("Capabilities: 1 tool available (weather_disruption_context)")
    logger.info("=" * 60)
    
    return JsonResponse(capabilities, json_dumps_params={'indent': 2})


@csrf_exempt
@require_http_methods(["POST"])
def mcp_tool_invoke(request):
    """
    MCP Tool Invocation Endpoint.
    
    Invokes the requested tool with provided arguments.
    Always returns valid MCP response (never fails).
    
    POST /mcp/tools/invoke
    Body: {
        "tool": "weather_disruption_context",
        "arguments": {
            "airport_code": "DEL"
        }
    }
    """
    logger.info("")
    logger.info(">>> MCP TOOL INVOCATION - REQUESTED")
    logger.info(f"Request Source: {request.META.get('REMOTE_ADDR', 'Unknown')}")
    
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Invalid JSON in request body: {e}")
        return JsonResponse({
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Request body must be valid JSON"
            }
        }, status=400)
    
    tool_name = body.get("tool")
    arguments = body.get("arguments", {})
    
    if not tool_name:
        logger.error("Tool name missing in request")
        return JsonResponse({
            "error": {
                "code": "MISSING_TOOL",
                "message": "Tool name is required"
            }
        }, status=400)
    
    logger.info(f"Tool: {tool_name}")
    logger.info(f"Arguments: {arguments}")
    
    # Route to appropriate tool handler
    if tool_name == "weather_disruption_context":
        airport_code = arguments.get("airport_code")
        
        if not airport_code:
            logger.error("airport_code missing in arguments")
            return JsonResponse({
                "error": {
                    "code": "INVALID_ARGUMENTS",
                    "message": "airport_code is required"
                }
            }, status=400)
        
        # Validate airport code format
        if not isinstance(airport_code, str) or len(airport_code) != 3:
            logger.error(f"Invalid airport_code format: {airport_code}")
            return JsonResponse({
                "error": {
                    "code": "INVALID_ARGUMENTS",
                    "message": "airport_code must be a 3-letter IATA code"
                }
            }, status=400)
        
        logger.info("Invoking weather_disruption_context tool...")
        
        # Get weather context (always succeeds - has fallback)
        result = WeatherDisruptionService.get_weather_context(airport_code)
        
        logger.info("Tool invocation complete")
        logger.info("")
        
        return JsonResponse({
            "tool": tool_name,
            "result": result
        })
    
    else:
        logger.error(f"Unknown tool: {tool_name}")
        return JsonResponse({
            "error": {
                "code": "UNKNOWN_TOOL",
                "message": f"Tool '{tool_name}' is not available. Use /mcp/capabilities to discover available tools."
            }
        }, status=404)
