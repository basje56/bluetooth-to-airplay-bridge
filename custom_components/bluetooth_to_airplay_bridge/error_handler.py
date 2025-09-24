"""Enhanced error handling with exponential backoff and recovery mechanisms."""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable, Optional, TypeVar, Union, cast

_LOGGER = logging.getLogger(__name__)

T = TypeVar('T')

class ErrorType(Enum):
    """Error type classifications."""
    USER_ERROR = "user_error"
    TRANSIENT_ERROR = "transient_error"
    PERMANENT_ERROR = "permanent_error"
    SYSTEM_ERROR = "system_error"
    NETWORK_ERROR = "network_error"
    BLUETOOTH_ERROR = "bluetooth_error"
    AUDIO_ERROR = "audio_error"
    AIRPLAY_ERROR = "airplay_error"

class ErrorCode(Enum):
    """Specific error codes."""
    # User errors
    INVALID_CONFIG = "INVALID_CONFIG"
    INVALID_BLUETOOTH_ADDRESS = "INVALID_BLUETOOTH_ADDRESS"
    INVALID_AIRPLAY_NAME = "INVALID_AIRPLAY_NAME"
    
    # Network errors
    NET_TIMEOUT = "NET_TIMEOUT"
    NET_CONNECTION_REFUSED = "NET_CONNECTION_REFUSED"
    NET_DNS_FAILURE = "NET_DNS_FAILURE"
    
    # Bluetooth errors
    BT_DEVICE_NOT_FOUND = "BT_DEVICE_NOT_FOUND"
    BT_CONNECTION_FAILED = "BT_CONNECTION_FAILED"
    BT_PAIRING_FAILED = "BT_PAIRING_FAILED"
    BT_AUDIO_NOT_AVAILABLE = "BT_AUDIO_NOT_AVAILABLE"
    
    # Audio errors
    AUDIO_CAPTURE_FAILED = "AUDIO_CAPTURE_FAILED"
    AUDIO_CODEC_UNSUPPORTED = "AUDIO_CODEC_UNSUPPORTED"
    AUDIO_PIPELINE_ERROR = "AUDIO_PIPELINE_ERROR"
    
    # AirPlay errors
    AIRPLAY_SERVER_START_FAILED = "AIRPLAY_SERVER_START_FAILED"
    AIRPLAY_MDNS_FAILED = "AIRPLAY_MDNS_FAILED"
    AIRPLAY_AUTH_FAILED = "AIRPLAY_AUTH_FAILED"
    
    # System errors
    DEPENDENCY_MISSING = "DEPENDENCY_MISSING"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"

class StructuredError:
    """Structured error with metadata."""
    
    def __init__(
        self,
        error_type: ErrorType,
        error_code: ErrorCode,
        message: str,
        component: str,
        context: Optional[dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
        suggested_actions: Optional[list[str]] = None
    ) -> None:
        """Initialize structured error."""
        self.error_type = error_type
        self.error_code = error_code
        self.message = message
        self.component = component
        self.context = context or {}
        self.original_exception = original_exception
        self.suggested_actions = suggested_actions or []
        self.timestamp = datetime.now().isoformat()
        self.request_id = str(uuid.uuid4())
        
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "level": "ERROR",
            "component": self.component,
            "event": "error",
            "message": self.message,
            "timestamp": self.timestamp,
            "request_id": self.request_id,
            "error": {
                "type": self.error_type.value,
                "code": self.error_code.value,
                "message": self.message,
                "context": self.context,
                "suggested_actions": self.suggested_actions,
                "stack": str(self.original_exception) if self.original_exception else None
            }
        }
        
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
        
    def log(self) -> None:
        """Log the error with appropriate level."""
        if self.error_type == ErrorType.USER_ERROR:
            _LOGGER.warning("User error: %s", self.message)
        elif self.error_type == ErrorType.TRANSIENT_ERROR:
            _LOGGER.warning("Transient error: %s", self.message)
        else:
            _LOGGER.error("Error: %s", self.message)
            
        _LOGGER.debug("Error details: %s", self.to_json())

class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ) -> None:
        """Initialize retry configuration."""
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

