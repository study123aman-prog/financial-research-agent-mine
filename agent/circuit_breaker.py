"""
Circuit Breaker
Prevents cascading failures when tools repeatedly fail
"""

import time
from typing import Dict, Any
from datetime import datetime
from enum import Enum


class CircuitState(Enum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Blocking calls - tool is broken
    HALF_OPEN = "half_open" # Testing if tool recovered


class CircuitBreaker:
    """
    Circuit breaker for a single tool.

    States:
    CLOSED  → tool working normally
    OPEN    → tool failed too many times, blocking calls
    HALF_OPEN → testing if tool recovered after reset timeout
    """

    def __init__(
        self,
        tool_name: str,
        failure_threshold: int = 3,
        reset_timeout: float = 60.0
    ):
        self.tool_name = tool_name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0

    def can_execute(self) -> bool:
        """Check if the tool can be called"""

        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if reset timeout has passed
            if self.last_failure_time:
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.reset_timeout:
                    print(f"[Circuit Breaker] {self.tool_name}: OPEN → HALF_OPEN (testing recovery)")
                    self.state = CircuitState.HALF_OPEN
                    return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return True

        return False

    def record_success(self):
        """Record a successful tool call"""
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 2:
                print(f"[Circuit Breaker] {self.tool_name}: HALF_OPEN → CLOSED (recovered)")
                self.state = CircuitState.CLOSED
                self.success_count = 0

    def record_failure(self):
        """Record a failed tool call"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            print(f"[Circuit Breaker] {self.tool_name}: HALF_OPEN → OPEN (still failing)")
            self.state = CircuitState.OPEN
            return

        if self.failure_count >= self.failure_threshold:
            print(f"[Circuit Breaker] {self.tool_name}: CLOSED → OPEN ({self.failure_count} failures)")
            self.state = CircuitState.OPEN

    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        return {
            "tool_name": self.tool_name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure": self.last_failure_time,
            "reset_timeout": self.reset_timeout
        }


class CircuitBreakerRegistry:
    """
    Manages circuit breakers for all tools.
    One circuit breaker per tool.
    """

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}

    def get_breaker(self, tool_name: str) -> CircuitBreaker:
        """Get or create a circuit breaker for a tool"""
        if tool_name not in self._breakers:
            self._breakers[tool_name] = CircuitBreaker(tool_name)
        return self._breakers[tool_name]

    def can_execute(self, tool_name: str) -> bool:
        """Check if a tool can be executed"""
        return self.get_breaker(tool_name).can_execute()

    def record_success(self, tool_name: str):
        """Record successful execution"""
        self.get_breaker(tool_name).record_success()

    def record_failure(self, tool_name: str):
        """Record failed execution"""
        self.get_breaker(tool_name).record_failure()

    def get_all_status(self) -> Dict[str, Any]:
        """Get status of all circuit breakers"""
        return {
            name: breaker.get_status()
            for name, breaker in self._breakers.items()
        }

    def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self._breakers.values():
            breaker.state = CircuitState.CLOSED
            breaker.failure_count = 0
        print("[Circuit Breaker Registry] All breakers reset")


# Global circuit breaker registry
_circuit_registry = CircuitBreakerRegistry()


def get_circuit_registry() -> CircuitBreakerRegistry:
    """Get the global circuit breaker registry"""
    return _circuit_registry