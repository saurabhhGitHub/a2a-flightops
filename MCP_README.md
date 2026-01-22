# MCP Weather Disruption Context Server

## What is MCP?

**Model Context Protocol (MCP)** is a protocol for AI systems to discover and use external tools and context providers. Unlike traditional REST APIs, MCP emphasizes:

- **Capability Discovery**: Clients can discover available tools and their schemas
- **Tool Definition**: Structured, machine-readable tool definitions
- **Tool Invocation**: Standardized way to invoke tools with arguments
- **Structured Responses**: Always returns valid, schema-compliant responses

This MCP server provides **external situation awareness** (weather-related disruption context) for enterprise AI systems like Salesforce Agentforce.

## Architecture Overview

```
┌─────────────────────┐
│  Salesforce         │
│  Agentforce         │
│  (Decision Owner)   │
└──────────┬──────────┘
           │
           │ MCP Protocol
           │ (Tool Discovery + Invocation)
           │
┌──────────▼──────────────────────────┐
│  MCP Weather Context Server         │
│  (This Server)                      │
│                                     │
│  ┌──────────────────────────────┐   │
│  │  Capability Discovery        │   │
│  │  GET /mcp/capabilities       │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌──────────────────────────────┐   │
│  │  Tool Invocation             │   │
│  │  POST /mcp/tools/invoke      │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌──────────────────────────────┐   │
│  │  Weather Service             │   │
│  │  - Real API (OpenWeather)    │   │
│  │  - Fallback Logic            │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
           │
           │ HTTP Request
           │ (if API key configured)
           │
┌──────────▼──────────┐
│  OpenWeatherMap API  │
│  (External Service)  │
└─────────────────────┘
```

## Why MCP Instead of REST?

### Traditional REST API Limitations:
- **No Discovery**: Clients must know endpoints in advance
- **Ad-hoc Schemas**: Each API defines its own response format
- **No Tool Semantics**: REST treats everything as resources, not tools

### MCP Advantages:
- **Discoverable**: Clients can query available capabilities
- **Structured**: Machine-readable input/output schemas
- **Tool-Oriented**: Designed for AI systems to use tools
- **Enterprise-Ready**: Fits into agent orchestration frameworks

## Why Fallback Logic is Critical

### The Reliability Principle

**"MCP is not about correctness. It is about availability and adaptability."**

In enterprise systems, **availability trumps perfection**. The MCP server MUST always return valid responses, even when external dependencies fail.

### Fallback Scenarios

The server falls back to hardcoded logic when:

1. **Weather API Key Missing**: `WEATHER_API_KEY` not configured
2. **API Unavailable**: OpenWeatherMap service down
3. **Network Timeout**: Request exceeds 5-second timeout
4. **Malformed Response**: API returns unexpected data format
5. **Unknown Airport**: Airport code not in mapping

### Fallback Rules

```python
HIGH_SEVERITY_AIRPORTS = {'DEL', 'BOM', 'CCU', 'BLR'}

if airport_code in HIGH_SEVERITY_AIRPORTS:
    severity = "HIGH"
    expected_duration_hours = 4.0
    cascading_delay_risk = "HIGH"
else:
    severity = "MEDIUM"
    expected_duration_hours = 2.0
    cascading_delay_risk = "MEDIUM"
```

### Fallback is NOT an Error

The `source` field in responses indicates data origin:
- `"source": "v1"` - Real weather data used
- `"source": "v2"` - Fallback logic used

**Both are valid responses.** The consumer should not treat v2 as an error condition.

## API Endpoints

### 1. Capability Discovery

**GET** `/mcp/capabilities`

Returns available tools and their schemas.

**Response:**
```json
{
  "mcp_version": "1.0",
  "server_name": "airline_disruption_context",
  "server_version": "1.0.0",
  "tools": [
    {
      "name": "weather_disruption_context",
      "description": "Provides weather severity and cascading delay risk...",
      "input_schema": { ... },
      "output_schema": { ... }
    }
  ]
}
```

### 2. Tool Invocation

**POST** `/mcp/tools/invoke`

Invokes a tool with provided arguments.

**Request:**
```json
{
  "tool": "weather_disruption_context",
  "arguments": {
    "airport_code": "DEL"
  }
}
```

**Response (Success):**
```json
{
  "tool": "weather_disruption_context",
  "result": {
    "severity": "HIGH",
    "expected_duration_hours": 4.0,
    "cascading_delay_risk": "HIGH",
    "source": "v1"
  }
}
```

**Response (Fallback):**
```json
{
  "tool": "weather_disruption_context",
  "result": {
    "severity": "HIGH",
    "expected_duration_hours": 4.0,
    "cascading_delay_risk": "HIGH",
    "source": "v2"
  }
}
```

## Weather Severity Normalization

The service normalizes real weather data into three severity levels:

### HIGH Severity
- Thunderstorms or extreme weather
- Heavy/severe precipitation
- Wind speed > 15 m/s
- Visibility < 1000 meters

