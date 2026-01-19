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
│  Call all three APIs in parallel:                       │
│  1. Gemini Cost Agent → Cost opinion                    │
│  2. Compliance Agent → Regulatory opinion               │
│  3. Ops Agent → Feasibility opinion                    │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 2: Evaluate Opinions (Decision Tree)             │
├─────────────────────────────────────────────────────────┤
│  Apply decision logic based on priority                 │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 3: Make Final Decision                           │
├─────────────────────────────────────────────────────────┤
│  Store decision and execute workflow                    │
└─────────────────────────────────────────────────────────┘
```

---

## Decision Formula / Logic

### Priority Order (Most Important First)

1. **Compliance Agent** (Highest Priority - Regulatory)
2. **Ops Agent** (Feasibility Constraints)
3. **Gemini Cost Agent** (Cost Optimization)

### Decision Tree

```
IF Compliance_Rule = "HOTEL_MANDATORY"
   THEN Final_Decision = "PROVIDE_HOTEL_TO_ALL"
   REASON: Regulatory requirement overrides all other considerations
   
ELSE IF Compliance_Rule = "HOTEL_NOT_REQUIRED"
   THEN Evaluate Cost + Ops:
   
   IF Hotel_Capacity = "LIMITED" AND Available_Seats < Total_Passengers
      THEN Final_Decision = "PROVIDE_HOTEL_TO_VIP_ONLY"
      REASON: Limited capacity, prioritize VIP passengers
      
   ELSE IF Cost_Recommendation = "HOTEL_FOR_ALL" 
           AND Cost_Confidence >= 0.8
           AND Hotel_Capacity = "AVAILABLE"
      THEN Final_Decision = "PROVIDE_HOTEL_TO_ALL"
      REASON: High confidence cost recommendation + capacity available
      
   ELSE IF Cost_Recommendation = "LIMIT_HOTEL"
           AND VIP_Passengers > 0
      THEN Final_Decision = "PROVIDE_HOTEL_TO_VIP_ONLY"
      REASON: Cost optimization suggests limiting, but VIP service required
      
   ELSE
      THEN Final_Decision = "NO_HOTEL_PROVIDED"
      REASON: No regulatory requirement, cost optimization suggests no hotel
```

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

**API Responses:**
- Compliance: `HOTEL_NOT_REQUIRED`
- Cost: `LIMIT_HOTEL` (confidence: 0.88)
- Ops: `available_seats: 30`, `hotel_capacity: "LIMITED"`

**Decision:** `PROVIDE_HOTEL_TO_VIP_ONLY`
**Reason:** Cost optimization + limited capacity + VIP passengers present

---

## Key Decision Principles

1. **Compliance First**: Regulatory requirements always override cost/ops
2. **Feasibility Check**: Can't provide what's not available
3. **Cost Optimization**: Considered when compliance allows flexibility
4. **VIP Service Standards**: VIP passengers get priority when resources are limited
5. **Confidence Matters**: Higher confidence opinions carry more weight

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

## Summary

**Decision Formula:**
```
IF Compliance = MANDATORY → PROVIDE_HOTEL_TO_ALL
ELSE IF Capacity Limited → PROVIDE_HOTEL_TO_VIP_ONLY
ELSE IF Cost High Confidence + Capacity Available → PROVIDE_HOTEL_TO_ALL
ELSE IF Cost Limit + VIP Present → PROVIDE_HOTEL_TO_VIP_ONLY
ELSE → NO_HOTEL_PROVIDED
```

**Key Point**: Agentforce makes the decision. Django agents only provide opinions. The decision logic lives in Salesforce, not in Django.
