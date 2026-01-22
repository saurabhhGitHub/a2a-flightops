# Agentforce Decision-Making Logic

This document explains how Salesforce Agentforce evaluates all agent opinions and makes final decisions.

## Overview

**Key Principle**: Salesforce Agentforce is the **decision owner**. Django agents only provide **opinions**. Agentforce evaluates all opinions and makes the final decision.

---

## Decision-Making Flow

```
┌─────────────────────────────────────────────────────────┐
│  STEP 1: Collect All Agent Opinions                    │
├─────────────────────────────────────────────────────────┤
│  Call APIs in parallel:                                 │
│  1. Gemini Cost Agent → Cost opinion                    │
│  2. Compliance Agent → Regulatory opinion               │
│  3. Ops Agent → Feasibility opinion                    │
│  4. Weather Agent (OPTIONAL) → External context        │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 2: Evaluate Opinions (Decision Tree)             │
├─────────────────────────────────────────────────────────┤
│  Apply decision logic based on priority                 │
│  (Weather is optional - flow works without it)         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 3: Make Final Decision                           │
├─────────────────────────────────────────────────────────┤
│  Store decision and execute workflow                    │
└─────────────────────────────────────────────────────────┘
```

**Note**: Weather context is **optional**. The flow works perfectly with only Cost, Compliance, and Ops agents. Weather provides additional external situation awareness for more informed decisions.

---

## Decision Formula / Logic

### Priority Order (Most Important First)

1. **Compliance Agent** (Highest Priority - Regulatory)
2. **Weather Agent** (OPTIONAL - External Situation Awareness)
3. **Ops Agent** (Feasibility Constraints)
4. **Gemini Cost Agent** (Cost Optimization)

**Note**: Weather is optional. If weather context is unavailable, skip Priority 2 and continue with Priority 3 (Ops).

### Decision Tree

```
IF Compliance_Rule = "HOTEL_MANDATORY"
   THEN Final_Decision = "PROVIDE_HOTEL_TO_ALL"
   REASON: Regulatory requirement overrides all other considerations
   
ELSE IF Weather_Severity = "HIGH" 
        AND Weather_Cascading_Risk = "HIGH"
        AND Weather_Available = TRUE
   THEN Final_Decision = "PROVIDE_HOTEL_TO_ALL"
   REASON: Severe weather with high cascading risk (external context)
   
ELSE IF Compliance_Rule = "HOTEL_NOT_REQUIRED"
   THEN Evaluate Cost + Ops + Weather (if available):
   
   IF Hotel_Capacity = "LIMITED" AND Available_Seats < Total_Passengers
      THEN Final_Decision = "PROVIDE_HOTEL_TO_VIP_ONLY"
      REASON: Limited capacity, prioritize VIP passengers
      
   ELSE IF Cost_Recommendation = "HOTEL_FOR_ALL" 
           AND Cost_Confidence >= 0.8
           AND Hotel_Capacity = "AVAILABLE"
           AND (Weather_Not_Available OR Weather_Severity != "HIGH")
      THEN Final_Decision = "PROVIDE_HOTEL_TO_ALL"
      REASON: High confidence cost recommendation + capacity available
      
   ELSE IF Weather_Severity = "MEDIUM"
           AND Weather_Cascading_Risk = "MEDIUM"
           AND Weather_Available = TRUE
      THEN Final_Decision = "PROVIDE_HOTEL_TO_VIP_ONLY"
      REASON: Moderate weather risk, prioritize VIP passengers
      
   ELSE IF Cost_Recommendation = "LIMIT_HOTEL"
           AND VIP_Passengers > 0
      THEN Final_Decision = "PROVIDE_HOTEL_TO_VIP_ONLY"
      REASON: Cost optimization suggests limiting, but VIP service required
      
   ELSE
      THEN Final_Decision = "NO_HOTEL_PROVIDED"
      REASON: No regulatory requirement, cost optimization suggests no hotel
```

**Important**: 
- Weather checks are **optional**. If `Weather_Available = FALSE`, skip weather conditions and continue with original logic.
- Flow works perfectly without weather context.
- Weather enhances decisions but is not required for correct answers.

---

## Detailed Decision Matrix

### Scenario 1: Compliance Mandatory
**Input:**
- Compliance: `HOTEL_MANDATORY`
- Cost: Any
- Ops: Any

**Decision:** `PROVIDE_HOTEL_TO_ALL`
**Reason:** Regulatory compliance is mandatory

---

### Scenario 2: No Compliance Requirement + Limited Capacity
**Input:**
- Compliance: `HOTEL_NOT_REQUIRED`
- Ops: `hotel_capacity = "LIMITED"`, `available_seats < total_passengers`
- Cost: Any

**Decision:** `PROVIDE_HOTEL_TO_VIP_ONLY`
**Reason:** Limited resources, prioritize VIP passengers

---

### Scenario 3: High Confidence Cost Recommendation
**Input:**
- Compliance: `HOTEL_NOT_REQUIRED`
- Cost: `HOTEL_FOR_ALL` with `confidence >= 0.8`
- Ops: `hotel_capacity = "AVAILABLE"`