### MEDIUM Severity
- Rain, snow, or drizzle
- Wind speed > 8 m/s
- Visibility < 5000 meters

### LOW Severity
- Clear or light conditions
- Normal wind and visibility

## Cascading Delay Risk Assessment

Cascading risk considers:
1. **Weather Severity**: Higher severity = higher cascading risk
2. **Airport Hub Status**: Major hubs (DEL, BOM, BLR, MAA) have higher cascading risk

## Configuration

### Environment Variables

```bash
# Optional: OpenWeatherMap API key
# Get free key from: https://openweathermap.org/api
WEATHER_API_KEY=your_api_key_here

# If not set, server uses fallback logic (still fully functional)
```

### Setting Up Weather API (Optional)

1. Sign up at https://openweathermap.org/api
2. Get free API key (1000 calls/day)
3. Set `WEATHER_API_KEY` environment variable
4. Server will use real weather data when available

**Note**: Server works perfectly without API key using fallback logic.

## Example Usage

### Discover Capabilities

```bash
curl https://your-server.com/mcp/capabilities
```

### Invoke Weather Tool

```bash
curl -X POST https://your-server.com/mcp/tools/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "weather_disruption_context",
    "arguments": {
      "airport_code": "DEL"
    }
  }'
```

### Python Example

```python
import requests

# Discover capabilities
capabilities = requests.get("https://your-server.com/mcp/capabilities").json()
print(f"Available tools: {[t['name'] for t in capabilities['tools']]}")

# Invoke tool
response = requests.post(
    "https://your-server.com/mcp/tools/invoke",
    json={
        "tool": "weather_disruption_context",
        "arguments": {"airport_code": "BOM"}
    }
).json()

result = response["result"]
print(f"Severity: {result['severity']}")
print(f"Source: {result['source']}")
```

## Integration with Salesforce Agentforce

### How Agentforce Uses MCP

1. **Discovery Phase**: Agentforce queries `/mcp/capabilities` to discover available tools
2. **Decision Phase**: When evaluating disruption scenarios, Agentforce invokes `/mcp/tools/invoke` with airport code
3. **Context Integration**: Weather context informs decision-making but does not make decisions

### Key Principle

**This MCP server provides context, not decisions.**

- ✅ Provides weather severity and risk assessment
- ✅ Informs Agentforce decision-making
- ❌ Does NOT decide hotel allocation
- ❌ Does NOT modify Salesforce records
- ❌ Does NOT replace Agentforce agents

## Error Handling

The MCP server **never fails** a request. All errors are handled gracefully:

- **Invalid JSON**: Returns 400 with error schema
- **Missing Tool**: Returns 404 with error message
- **Invalid Arguments**: Returns 400 with validation error
- **Weather API Failure**: Falls back to hardcoded logic (returns 200)

## Stateless Design

This server is **completely stateless**:
- No database for weather data
- No caching of API responses
- No session management
- Each request is independent

This ensures:
- Horizontal scalability
- No data consistency issues
- Simple deployment
- No cleanup required

## Deployment

### Heroku Deployment

The server is configured for Heroku deployment:

```bash
# Set environment variables
heroku config:set WEATHER_API_KEY=your_key_here

# Deploy
git push heroku main
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (optional)
export WEATHER_API_KEY=your_key_here

# Run server
python manage.py runserver
```

## Monitoring and Observability

All tool invocations are logged with:
- Airport code requested
- Data source (real API or fallback)
- Severity and risk assessment
- Processing time

Check application logs to monitor:
- Fallback usage frequency
- API availability
- Response times

## Best Practices

1. **Always Handle Both Versions**: Consumers should treat both `v1` and `v2` sources as valid
2. **Cache Discovery**: Capabilities don't change frequently - cache the discovery response
3. **Timeout Handling**: Set reasonable timeouts (5 seconds) for tool invocations
4. **Error Resilience**: Design consumers to work with fallback data
5. **Monitoring**: Track fallback usage to assess API reliability

## Why This Architecture?

### Enterprise Reliability

- **Always Available**: Never fails due to external dependencies
- **Predictable**: Fallback ensures consistent behavior
- **Observable**: Clear logging of data sources
- **Scalable**: Stateless design allows horizontal scaling

### MCP Protocol Benefits

- **Discoverable**: AI systems can find and use tools automatically
- **Structured**: Machine-readable schemas enable validation
- **Standardized**: Follows MCP protocol for interoperability
- **Tool-Oriented**: Designed for AI agent orchestration

## Summary

This MCP server provides **external situation awareness** for enterprise AI systems. It:

✅ Implements real MCP protocol semantics  
✅ Integrates with real weather APIs  
✅ Always returns valid responses (fallback logic)  
✅ Is stateless and horizontally scalable  
✅ Provides context, not decisions  
✅ Never fails requests  

**Fallback is not an error - it's a feature that ensures enterprise reliability.**
