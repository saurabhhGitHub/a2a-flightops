# Salesforce Team Integration Guide - MCP Weather Context

## Overview

A new **MCP Weather Context** endpoint has been added to provide external weather situation awareness. This document explains what the SF team needs to change and how to integrate it into the existing flow.

---

## 🎯 What Changed?

### New Endpoint Added

**MCP Weather Disruption Context** - Provides weather severity and cascading delay risk for airports.

### Existing Endpoints (No Changes)

These remain the same:
- ✅ `/api/agent/gemini-cost/` - Cost optimization opinion
- ✅ `/api/agent/compliance/` - Regulatory compliance opinion  
- ✅ `/api/agent/ops/` - Operational feasibility opinion

---

## 📍 Endpoints to Use

### Base URL
```
Production: https://a2a-flightops.herokuapp.com
Local Dev: http://localhost:8000
```

### 1. MCP Capability Discovery (One-time setup)

**GET** `/mcp/capabilities`

**Purpose**: Discover available MCP tools (one-time setup, can be cached)

**Response**:
```json
{
  "mcp_version": "1.0",
  "server_name": "airline_disruption_context",
  "tools": [
    {
      "name": "weather_disruption_context",
      "description": "Provides weather severity and cascading delay risk...",
      "input_schema": {...},
      "output_schema": {...}
    }
  ]
}
```

---

### 2. MCP Weather Tool Invocation (Use this in Flow)

**POST** `/mcp/tools/invoke`

**Request Body**:
```json
{
  "tool": "weather_disruption_context",
  "arguments": {
    "airport_code": "DEL"
  }
}
```

**Response**:
```json
{
  "tool": "weather_disruption_context",
  "result": {
    "severity": "MEDIUM",
    "expected_duration_hours": 2.0,
    "cascading_delay_risk": "MEDIUM",
    "source": "v1",
    "raw_weather": {
      "condition": "MIST",
      "description": "mist",
      "wind_speed_ms": 0,
      "visibility_m": 1500
    }
  }
}
```

**Response Fields**:
- `severity`: `"LOW"` | `"MEDIUM"` | `"HIGH"` - Weather severity level
- `expected_duration_hours`: `number` - Expected disruption duration
- `cascading_delay_risk`: `"LOW"` | `"MEDIUM"` | `"HIGH"` - Risk of delays cascading
- `source`: `"v1"` (real weather) | `"v2"` (fallback) - Data source indicator
- `raw_weather`: Additional weather details (only when `source = "v1"`)

---

## 🔄 Updated Flow Integration

### Current Flow (Before)

```
1. Get Flight Record
2. Call Gemini Cost Agent → Cost opinion
3. Call Compliance Agent → Regulatory opinion
4. Call Ops Agent → Feasibility opinion
5. Evaluate all opinions → Make decision
6. Execute workflow
```

### New Flow (After - Add Weather Context)

```
1. Get Flight Record (with Airport_Code__c)
2. Call Gemini Cost Agent → Cost opinion
3. Call Compliance Agent → Regulatory opinion
4. Call Ops Agent → Feasibility opinion
5. ⭐ NEW: Call MCP Weather Tool → Weather context
6. Evaluate all opinions + weather → Make decision
7. Execute workflow
```

---

## 📝 Salesforce Changes Required

### Step 1: Add Airport Code Field (If Not Exists)

**Object**: Flight (or your custom object)

**Field**:
- **API Name**: `Airport_Code__c`
- **Type**: Text (3 characters)
- **Label**: Airport Code
- **Description**: IATA airport code (e.g., DEL, BOM, BLR)

---

### Step 2: Update Named Credential

**Setup → Named Credentials → Django_Agent_Backend**

- **URL**: `https://a2a-flightops.herokuapp.com` (or your deployed URL)
- No other changes needed

---

### Step 3: Add Weather Context Call in Flow

**Location**: In your existing Flow (after Ops Agent call, before decision logic)

**Flow Element**: **Action** → **Call External Service**

**Configuration**:
- **Endpoint**: `/mcp/tools/invoke`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "tool": "weather_disruption_context",
    "arguments": {
      "airport_code": "{!$Record.Airport_Code__c}"
    }
  }
  ```
- **Response Variable**: `weatherResponse`

**Store Response** (Optional - for logging):
- `Weather_Severity__c = {!weatherResponse.result.severity}`
- `Weather_Duration__c = {!weatherResponse.result.expected_duration_hours}`
- `Weather_Cascading_Risk__c = {!weatherResponse.result.cascading_delay_risk}`
- `Weather_Source__c = {!weatherResponse.result.source}`

---

### Step 4: Update Decision Logic

**Location**: Decision element in Flow (after all agent calls)

**Updated Decision Tree**:

```
IF Compliance_Rule = "HOTEL_MANDATORY"
   THEN Final_Decision = "PROVIDE_HOTEL_TO_ALL"
   REASON: Regulatory requirement overrides all