**Decision:** `PROVIDE_HOTEL_TO_ALL`
**Reason:** Strong cost justification + capacity available

---

### Scenario 4: Cost Optimization + VIP Passengers
**Input:**
- Compliance: `HOTEL_NOT_REQUIRED`
- Cost: `LIMIT_HOTEL`
- Ops: Any
- VIP Passengers: > 0

**Decision:** `PROVIDE_HOTEL_TO_VIP_ONLY`
**Reason:** Cost optimization suggests limiting, but VIP service standards require accommodation

---

### Scenario 5: No Strong Recommendation
**Input:**
- Compliance: `HOTEL_NOT_REQUIRED`
- Cost: `LIMIT_HOTEL` with low confidence
- Ops: Any
- VIP Passengers: 0

**Decision:** `NO_HOTEL_PROVIDED`
**Reason:** No regulatory requirement, no strong cost justification, no VIP passengers

---

## Confidence Scoring (Optional Enhancement)

If you want to add weighted scoring:

```
Total_Score = 0

IF Compliance_Rule = "HOTEL_MANDATORY"
   Total_Score += 100  (Compliance is mandatory)

IF Cost_Recommendation = "HOTEL_FOR_ALL"
   Total_Score += (Cost_Confidence * 30)  (Cost weight: 30%)

IF Hotel_Capacity = "AVAILABLE"
   Total_Score += 20  (Feasibility bonus)

IF VIP_Passengers > 0
   Total_Score += 10  (VIP service requirement)

Decision Thresholds:
- Total_Score >= 100 → PROVIDE_HOTEL_TO_ALL
- Total_Score >= 50 → PROVIDE_HOTEL_TO_VIP_ONLY
- Total_Score < 50 → NO_HOTEL_PROVIDED
```

---

## Example Decision Scenarios

### Example 1: Long Delay (Regulatory)
**Input:**
- Delay: 3 hours
- Total Passengers: 180
- VIP Passengers: 18

**API Responses:**
- Compliance: `HOTEL_MANDATORY` (delay >= 2 hours)
- Cost: `LIMIT_HOTEL` (confidence: 0.85)
- Ops: `available_seats: 42`, `hotel_capacity: "LIMITED"`

**Decision:** `PROVIDE_HOTEL_TO_ALL`
**Reason:** Compliance mandates hotel, overrides cost optimization

---

### Example 2: Short Delay + High Cost Confidence
**Input:**
- Delay: 1 hour
- Total Passengers: 50
- VIP Passengers: 5

**API Responses:**
- Compliance: `HOTEL_NOT_REQUIRED` (delay < 2 hours)
- Cost: `HOTEL_FOR_ALL` (confidence: 0.92, reason: "Small passenger count")
- Ops: `available_seats: 100`, `hotel_capacity: "AVAILABLE"`

**Decision:** `PROVIDE_HOTEL_TO_ALL`
**Reason:** High confidence cost recommendation + capacity available

---

### Example 3: Short Delay + Cost Optimization
**Input:**
- Delay: 1.5 hours
- Total Passengers: 200
- VIP Passengers: 20
- Airport: DEL

**API Responses:**
- Compliance: `HOTEL_NOT_REQUIRED`
- Cost: `LIMIT_HOTEL` (confidence: 0.88)
- Ops: `available_seats: 30`, `hotel_capacity: "LIMITED"`
- Weather: Not available (optional)

**Decision:** `PROVIDE_HOTEL_TO_VIP_ONLY`
**Reason:** Cost optimization + limited capacity + VIP passengers present

---

### Example 4: Short Delay + Severe Weather (With Weather Context)
**Input:**
- Delay: 1.5 hours
- Total Passengers: 180
- VIP Passengers: 18
- Airport: DEL

**API Responses:**
- Compliance: `HOTEL_NOT_REQUIRED` (delay < 2 hours)
- Cost: `LIMIT_HOTEL` (confidence: 0.85)
- Ops: `available_seats: 42`, `hotel_capacity: "LIMITED"`
- Weather: `severity: "HIGH"`, `cascading_risk: "HIGH"`, `expected_duration: 4.0h`

**Decision:** `PROVIDE_HOTEL_TO_ALL`
**Reason:** Severe weather with high cascading risk overrides cost optimization

**Note**: Without weather context, this would have been `PROVIDE_HOTEL_TO_VIP_ONLY`. Weather provides additional external awareness.

---

### Example 5: Moderate Weather (With Weather Context)
**Input:**
- Delay: 1 hour
- Total Passengers: 150
- VIP Passengers: 15
- Airport: BOM

**API Responses:**
- Compliance: `HOTEL_NOT_REQUIRED`
- Cost: `LIMIT_HOTEL` (confidence: 0.75)
- Ops: `available_seats: 50`, `hotel_capacity: "AVAILABLE"`
- Weather: `severity: "MEDIUM"`, `cascading_risk: "MEDIUM"`

