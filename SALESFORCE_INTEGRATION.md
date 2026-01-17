# Salesforce Integration Guide

This document explains how Salesforce Agentforce consumes the Django backend APIs and how to connect the full stack.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    SALESFORCE (System of Record)            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Agentforce / Flow / Apex                             │  │
│  │  - Flight Records                                      │  │
│  │  - Passenger Data                                      │  │
│  │  - Decision Logic                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          │ HTTP POST (Callouts)              │
│                          ▼                                   │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ REST API Calls
                          │
┌─────────────────────────────────────────────────────────────┐
│              DJANGO BACKEND (Stateless Agents)              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  /api/agent/gemini-cost/                             │  │
│  │  /api/agent/compliance/                              │  │
│  │  /api/agent/ops/                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          │ Returns JSON Opinions            │
│                          ▼                                   │
└─────────────────────────────────────────────────────────────┘
```

## Integration Methods

### Method 1: Salesforce Flow (Recommended for Agentforce)

Salesforce Flow can make HTTP callouts directly to your Django backend.

#### Step 1: Create Named Credential

1. **Setup → Named Credentials → New**
   - **Label**: `Django_Agent_Backend`
   - **Name**: `Django_Agent_Backend`
   - **URL**: `http://your-django-server:8000` (or your deployed URL)
   - **Identity Type**: Named Principal
   - **Authentication Protocol**: No Authentication (for demo)
   - **Save**

#### Step 2: Create Flow for Gemini Cost Agent

**Flow Type**: Record-Triggered Flow or Screen Flow

**Elements**:
1. **Get Records** - Get Flight record with delay_hours, total_passengers, vip_passengers
2. **Action** - Call External Service
   - **External Service**: Create new External Service
   - **Endpoint**: `/api/agent/gemini-cost/`
   - **Method**: POST
   - **Request Body**:
     ```json
     {
       "delay_hours": {!$Record.Delay_Hours__c},
       "total_passengers": {!$Record.Total_Passengers__c},
       "vip_passengers": {!$Record.VIP_Passengers__c}
     }
     ```
   - **Response Variable**: `geminiResponse`
3. **Assignment** - Store response
   - `Cost_Recommendation__c = {!geminiResponse.recommendation}`
   - `Cost_Reason__c = {!geminiResponse.reason}`
   - `Cost_Confidence__c = {!geminiResponse.confidence}`

---

### Method 2: Apex HTTP Callout (For Complex Logic)

Create Apex classes to call the Django APIs.

#### Step 1: Create Apex Class for API Integration

```apex
public class DjangoAgentService {
    private static final String BASE_URL = 'http://your-django-server:8000';
    
    // Call Gemini Cost Agent
    public static GeminiCostResponse callGeminiCostAgent(
        Decimal delayHours, 
        Integer totalPassengers, 
        Integer vipPassengers
    ) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint(BASE_URL + '/api/agent/gemini-cost/');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setBody(JSON.serialize(new Map<String, Object>{
            'delay_hours' => delayHours,
            'total_passengers' => totalPassengers,
            'vip_passengers' => vipPassengers
        }));
        req.setTimeout(30000);
        
        Http http = new Http();
        HttpResponse res = http.send(req);
        
        if (res.getStatusCode() == 200) {
            return (GeminiCostResponse) JSON.deserialize(
                res.getBody(), 
                GeminiCostResponse.class
            );
        } else {
            throw new CalloutException('API Error: ' + res.getStatusCode());
        }
    }
    
    // Call Compliance Agent
    public static ComplianceResponse callComplianceAgent(Decimal delayHours) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint(BASE_URL + '/api/agent/compliance/');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setBody(JSON.serialize(new Map<String, Object>{
            'delay_hours' => delayHours
        }));
        req.setTimeout(30000);
        
        Http http = new Http();
        HttpResponse res = http.send(req);
        
        if (res.getStatusCode() == 200) {
            return (ComplianceResponse) JSON.deserialize(
                res.getBody(), 
                ComplianceResponse.class
            );
        } else {
            throw new CalloutException('API Error: ' + res.getStatusCode());
        }
    }
    
    // Call Ops Agent
    public static OpsResponse callOpsAgent() {
        HttpRequest req = new HttpRequest();
        req.setEndpoint(BASE_URL + '/api/agent/ops/');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setBody('{}');
        req.setTimeout(30000);
        
        Http http = new Http();
        HttpResponse res = http.send(req);
        
        if (res.getStatusCode() == 200) {
            return (OpsResponse) JSON.deserialize(
                res.getBody(), 
                OpsResponse.class
            );
        } else {
            throw new CalloutException('API Error: ' + res.getStatusCode());
        }
    }
    
    // Response Wrapper Classes
    public class GeminiCostResponse {
        public String agent;
        public String recommendation;
        public String reason;
        public Decimal confidence;
    }
    
    public class ComplianceResponse {
        public String agent;
        public String rule;
        public String reason;
        public Decimal confidence;
    }
    
    public class OpsResponse {
        public String agent;
        public Integer available_seats;
        public String hotel_capacity;
    }
}
```

