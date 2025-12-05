# core/event_queue.py
"""
Simple in-memory event queue used for inter-agent messaging.

Design goals:
- Extremely simple and deterministic for hackathon demos.
- Supports multiple subscribers (agents) to poll messages.
- Messages are plain dictionaries with fields:
  { from, to, action, data, timestamp }
- Orchestrator is responsible for registering agents and dispatching messages.
"""

from collections import deque
from threading import Lock
from typing import Dict, Any, Optional


class EventQueue:
    def __init__(self):
        self._queue = deque()
        self._lock = Lock()
        # Optional dictionary of callbacks for certain recipients (for routing)
        self.subscribers = {}  # map: agent_id -> callable(message) OR agent object

    def push(self, message: Dict[str, Any]) -> None:
        """Push a message into the queue (thread-safe)."""
        with self._lock:
            self._queue.append(message)

    def pop(self) -> Optional[Dict[str, Any]]:
        """Pop next message from queue. Returns None if empty."""
        with self._lock:
            if not self._queue:
                return None
            return self._queue.popleft()

    def peek(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            if not self._queue:
                return None
            return self._queue[0]

    def register(self, agent_id: str, recipient):
        """
        Register an agent (or callback) to the subscriber map.
        The orchestrator will look up recipients in this map to deliver messages directly.
        """
        self.subscribers[agent_id] = recipient

    def unregister(self, agent_id: str):
        if agent_id in self.subscribers:
            del self.subscribers[agent_id]

    def route_if_possible(self, message: Dict[str, Any]) -> bool:
        """
        If the target 'to' exists as a registered subscriber, call it directly and return True.
        Otherwise return False and let the orchestrator handle it.
        """
        target = message.get("to")
        if target is None:
            return False

        recipient = self.subscribers.get(target)
        if not recipient:
            return False

        # If the registered recipient is an agent object with process_message, call it.
        try:
            if hasattr(recipient, "process_message"):
                # Deliver synchronously and optionally allow the recipient to send its own messages.
                recipient.process_message(message)
            elif callable(recipient):
                recipient(message)
            else:
                # Unknown subscriber type — ignore
                return False
            return True
        except Exception as exc:
            # Avoid crashing the queue on agent errors; let orchestrator see logs.
            print(f"[EventQueue] Error delivering to {target}: {exc}")
            return False