**Decision:** `PROVIDE_HOTEL_TO_VIP_ONLY`
**Reason:** Moderate weather risk, prioritize VIP passengers despite available capacity

---

## Key Decision Principles

1. **Compliance First**: Regulatory requirements always override cost/ops/weather
2. **Weather Context** (Optional): External situation awareness informs decisions when available
3. **Feasibility Check**: Can't provide what's not available
4. **Cost Optimization**: Considered when compliance allows flexibility
5. **VIP Service Standards**: VIP passengers get priority when resources are limited
6. **Confidence Matters**: Higher confidence opinions carry more weight
7. **Graceful Degradation**: Flow works correctly even if weather context is unavailable

---

## Decision Output Format

After evaluation, Agentforce stores:

```
Final_Decision__c = "PROVIDE_HOTEL_TO_ALL" | "PROVIDE_HOTEL_TO_VIP_ONLY" | "NO_HOTEL_PROVIDED"
Decision_Reason__c = "Compliance mandates hotel accommodation"
Decision_Confidence__c = 1.0
Decision_Timestamp__c = 2026-01-17T12:00:00Z
```

---

## Workflow Execution Based on Decision

### If Decision = "PROVIDE_HOTEL_TO_ALL"
1. Create Hotel Booking records for all passengers
2. Send notification to Operations team
3. Update Flight status to "Hotel Accommodation Provided"
4. Create tasks for hotel coordination
5. Send SMS/Email to all passengers

### If Decision = "PROVIDE_HOTEL_TO_VIP_ONLY"
1. Create Hotel Booking records for VIP passengers only
2. Send notification to VIP Services team
3. Update Flight status to "VIP Hotel Accommodation"
4. Create tasks for VIP hotel coordination
5. Send SMS/Email to VIP passengers only
6. Send general delay notification to other passengers

### If Decision = "NO_HOTEL_PROVIDED"
1. Update Flight status to "Delay - No Accommodation"
2. Send delay notification to all passengers
3. Provide meal vouchers if delay > 1 hour
4. Monitor for delay extension (may trigger re-evaluation)

---

## Re-evaluation Triggers

Agentforce should re-evaluate if:
- Delay hours increase (may cross compliance threshold)
- New information received (e.g., hotel capacity changes)
- Manual override requested
- Time-based re-check (every 30 minutes for long delays)

---

## Weather Context Integration (Optional Enhancement)

### Weather Agent Details

**Endpoint**: `POST /mcp/tools/invoke`

**Request**:
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
    "source": "v1"
  }
}
```

### Weather Integration Notes

1. **Optional**: Weather context is optional. Flow works perfectly without it.
2. **Graceful Degradation**: If weather call fails or is skipped, continue with original logic (Compliance + Cost + Ops).
3. **Enhancement, Not Requirement**: Weather provides external situation awareness but is not required for correct decisions.
4. **Source Field**: 
   - `"source": "v1"` = weather data from API
   - `"source": "v2"` = Fallback logic (API unavailable)
   - Both are valid - treat them the same way

### When to Use Weather

- **Recommended**: Production environments, when airport code is available
- **Optional**: Development/testing, when weather API is down, when you want faster decisions

### Implementation Pattern

```apex
// Try to get weather context (optional)
WeatherContextResponse weather = null;
try {
    weather = DjangoAgentService.callWeatherContext(airportCode);
} catch (Exception e) {
    // Weather unavailable - continue without it
    System.debug('Weather context unavailable: ' + e.getMessage());
}

// Use weather if available, otherwise use original logic
String decision = makeDecision(compliance, cost, ops, weather);
```

---

## Summary

**Decision Formula (Without Weather)**:
```
IF Compliance = MANDATORY → PROVIDE_HOTEL_TO_ALL
ELSE IF Capacity Limited → PROVIDE_HOTEL_TO_VIP_ONLY
ELSE IF Cost High Confidence + Capacity Available → PROVIDE_HOTEL_TO_ALL
ELSE IF Cost Limit + VIP Present → PROVIDE_HOTEL_TO_VIP_ONLY
ELSE → NO_HOTEL_PROVIDED
```

**Decision Formula (With Weather - Enhanced)**:
```
IF Compliance = MANDATORY → PROVIDE_HOTEL_TO_ALL
ELSE IF Weather = HIGH + Cascading Risk HIGH → PROVIDE_HOTEL_TO_ALL
ELSE IF Capacity Limited → PROVIDE_HOTEL_TO_VIP_ONLY
ELSE IF Cost High Confidence + Capacity Available + Weather != HIGH → PROVIDE_HOTEL_TO_ALL
ELSE IF Weather = MEDIUM → PROVIDE_HOTEL_TO_VIP_ONLY
ELSE IF Cost Limit + VIP Present → PROVIDE_HOTEL_TO_VIP_ONLY
ELSE → NO_HOTEL_PROVIDED
```

**Key Points**: 
- Agentforce makes the decision. Django agents only provide opinions. The decision logic lives in Salesforce, not in Django.
- Weather context is **optional**. Flow works correctly with or without it.
- Weather enhances decision quality but is not required for correct answers.