#### Step 2: Create Remote Site Settings

**Setup → Remote Site Settings → New**

- **Remote Site Name**: `Django_Backend`
- **Remote Site URL**: `http://your-django-server:8000`
- **Active**: ✅
- **Save**

#### Step 3: Use in Apex Trigger or Flow

```apex
// Example: In a Flight trigger or Flow
public class FlightHandler {
    public static void evaluateDisruption(Flight__c flight) {
        // Call all three agents
        DjangoAgentService.GeminiCostResponse costResponse = 
            DjangoAgentService.callGeminiCostAgent(
                flight.Delay_Hours__c,
                flight.Total_Passengers__c,
                flight.VIP_Passengers__c
            );
        
        DjangoAgentService.ComplianceResponse complianceResponse = 
            DjangoAgentService.callComplianceAgent(flight.Delay_Hours__c);
        
        DjangoAgentService.OpsResponse opsResponse = 
            DjangoAgentService.callOpsAgent();
        
        // Store opinions in Flight record
        flight.Cost_Recommendation__c = costResponse.recommendation;
        flight.Cost_Reason__c = costResponse.reason;
        flight.Cost_Confidence__c = costResponse.confidence;
        
        flight.Compliance_Rule__c = complianceResponse.rule;
        flight.Compliance_Reason__c = complianceResponse.reason;
        
        flight.Available_Seats__c = opsResponse.available_seats;
        flight.Hotel_Capacity__c = opsResponse.hotel_capacity;
        
        // Salesforce makes the final decision based on all opinions
        // ... your decision logic here ...
    }
}
```

---

### Method 3: Salesforce Agentforce Integration

If using Salesforce Agentforce (AI-powered decision making):

1. **Create Custom Actions** in Agentforce that call the Django APIs
2. **Agentforce Flow**:
   - Trigger: Flight delay detected
   - Actions:
     - Call Gemini Cost Agent → Get cost opinion
     - Call Compliance Agent → Get compliance opinion
     - Call Ops Agent → Get feasibility opinion
   - Decision: Agentforce evaluates all opinions and makes final decision
   - Execution: Execute workflow based on decision

---

## Complete Integration Example

### Salesforce Object Structure

**Flight__c Object** (Custom Object):
- `Delay_Hours__c` (Number)
- `Total_Passengers__c` (Number)
- `VIP_Passengers__c` (Number)
- `Cost_Recommendation__c` (Text) - from Gemini
- `Cost_Reason__c` (Long Text) - from Gemini
- `Cost_Confidence__c` (Number) - from Gemini
- `Compliance_Rule__c` (Text) - from Compliance Agent
- `Available_Seats__c` (Number) - from Ops Agent
- `Hotel_Capacity__c` (Text) - from Ops Agent
- `Final_Decision__c` (Text) - Salesforce decision

### Flow Example (Complete)