class ErrorHandler:
    """Enhanced error handler with retry and recovery mechanisms."""
    
    def __init__(self) -> None:
        """Initialize error handler."""
        self._error_counts: dict[str, int] = {}
        self._last_error_time: dict[str, float] = {}
        
    async def retry_with_backoff(
        self,
        func: Union[Callable[..., T], Callable[..., Awaitable[T]]],
        *args,
        retry_config: Optional[RetryConfig] = None,
        error_context: Optional[dict[str, Any]] = None,
        **kwargs
    ) -> T:
        """Execute function with exponential backoff retry."""
        config = retry_config or RetryConfig()
        context = error_context or {}
        
        last_exception = None
        
        for attempt in range(config.max_retries + 1):
            try:
                if attempt > 0:
                    delay = self._calculate_delay(attempt, config)
                    _LOGGER.debug("Retrying in %.2f seconds (attempt %d/%d)", 
                                delay, attempt + 1, config.max_retries + 1)
                    await asyncio.sleep(delay)
                    
                if asyncio.iscoroutinefunction(func):
                    result = await cast(Callable[..., Awaitable[T]], func)(*args, **kwargs)
                else:
                    result = cast(Callable[..., T], func)(*args, **kwargs)
                
                # Reset error count on success
                func_key = f"{func.__name__}_{hash(str(args))}"
                self._error_counts.pop(func_key, None)
                self._last_error_time.pop(func_key, None)
                
                return result
                
            except Exception as err:
                last_exception = err
                func_key = f"{func.__name__}_{hash(str(args))}"
                self._error_counts[func_key] = self._error_counts.get(func_key, 0) + 1
                self._last_error_time[func_key] = time.time()
                
                # Determine if we should retry
                if not self._should_retry(err, attempt, config.max_retries):
                    break
                    
                _LOGGER.warning("Attempt %d failed: %s", attempt + 1, err)
                
        # All retries exhausted
        if last_exception is None:
            last_exception = RuntimeError("All retry attempts failed with no recorded exception")
        structured_error = self._create_structured_error(last_exception, context)
        structured_error.log()
        raise last_exception
        
    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay for exponential backoff."""
        delay = config.base_delay * (config.exponential_base ** (attempt - 1))
        delay = min(delay, config.max_delay)
        
        if config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
            
        return delay
        
    def _should_retry(self, exception: Exception, attempt: int, max_retries: int) -> bool:
        """Determine if an exception should trigger a retry."""
        if attempt >= max_retries:
            return False
            
        # Don't retry user errors
        if isinstance(exception, (ValueError, TypeError)):
            return False
            
        # Retry network and transient errors
        if isinstance(exception, (ConnectionError, TimeoutError, OSError)):
            return True
            
        # Retry specific Bluetooth errors
        if "bluetooth" in str(exception).lower():
            if any(keyword in str(exception).lower() for keyword in 
                   ["timeout", "connection", "busy", "resource"]):
                return True
                
        return False
        
    def _create_structured_error(
        self, 
        exception: Exception, 
        context: dict[str, Any]
    ) -> StructuredError:
        """Create structured error from exception."""
        error_type, error_code = self._classify_error(exception)
        
        return StructuredError(
            error_type=error_type,
            error_code=error_code,
            message=str(exception),
            component=context.get("component", "unknown"),
            context=context,
            original_exception=exception,
            suggested_actions=self._get_suggested_actions(error_code)
        )
        
    def _classify_error(self, exception: Exception) -> tuple[ErrorType, ErrorCode]:
        """Classify exception into error type and code."""
        exc_str = str(exception).lower()
        
        # User errors
        if isinstance(exception, ValueError):
            if "bluetooth" in exc_str and "address" in exc_str:
                return ErrorType.USER_ERROR, ErrorCode.INVALID_BLUETOOTH_ADDRESS
            return ErrorType.USER_ERROR, ErrorCode.INVALID_CONFIG
            
        # Network errors
        if isinstance(exception, TimeoutError) or "timeout" in exc_str:
            return ErrorType.NETWORK_ERROR, ErrorCode.NET_TIMEOUT
        if isinstance(exception, ConnectionRefusedError):
            return ErrorType.NETWORK_ERROR, ErrorCode.NET_CONNECTION_REFUSED
            
        # Bluetooth errors
        if "bluetooth" in exc_str:
            if "not found" in exc_str or "no such device" in exc_str:
                return ErrorType.BLUETOOTH_ERROR, ErrorCode.BT_DEVICE_NOT_FOUND
            if "connection" in exc_str and "failed" in exc_str:
                return ErrorType.BLUETOOTH_ERROR, ErrorCode.BT_CONNECTION_FAILED
            if "audio" in exc_str:
                return ErrorType.BLUETOOTH_ERROR, ErrorCode.BT_AUDIO_NOT_AVAILABLE
                
        # Audio errors
        if any(keyword in exc_str for keyword in ["gstreamer", "pulse", "alsa", "audio"]):
            if "codec" in exc_str:
                return ErrorType.AUDIO_ERROR, ErrorCode.AUDIO_CODEC_UNSUPPORTED
            if "pipeline" in exc_str:
                return ErrorType.AUDIO_ERROR, ErrorCode.AUDIO_PIPELINE_ERROR
            return ErrorType.AUDIO_ERROR, ErrorCode.AUDIO_CAPTURE_FAILED
            
        # AirPlay errors
        if any(keyword in exc_str for keyword in ["airplay", "shairport", "mdns"]):
            if "mdns" in exc_str or "zeroconf" in exc_str:
                return ErrorType.AIRPLAY_ERROR, ErrorCode.AIRPLAY_MDNS_FAILED
            return ErrorType.AIRPLAY_ERROR, ErrorCode.AIRPLAY_SERVER_START_FAILED
            
        # System errors
        if isinstance(exception, PermissionError):
            return ErrorType.SYSTEM_ERROR, ErrorCode.PERMISSION_DENIED
        if isinstance(exception, ImportError) or "not found" in exc_str:
            return ErrorType.SYSTEM_ERROR, ErrorCode.DEPENDENCY_MISSING
            
        # Default to transient error
        return ErrorType.TRANSIENT_ERROR, ErrorCode.NET_TIMEOUT
        
    def _get_suggested_actions(self, error_code: ErrorCode) -> list[str]:
        """Get suggested actions for error code."""
        suggestions = {
            ErrorCode.INVALID_BLUETOOTH_ADDRESS: [
                "Check Bluetooth device address format (XX:XX:XX:XX:XX:XX)",
                "Verify device is discoverable and paired"
            ],
            ErrorCode.BT_DEVICE_NOT_FOUND: [
                "Ensure Bluetooth device is powered on and discoverable",
                "Check if device is already paired with system",
                "Try scanning for devices: bluetoothctl scan on"
            ],
            ErrorCode.BT_CONNECTION_FAILED: [
                "Restart Bluetooth service: sudo systemctl restart bluetooth",
                "Remove and re-pair the device",
                "Check device compatibility with A2DP profile"
            ],
            ErrorCode.AUDIO_CAPTURE_FAILED: [
                "Install GStreamer: sudo apt install gstreamer1.0-*",
                "Check PulseAudio is running: pulseaudio --check",
                "Verify audio permissions for user"
            ],
            ErrorCode.AIRPLAY_SERVER_START_FAILED: [
                "Install shairport-sync: sudo apt install shairport-sync",
                "Check port 5000 is not in use: netstat -ln | grep 5000",
                "Verify network interface is available"
            ],
            ErrorCode.DEPENDENCY_MISSING: [
                "Install required dependencies from manifest.json",
                "Check Python package versions",
                "Restart Home Assistant after installing dependencies"
            ]
        }
        
        return suggestions.get(error_code, ["Check logs for more details", "Restart the integration"])
        
    def get_error_stats(self) -> dict[str, Any]:
        """Get error statistics."""
        return {
            "error_counts": dict(self._error_counts),
            "last_error_times": dict(self._last_error_time),
            "total_errors": sum(self._error_counts.values())
        }
        
    def reset_error_stats(self) -> None:
        """Reset error statistics."""
        self._error_counts.clear()
        self._last_error_time.clear()

# Global error handler instance
error_handler = ErrorHandler()