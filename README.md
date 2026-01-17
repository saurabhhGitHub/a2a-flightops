# Airline Disruption Control - Backend Service

Django-based backend service for Airline Disruption Control demo. This service provides agent APIs that Salesforce Agentforce can call to get recommendations and opinions.

## Tech Stack

- **Backend**: Django 4.2.7 + Django REST Framework
- **Database**: PostgreSQL
- **AI**: Google Gemini API (for cost optimization agent)
- **Auth**: None (demo only)

## Architecture

### System Boundaries

**CRITICAL: This backend is STATELESS with respect to business data.**

- **Salesforce is the SYSTEM OF RECORD**
  - Owns all Flight data
  - Owns all Passenger data
  - Owns delay status
  - Makes all final decisions
  - Executes all workflows

- **This Django backend is ONLY an external agent layer**
  - Provides "opinions" via HTTP callouts
  - Does NOT own business data
  - Does NOT make decisions
  - Does NOT execute actions
  - Is fully stateless (request → response)

### Agent Behavior

- Agents do NOT talk to each other
- Agents do NOT execute actions
- Agents only return structured JSON responses
- Agents are "disposable reasoning engines"

**Mental Model**: "Salesforce decides. Django thinks."

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- PostgreSQL (with pgAdmin)
- Google Gemini API key (optional, has fallback)

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 3. Database Setup

Create a PostgreSQL database:

```sql
CREATE DATABASE flight_ops;
```

### 4. Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```
SECRET_KEY=your-secret-key-here
DEBUG=True

DB_NAME=flight_ops
DB_USER=postgres
DB_PASSWORD=1234
DB_HOST=localhost
DB_PORT=5432

GEMINI_API_KEY=your-gemini-api-key-here
```

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser (Optional, for admin)

```bash
python manage.py createsuperuser
```

### 7. Run Server

```bash
python manage.py runserver
```

Server will run on `http://localhost:8000`

## API Endpoints

### 1. Gemini Cost Optimization Agent

**Endpoint**: `POST /api/agent/gemini-cost/`

**Request**:
```json
{
  "delay_hours": 3,
  "total_passengers": 180,
  "vip_passengers": 18
}
```

**Response**:
```json
{
  "agent": "Gemini-Cost-Agent",
  "recommendation": "LIMIT_HOTEL",
  "reason": "Hotel for all passengers is expensive for this delay duration",
  "confidence": 0.88
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/agent/gemini-cost/ \
  -H "Content-Type: application/json" \
  -d '{
    "delay_hours": 3,
    "total_passengers": 180,
    "vip_passengers": 18
  }'
```

---

### 2. Compliance Agent

**Endpoint**: `POST /api/agent/compliance/`

**Request**:
```json
{
  "delay_hours": 3
}
```

**Response**:
```json
{
  "agent": "Compliance-Agent",
  "rule": "HOTEL_MANDATORY",
  "reason": "Delay exceeds regulatory threshold",
  "confidence": 1.0
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/agent/compliance/ \
  -H "Content-Type: application/json" \
  -d '{
    "delay_hours": 3
  }'
```

**Logic**:
- If `delay_hours >= 2` → `HOTEL_MANDATORY`
- Else → `HOTEL_NOT_REQUIRED`

---

### 3. Ops Feasibility Agent

**Endpoint**: `POST /api/agent/ops/`

**Request**: (empty body or `{}`)

**Response**:
```json
{
  "agent": "Ops-Agent",
  "available_seats": 42,
  "hotel_capacity": "LIMITED"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/agent/ops/ \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## Database Models

### AgentCallLog (Observability Only)
- `agent_name` (CharField)
- `request_payload` (JSONField)
- `response_payload` (JSONField)
- `created_at` (DateTimeField)

**Note**: This is for observability/demo visibility only. It does NOT store business state.

All API calls are automatically logged in `AgentCallLog` for demo visibility. Logging failures are gracefully handled and do not affect API responses.

**No Flight or Passenger models**: This backend does NOT own business data. Salesforce is the system of record.

## Salesforce Integration

Salesforce Agentforce can call these endpoints via HTTP POST requests:

1. **Cost Decision**: Call `/api/agent/gemini-cost/` with flight details
2. **Compliance Check**: Call `/api/agent/compliance/` with delay hours
3. **Feasibility Check**: Call `/api/agent/ops/` for operational status

All responses are deterministic JSON with no extra text.

**📖 For detailed Salesforce integration guide, see [SALESFORCE_INTEGRATION.md](./SALESFORCE_INTEGRATION.md)**

The guide includes:
- Apex HTTP callout examples
- Salesforce Flow configurations
- Agentforce integration patterns
- Complete code examples
- Deployment checklist

## Error Handling

- **Gemini API Failure**: Falls back to rule-based recommendation
- **Invalid Requests**: Returns 400 with error details
- **All errors are logged** in AgentCallLog

## Admin Interface

Access Django admin at `http://localhost:8000/admin/` to view:
- Agent call logs (for observability only)

## Code Structure

```
flight_ops/
├── flight_ops/          # Main project
│   ├── settings.py      # Django settings with PostgreSQL config
│   └── urls.py          # Root URL configuration
├── agents/              # Agents app
│   ├── models.py        # AgentCallLog model (observability only)
│   ├── serializers.py   # Request/response validation
│   ├── services.py      # Stateless business logic (Gemini, Compliance, Ops)
│   ├── views.py         # Stateless API endpoints
│   └── urls.py          # Agent URL routes
└── requirements.txt     # Python dependencies
```

## Performance Notes

- Backend is fully stateless - no business data queries
- Agent calls are logged for observability (logging failures don't affect responses)
- Database indexes on AgentCallLog for query performance
- All services are pure functions (no side effects on business state)

## Testing

Example test scenarios:

```bash
# Test Gemini Cost Agent
curl -X POST http://localhost:8000/api/agent/gemini-cost/ \
  -H "Content-Type: application/json" \
  -d '{"delay_hours": 3, "total_passengers": 180, "vip_passengers": 18}'

# Test Compliance Agent
curl -X POST http://localhost:8000/api/agent/compliance/ \
  -H "Content-Type: application/json" \
  -d '{"delay_hours": 3}'

# Test Ops Agent
curl -X POST http://localhost:8000/api/agent/ops/ \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Notes

- **Stateless Architecture**: No business data persistence. Salesforce owns all business state.
- **No Authentication**: Demo only - no auth required
- **Pure JSON**: All responses are deterministic JSON
- **Observability**: Requests logged for demo visibility (optional)
- **Gemini API**: Optional - graceful fallback if API key not set
- **Error Handling**: All errors are handled gracefully without affecting responses
# Agent2Agent_FlightOps
