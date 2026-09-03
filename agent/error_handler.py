"""
Error Handler
Retry logic with exponential backoff for all tool calls
"""

import time
import random
import functools
from typing import Dict, Any, Callable, Optional
from datetime import datetime


class ToolError(Exception):
    """Custom exception for tool failures"""
    def __init__(self, tool_name: str, message: str, is_retryable: bool = True):
        self.tool_name = tool_name
        self.message = message
        self.is_retryable = is_retryable
        super().__init__(f"[{tool_name}] {message}")


def with_retry(
    func: Callable,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 16.0,
    jitter: float = 0.5
) -> Callable:
    """
    Wrap a function with exponential backoff retry logic.

    Retry schedule:
    Attempt 1: immediate
    Attempt 2: 1s + jitter
    Attempt 3: 2s + jitter
    Attempt 4: 4s + jitter
    Attempt 5: 8s + jitter
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                result = func(*args, **kwargs)
                if attempt > 0:
                    print(f"[Retry] Succeeded on attempt {attempt + 1}")
                return result

            except Exception as e:
                last_error = e

                if attempt == max_retries:
                    print(f"[Retry] All {max_retries} retries exhausted")
                    raise e

                # Calculate delay with exponential backoff
                delay = min(base_delay * (2 ** attempt), max_delay)
                jitter_amount = random.uniform(0, jitter)
                total_delay = delay + jitter_amount

                print(f"[Retry] Attempt {attempt + 1} failed: {str(e)[:50]}")
                print(f"[Retry] Waiting {total_delay:.1f}s before retry...")
                time.sleep(total_delay)

        raise last_error

    return wrapper


def safe_tool_call(
    tool_name: str,
    func: Callable,
    inputs: Dict[str, Any],
    fallback_func: Optional[Callable] = None,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Safely execute a tool with retry and fallback.

    Args:
        tool_name: Name of the tool
        func: Primary tool function
        inputs: Tool inputs
        fallback_func: Optional fallback function
        max_retries: Maximum retry attempts

    Returns:
        Tool result or fallback result
    """

    errors = []

    # Try primary function with retries
    for attempt in range(max_retries + 1):
        try:
            result = func(**inputs)

            if result and not result.get("error"):
                return {
                    **result,
                    "tool_used": tool_name,
                    "attempt": attempt + 1,
                    "used_fallback": False
                }

        except Exception as e:
            errors.append({
                "attempt": attempt + 1,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

            if attempt < max_retries:
                delay = (2 ** attempt) + random.uniform(0, 0.5)
                print(f"[Error Handler] {tool_name} attempt {attempt + 1} failed. Retrying in {delay:.1f}s")
                time.sleep(delay)
            else:
                print(f"[Error Handler] {tool_name} failed after {max_retries + 1} attempts")

    # Try fallback if available
    if fallback_func:
        try:
            print(f"[Error Handler] Trying fallback for {tool_name}")
            result = fallback_func(**inputs)
            return {
                **result,
                "tool_used": f"{tool_name}_fallback",
                "used_fallback": True,
                "original_errors": errors
            }
        except Exception as e:
            print(f"[Error Handler] Fallback also failed: {e}")

    # Return graceful degradation response
    return {
        "success": False,
        "tool_used": tool_name,
        "error": f"All attempts failed for {tool_name}",
        "errors": errors,
        "data": None,
        "used_fallback": False,
        "graceful_degradation": True,
        "message": f"Data from {tool_name} is unavailable. This section may be incomplete."
    }


def log_error(
    tool_name: str,
    error: Exception,
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Log an error with context for debugging and evaluation.

    Args:
        tool_name: Name of the tool that failed
        error: The exception that occurred
        context: Additional context about the failure

    Returns:
        Structured error log entry
    """

    error_entry = {
        "tool_name": tool_name,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.now().isoformat(),
        "context": context or {},
        "is_retryable": _is_retryable_error(error)
    }

    print(f"[Error Log] {tool_name}: {type(error).__name__}: {str(error)[:100]}")
    return error_entry


def _is_retryable_error(error: Exception) -> bool:
    """Determine if an error is worth retrying"""

    error_str = str(error).lower()

    # Non-retryable errors
    non_retryable = [
        "invalid api key",
        "unauthorized",
        "not found",
        "invalid symbol",
        "invalid ticker"
    ]

    for pattern in non_retryable:
        if pattern in error_str:
            return False

    # Retryable errors
    retryable = [
        "timeout",
        "rate limit",
        "too many requests",
        "service unavailable",
        "connection",
        "network"
    ]

    for pattern in retryable:
        if pattern in error_str:
            return True

    return True  # Default to retryable