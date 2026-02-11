# AgentRedCross

A multi-agent hospital workflow system built with Python. Agents coordinate through a central orchestrator and an in-memory event queue to handle patient intake, EHR operations, lab requests, access control, audit logging, and privacy/security.

## Features

- **Multi-agent architecture**: Receptionist, Doctor, EHR, Lab, Access Control, Audit Logger, IDS, and Privacy Guard agents
- **Event-driven messaging**: Agents communicate via a shared queue; the orchestrator dispatches messages to the correct agent
- **Permission-aware**: Each agent has a role and permissions; actions are checked before execution
- **Audit logging**: Actions can be forwarded to an audit logger for compliance
- **PostgreSQL backend**: Patients, medical records, access logs, and lab requests stored in a configurable database

## Prerequisites

- **Python 3.8+**
- **PostgreSQL** (for the hospital database)
- Optional: virtual environment (recommended)

## Quick Start

### 1. Clone and set up environment

```bash
git clone <repo-url>
cd AgentRedCross
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure the database

Create a PostgreSQL database (e.g. `hospital_db`) and set environment variables (or use defaults):

| Variable    | Description        | Default    |
|------------|--------------------|------------|
| `DB_HOST`  | PostgreSQL host    | `localhost`|
| `DB_PORT`  | PostgreSQL port    | `5432`     |
| `DB_USER`  | Database user      | `postgres` |
| `DB_PASSWORD` | Database password | `password` |
| `DB_NAME`  | Database name      | `hospital_db` |

Create a `.env` file with the variables below if you use one (optional).

### 3. Initialize the schema

From the project root:

```bash
python -c "from database.db_init import init_database; init_database()"
```

### 4. Run the orchestrator and agents

Register your agents with the orchestrator and start the event loop (see **Usage** below). The codebase provides the core and agents; you can wire them in a script or a FastAPI app (see `requirements.txt` for `uvicorn`/`fastapi`).

## Project Structure

```
AgentRedCross/
├── agents/           # All agent implementations
│   ├── base_agent.py       # Base class (permissions, audit, send_message)
│   ├── receptionist_agent.py
│   ├── doctor_agent.py
│   ├── ehr_agent.py
│   ├── lab_agent.py
│   ├── access_control_agent.py
│   ├── audit_logger_agent.py
│   ├── ids_agent.py
│   └── privacy_guard.py
├── core/
│   ├── orchestrator.py     # Central message dispatcher
│   ├── event_queue.py      # In-memory message queue
│   └── database.py         # DB utilities
├── database/
│   ├── db_config.py        # DB connection config (env)
│   ├── db_init.py          # Schema initialization
│   ├── db_pool.py          # Connection pool
│   └── hospital_schema.sql # Tables: patients, medical_records, access_logs, lab_requests
├── requirements.txt
└── README.md
```

## Agents

| Agent               | Role          | Main responsibilities                          |
|---------------------|---------------|-------------------------------------------------|
| **Receptionist**    | receptionist  | Patient intake, scheduling, create_patient      |
| **Doctor**          | doctor        | Diagnoses, prescriptions, read/write records    |
| **EHR Agent**       | ehr           | CRUD for patients and medical records           |
| **Lab Agent**       | lab           | Lab requests and results                        |
| **Access Control**  | access_control| Access checks and policy enforcement            |
| **Audit Logger**    | audit_logger  | Persist access/audit events                     |
| **IDS Agent**       | ids           | Intrusion / anomaly detection                   |
| **Privacy Guard**   | privacy_guard | Privacy and consent enforcement                 |

All agents extend `BaseAgent`, implement `process_message(message)`, and use `send_message(to, action, data)` to talk to other agents. The orchestrator injects the shared `event_queue` when registering each agent.

## Usage

Example: register agents and push a message into the queue.

```python
from core.orchestrator import Orchestrator
from agents.receptionist_agent import ReceptionistAgent
from agents.ehr_agent import EHRAgent
from agents.audit_logger_agent import AuditLoggerAgent

orch = Orchestrator()
orch.register_agent("receptionist", ReceptionistAgent("receptionist"))
orch.register_agent("ehr_agent", EHRAgent("ehr_agent"))
orch.register_agent("audit_logger", AuditLoggerAgent("audit_logger"))

# Example: trigger patient intake (receptionist -> ehr_agent, audit_logger)
orch.queue.push({
    "from": "api",
    "to": "receptionist",
    "action": "patient_intake",
    "data": {"name": "Jane Doe", "dob": "1990-01-15", "contact": "jane@example.com"},
    "timestamp": "2025-02-11T12:00:00"
})

# Run the loop (blocking) to process messages
orch.start()
```

Messages use the format: `from`, `to`, `action`, `data`, `timestamp`. The orchestrator delivers by `to`; agents can send follow-up messages via `send_message`.

## Testing

```bash
pytest
```

Add tests under `tests/` if not present; use pytest fixtures for DB and orchestrator where needed.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — Event queue, orchestrator, message contract, and agent contract
- [Contributing](docs/CONTRIBUTING.md) — How to contribute to the project

## License

See [LICENSE](LICENSE) in the repository root, if present.
