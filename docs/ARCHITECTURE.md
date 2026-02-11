# Architecture

This document describes the design of the AgentRedCross multi-agent hospital system: the event queue, orchestrator, message contract, agent contract, and database schema.

## Overview

The system is **event-driven**. Agents do not call each other directly; they push messages onto a shared **EventQueue**. The **Orchestrator** runs a loop that pops messages and dispatches them to the correct agent by `to` id. Agents can send new messages via `send_message()`, which pushes to the same queue. This keeps coupling low and makes it easy to add or replace agents.

```
┌─────────────┐     push      ┌──────────────┐     pop / dispatch     ┌─────────────┐
│   Agents    │ ───────────►  │  EventQueue  │  ◄───────────────────  │ Orchestrator│
│ (multiple)  │ ◄───────────  │  (in-memory) │  ───────────────────►  │             │
└─────────────┘   (via orch)  └──────────────┘                        └─────────────┘
```

## Event queue

- **Module**: `core/event_queue.py`
- **Role**: Thread-safe, in-memory FIFO queue of message dictionaries.
- **Operations**:
  - `push(message)` — enqueue
  - `pop()` — dequeue (returns `None` if empty)
  - `peek()` — look at next without removing
- **Routing**: The queue keeps a `subscribers` map: `agent_id -> agent object`. The orchestrator can call `route_if_possible(message)`: if `message["to"]` is in `subscribers`, the queue delivers the message directly to that agent’s `process_message(message)` and returns `True`; otherwise it returns `False` and the orchestrator handles delivery itself.

Design is intentionally simple for demos and hackathons. For production, the queue could be replaced with Redis, RabbitMQ, or another durable broker.

## Orchestrator

- **Module**: `core/orchestrator.py`
- **Responsibilities**:
  1. Hold a single `EventQueue` and a map `agents: agent_id -> agent instance`.
  2. **Register/unregister agents**: On register, the orchestrator sets `agent.event_queue = self.queue` and adds the agent to `queue.subscribers[agent_id]`.
  3. **Dispatch**: For each message, first try `queue.route_if_possible(message)`. If that returns `False`, look up `agents[message["to"]]` and call `agent.process_message(message)`.
  4. **Event loop**: `start()` runs a blocking loop: `pop()` a message, dispatch it, and optionally push a response back if the original message had a `reply_to` field. If the queue is empty, sleep for `poll_interval` (default 0.05s).

All delivery is **synchronous** in the main thread. For scaling, the loop could be replaced with async workers or a separate consumer process.

## Message contract

Every message is a dictionary with at least:

| Field       | Type   | Description                    |
|------------|--------|--------------------------------|
| `from`     | string | Sender agent id (or `"api"`)   |
| `to`       | string | Recipient agent id             |
| `action`   | string | Verb or command (e.g. `create_patient`, `log_event`) |
| `data`     | dict   | Payload for the action         |
| `timestamp`| string | ISO datetime (optional)        |
| `reply_to` | string | (Optional) Agent id to send response to |

Agents interpret `action` and `data`; the orchestrator only uses `to` (and `reply_to` for responses). Responses returned from `process_message()` can be wrapped by the orchestrator and pushed to `reply_to` as a message with `action: "response"` and `data: <return value>`.

## Agent contract

- **Base class**: `agents/base_agent.py` — `BaseAgent(ABC)`.
- **Constructor**: `__init__(self, agent_id: str, role: str, permissions: list)`. Subclasses call `super().__init__(...)` with their id, role, and list of permission strings.
- **Required method**: `process_message(self, message: Dict[str, Any]) -> Dict[str, Any]`. Implementations should switch on `message["action"]` and return a result dict (or error dict with e.g. `status: "error"`).
- **Provided helpers**:
  - `send_message(target_agent, action, data)` — builds a message and pushes it to `self.event_queue` (injected by orchestrator).
  - `check_permission(action)` — returns `action in self.permissions`.
  - `audit_log(action, patient_id, details)` — sends a `log_event` message to `audit_logger` with agent_id, action, patient_id, details, timestamp.

New agents must live in `agents/`, subclass `BaseAgent`, and be registered with the orchestrator under a unique `agent_id` that matches the `to` field used in messages.

## Database schema

- **Config**: `database/db_config.py` — reads `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` from the environment.
- **Schema file**: `database/hospital_schema.sql`.
- **Tables**:
  - **patients**: `patient_id` (UUID), `name`, `dob`, `contact`, `created_at`.
  - **medical_records**: `record_id`, `patient_id` (FK), `diagnosis`, `medications`, `lab_results` (JSONB), `imaging_results` (JSONB), `created_at`.
  - **access_logs**: `log_id`, `agent_id`, `patient_id`, `action`, `timestamp`.
  - **lab_requests**: `request_id`, `patient_id`, `doctor_id`, `test_type`, `status`, `created_at`.

Initialization is done via `database/db_init.py`, which runs the schema SQL against the configured database. Connection pooling is in `database/db_pool.py` for use by agents that need DB access.

## Data flow examples

1. **Patient intake**: API or client pushes `to: "receptionist", action: "patient_intake", data: { name, dob, contact }`. Receptionist checks permission, sends `create_patient` to EHR agent, may send audit event to audit_logger. EHR agent writes to `patients` (and possibly `medical_records`).
2. **Lab request**: Doctor agent sends a message to lab agent with patient id and test type; lab agent may create/update `lab_requests` and later push results back.
3. **Audit**: Any agent can call `self.audit_log(...)`, which sends a message to `audit_logger`; the audit logger agent writes to `access_logs` or a dedicated audit store.

For more detail on each agent’s supported actions and payloads, see the docstrings in the respective files under `agents/`.