ELSE IF Weather_Severity = "HIGH" 
        AND Weather_Cascading_Risk = "HIGH"
   THEN Final_Decision = "PROVIDE_HOTEL_TO_ALL"
   REASON: Severe weather with high cascading risk

ELSE IF Compliance_Rule = "HOTEL_NOT_REQUIRED"
   THEN Evaluate Cost + Ops + Weather:
   
   IF Hotel_Capacity = "LIMITED" 
      AND Available_Seats < Total_Passengers
      THEN Final_Decision = "PROVIDE_HOTEL_TO_VIP_ONLY"
      
   ELSE IF Cost_Recommendation = "HOTEL_FOR_ALL" 
           AND Cost_Confidence >= 0.8
           AND Hotel_Capacity = "AVAILABLE"
           AND Weather_Severity != "HIGH"
      THEN Final_Decision = "PROVIDE_HOTEL_TO_ALL"
      
   ELSE IF Weather_Severity = "MEDIUM"
           AND Weather_Cascading_Risk = "MEDIUM"
      THEN Final_Decision = "PROVIDE_HOTEL_TO_VIP_ONLY"
      REASON: Moderate weather risk, prioritize VIP
      
   ELSE IF Cost_Recommendation = "LIMIT_HOTEL"
           AND VIP_Passengers > 0
      THEN Final_Decision = "PROVIDE_HOTEL_TO_VIP_ONLY"
      
   ELSE
      THEN Final_Decision = "NO_HOTEL_PROVIDED"
```

---

## 💻 Apex Code Example (If Using Apex)

### Add Weather Context Method

```apex
public class DjangoAgentService {
    private static final String BASE_URL = 'https://a2a-flightops.herokuapp.com';
    
    // Existing methods (Gemini, Compliance, Ops)...
    
    // NEW: Call MCP Weather Tool
    public static WeatherContextResponse callWeatherContext(String airportCode) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint(BASE_URL + '/mcp/tools/invoke');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setBody(JSON.serialize(new Map<String, Object>{
            'tool' => 'weather_disruption_context',
            'arguments' => new Map<String, Object>{
                'airport_code' => airportCode
            }
        }));
        req.setTimeout(10000);
        
        Http http = new Http();
        HttpResponse res = http.send(req);
        
