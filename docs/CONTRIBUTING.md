# Contributing to AgentRedCross

Thank you for your interest in contributing. This document outlines how to set up your environment and submit changes.

## Development setup

1. **Fork and clone** the repository.
2. **Create a virtual environment** and install dependencies:
   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```
3. **PostgreSQL**: Ensure a local (or remote) instance is available. Use `.env` or environment variables for `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`.
4. **Initialize the database** (from repo root):
   ```bash
   python -c "from database.db_init import init_database; init_database()"
   ```

## Code style

- **Python**: Follow PEP 8. Use clear names and docstrings for modules, classes, and public methods.
- **Agents**: Subclass `BaseAgent`, implement `process_message(self, message) -> Dict[str, Any]`, and use `self.send_message(...)` for inter-agent communication.
- **Imports**: Prefer absolute imports from project root (e.g. `from agents.base_agent import BaseAgent`, `from core.orchestrator import Orchestrator`).

## Adding or changing agents

- Put new agents in the `agents/` directory.
- Extend `BaseAgent` and pass `agent_id`, `role`, and `permissions` to `super().__init__()`.
- Document supported `action` types and `data` shapes in the agent’s docstring or in [ARCHITECTURE.md](docs/ARCHITECTURE.md).
- Register the agent with the orchestrator in your entry point or tests.

## Database changes

- Update `database/hospital_schema.sql` with new tables or columns.
- Keep migrations additive where possible; document any breaking changes in the PR.
- Ensure `db_init.py` (or your migration path) applies the schema correctly.

## Testing

- Use **pytest** for tests. Place tests in a `tests/` directory.
- Mock or use a test database for integration tests that touch PostgreSQL.
- Run tests before submitting:
  ```bash
  pytest
  ```

## Submitting changes

1. Create a **branch** from `main` (e.g. `feature/your-feature` or `fix/issue-description`).
2. Make your changes and run tests and any linters you use.
3. **Commit** with clear messages (e.g. “Add LabAgent support for bulk requests”).
4. Open a **Pull Request** against `main`. Describe what changed and why; reference any issues if applicable.
5. Address review feedback; maintainers will merge when ready.

## Questions

Open an issue for bugs, feature ideas, or documentation improvements. For architecture or design discussions, use an issue with an appropriate label if the project uses them.