```
┌─────────────────────────────────────────────────┐
│  Flow: Evaluate Flight Disruption              │
├─────────────────────────────────────────────────┤
│  1. Get Flight Record                           │
│     - Delay_Hours__c                            │
│     - Total_Passengers__c                       │
│     - VIP_Passengers__c                         │
│                                                  │
│  2. Call Gemini Cost Agent                      │
│     POST /api/agent/gemini-cost/                │
│     → Store: Cost_Recommendation__c             │
│                                                  │
│  3. Call Compliance Agent                       │
│     POST /api/agent/compliance/                 │
│     → Store: Compliance_Rule__c                 │
│                                                  │
│  4. Call Ops Agent                              │
│     POST /api/agent/ops/                        │
│     → Store: Available_Seats__c                │
│                                                  │
│  5. Decision Element                            │
│     IF Compliance_Rule__c = "HOTEL_MANDATORY"   │
│     THEN Final_Decision__c = "PROVIDE_HOTEL"    │
│     ELSE Evaluate Cost + Ops opinions           │
│                                                  │
│  6. Update Flight Record                        │
│     - Store all opinions                        │
│     - Store final decision                      │
│                                                  │
│  7. Execute Actions                             │
│     - Send notifications                        │
│     - Create tasks                              │
│     - Update related records                    │
└─────────────────────────────────────────────────┘
```

---

## Deployment Considerations

### 1. Environment URLs

**Development:**
- Django: `http://localhost:8000`
- Salesforce: Use Remote Site Settings for localhost

**Production:**
- Django: `https://your-domain.com` or deployed URL
- Salesforce: Update Remote Site Settings and Named Credentials

### 2. Security (Production)

**For Production, add authentication:**

1. **Django Side** (Optional for demo, required for production):
   ```python
   # In settings.py
   REST_FRAMEWORK = {
       'DEFAULT_AUTHENTICATION_CLASSES': [
           'rest_framework.authentication.TokenAuthentication',
       ],
   }
   ```

2. **Salesforce Side**:
   - Use Named Credentials with OAuth or API Key
   - Store credentials securely

### 3. Error Handling

**In Salesforce Flow/Apex:**
- Handle timeout errors (30 seconds default)
- Handle HTTP errors (400, 500, etc.)
- Fallback to default values if API fails
- Log errors for debugging

---

## Testing the Integration

### Test from Salesforce Developer Console

```apex
// Execute Anonymous Apex
DjangoAgentService.GeminiCostResponse response = 
    DjangoAgentService.callGeminiCostAgent(3, 180, 18);
System.debug('Recommendation: ' + response.recommendation);
System.debug('Reason: ' + response.reason);
System.debug('Confidence: ' + response.confidence);
```

### Test from Postman/curl (Same as Django)

```bash
# Test from external tool (same as Django curl commands)
curl -X POST http://your-django-server:8000/api/agent/gemini-cost/ \
  -H "Content-Type: application/json" \
  -d '{"delay_hours": 3, "total_passengers": 180, "vip_passengers": 18}'
```

---

## Best Practices

1. **Stateless Design**: ✅ Django backend is stateless - perfect for Salesforce
2. **Error Handling**: Always handle API failures gracefully
3. **Timeout Settings**: Set appropriate timeouts (30 seconds recommended)
4. **Logging**: Use AgentCallLog in Django for observability
5. **Caching**: Consider caching responses in Salesforce if appropriate
6. **Rate Limiting**: Implement rate limiting if needed
7. **Monitoring**: Monitor API calls and response times

---

## Quick Start Checklist

- [ ] Deploy Django backend (local or cloud)
- [ ] Create Remote Site Settings in Salesforce
- [ ] Create Named Credentials (optional, for Flow)
- [ ] Create Apex classes for API calls (or use Flow)
- [ ] Create Custom Fields on Flight object
- [ ] Create Flow or Trigger to call APIs
- [ ] Test with sample Flight record
- [ ] Verify responses are stored correctly
- [ ] Implement decision logic in Salesforce
- [ ] Test end-to-end workflow

---

## Support

For issues:
1. Check Django server logs
2. Check AgentCallLog in Django admin
3. Check Salesforce Debug Logs
4. Verify Remote Site Settings
5. Test APIs directly with curl first