        if (res.getStatusCode() == 200) {
            Map<String, Object> responseMap = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
            Map<String, Object> result = (Map<String, Object>) responseMap.get('result');
            
            WeatherContextResponse response = new WeatherContextResponse();
            response.severity = (String) result.get('severity');
            response.expectedDurationHours = (Decimal) result.get('expected_duration_hours');
            response.cascadingDelayRisk = (String) result.get('cascading_delay_risk');
            response.source = (String) result.get('source');
            
            return response;
        } else {
            throw new CalloutException('Weather API Error: ' + res.getStatusCode());
        }
    }
    
    // Response wrapper class
    public class WeatherContextResponse {
        public String severity;
        public Decimal expectedDurationHours;
        public String cascadingDelayRisk;
        public String source;
    }
}
```

### Updated Decision Logic in Apex

```apex
public static String makeDecision(
    ComplianceResponse compliance,
    GeminiCostResponse cost,
    OpsResponse ops,
    WeatherContextResponse weather
) {
    // Priority 1: Compliance
    if (compliance.rule == 'HOTEL_MANDATORY') {
        return 'PROVIDE_HOTEL_TO_ALL';
    }
    
    // Priority 2: Weather (NEW)
    if (weather.severity == 'HIGH' && weather.cascadingDelayRisk == 'HIGH') {
        return 'PROVIDE_HOTEL_TO_ALL';
    }
    
    // Priority 3: Ops + Cost + Weather
    if (ops.hotelCapacity == 'LIMITED' && ops.availableSeats < totalPassengers) {
        return 'PROVIDE_HOTEL_TO_VIP_ONLY';
    }
    
    if (cost.recommendation == 'HOTEL_FOR_ALL' 
        && cost.confidence >= 0.8 
        && ops.hotelCapacity == 'AVAILABLE'
        && weather.severity != 'HIGH') {
        return 'PROVIDE_HOTEL_TO_ALL';
    }
    
    if (weather.severity == 'MEDIUM' && weather.cascadingDelayRisk == 'MEDIUM') {
        return 'PROVIDE_HOTEL_TO_VIP_ONLY';
    }
    
    // ... rest of logic
}
```

---

## 🎯 Decision Priority Order (Updated)

1. **Compliance Agent** (Highest - Regulatory)
2. **Weather Context** (NEW - External situation awareness)
3. **Ops Agent** (Feasibility constraints)
4. **Gemini Cost Agent** (Cost optimization)

---

## 📊 Example Scenario with Weather

### Scenario: Delhi Airport with Severe Weather

**Input**:
- Airport: DEL
- Delay: 1.5 hours
- Total Passengers: 180
- VIP Passengers: 18

**API Responses**:
- Compliance: `HOTEL_NOT_REQUIRED` (delay < 2h)
- Cost: `LIMIT_HOTEL` (confidence: 0.85)
- Ops: `available_seats: 42`, `hotel_capacity: "LIMITED"`
- **Weather**: `severity: "HIGH"`, `cascading_risk: "HIGH"`, `expected_duration: 4.0h`

**Decision**: `PROVIDE_HOTEL_TO_ALL`
**Reason**: Severe weather with high cascading risk overrides cost optimization

---

## ⚠️ Important Notes

### 1. Weather is Context, Not Decision
- Weather provides **situation awareness**
- Agentforce still makes the **final decision**
- Weather informs but doesn't replace compliance/cost/ops logic

### 2. Source Field (`v1` vs `v2`)
- `"source": "v1"` = Real weather data from API
- `"source": "v2"` = Fallback logic (API unavailable)
- **Both are valid** - treat them the same way
- Don't fail if `source = "v2"`

### 3. Error Handling
- If weather API fails, it returns `v2` (fallback)
- Flow should continue normally
- Weather is **optional context**, not mandatory

### 4. Performance
- Weather API call takes ~1-2 seconds
- Can be called in parallel with other agents
- Consider caching if same airport queried multiple times

---

## 🧪 Testing

### Test Weather Endpoint

```bash
# Test with Delhi
curl -X POST https://a2a-flightops.herokuapp.com/mcp/tools/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "weather_disruption_context",
    "arguments": {
      "airport_code": "DEL"
    }
  }'

# Test with Mumbai
curl -X POST https://a2a-flightops.herokuapp.com/mcp/tools/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "weather_disruption_context",
    "arguments": {
      "airport_code": "BOM"
    }
  }'
```

---

## 📋 Checklist for SF Team

- [ ] Add `Airport_Code__c` field to Flight object (if not exists)
- [ ] Update Named Credential URL (if needed)
- [ ] Add MCP Weather call in Flow (after Ops, before decision)
- [ ] Update Decision logic to include weather context
- [ ] Add weather fields to Flight object (optional, for logging)
- [ ] Test with different airports (DEL, BOM, BLR, MAA)
- [ ] Test error handling (what if weather API fails)
- [ ] Update documentation/runbooks

---

## 🔗 Quick Reference

### Endpoints Summary

| Endpoint | Method | Purpose | When to Call |
|----------|--------|---------|--------------|
| `/api/agent/gemini-cost/` | POST | Cost opinion | Always |
| `/api/agent/compliance/` | POST | Regulatory opinion | Always |
| `/api/agent/ops/` | POST | Feasibility opinion | Always |
| `/mcp/tools/invoke` | POST | Weather context | **NEW - Always** |

### Request Format

```json
{
  "tool": "weather_disruption_context",
  "arguments": {
    "airport_code": "DEL"
  }
}
```

### Response Format

```json
{
  "tool": "weather_disruption_context",
  "result": {
    "severity": "MEDIUM",
    "expected_duration_hours": 2.0,
    "cascading_delay_risk": "MEDIUM",
    "source": "v1"
  }
}
```

---

## ❓ Questions?

- **Q: What if airport code is missing?**
  - A: Weather call will fail gracefully, use `v2` fallback, flow continues

- **Q: Should we call weather for every flight?**
  - A: Yes, it's fast and provides valuable context

- **Q: Can we cache weather data?**
  - A: Yes, but weather changes frequently. Cache for 15-30 minutes max.

- **Q: What airports are supported?**
  - A: All IATA 3-letter codes. Common ones: DEL, BOM, BLR, MAA, CCU, HYD, COK, GOI

---

## Summary

**What Changed**: Added MCP Weather Context endpoint  
**What SF Team Needs**: Add weather call in Flow, update decision logic  
**Impact**: Weather context now informs decisions (doesn't replace existing logic)  
**Timeline**: Can be added incrementally, existing flow continues to work

**Key Point**: Weather is **additional context**, not a replacement for existing agents.
