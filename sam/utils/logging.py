"""
Logging utilities for S.A.M.

Provides structured logging using structlog with JSON output and
configurable log levels.
"""

import sys
from typing import Any, Dict, Optional

import structlog
from structlog.stdlib import LoggerFactory


def setup_logging(level: str = "INFO", 
                  format_type: str = "json",
                  log_file: Optional[str] = None) -> None:
    """
    Setup structured logging for S.A.M.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Output format ("json" or "console")
        log_file: Optional log file path
    """
    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if format_type == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    import logging
    
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout if log_file is None else open(log_file, 'a'),
        level=getattr(logging, level.upper()),
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return structlog.get_logger(name)


def log_event(logger: structlog.stdlib.BoundLogger,
              event_type: str,
              **kwargs: Any) -> None:
    """
    Log a structured event.
    
    Args:
        logger: Logger instance
        event_type: Type of event (e.g., "MODE_SWITCH", "FIREWALL")
        **kwargs: Additional event data
    """
    logger.info(event_type, **kwargs)


def log_error(logger: structlog.stdlib.BoundLogger,
              error: Exception,
              context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an error with context.
    
    Args:
        logger: Logger instance
        error: Exception to log
        context: Optional context data
    """
    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    
    if context:
        error_data.update(context)
    
    logger.error("ERROR", exc_info=error, **error_data)


def log_metric(logger: structlog.stdlib.BoundLogger,
               metric_name: str,
               value: float,
               tags: Optional[Dict[str, str]] = None) -> None:
    """
    Log a metric.
    
    Args:
        logger: Logger instance
        metric_name: Name of the metric
        value: Metric value
        tags: Optional tags for the metric
    """
    metric_data = {
        "metric_name": metric_name,
        "value": value,
    }
    
    if tags:
        metric_data["tags"] = tags
    
    logger.info("METRIC", **metric_data)


def log_psp_event(logger: structlog.stdlib.BoundLogger,
                  event: str,
                  psp_id: str,
                  mode: str,
                  vsp_value: float,
                  **kwargs: Any) -> None:
    """
    Log a PSP-related event.
    
    Args:
        logger: Logger instance
        event: Event type
        psp_id: PSP instance ID
        mode: Current cognitive mode
        vsp_value: Current V_SP value
        **kwargs: Additional event data
    """
    event_data = {
        "psp_id": psp_id,
        "mode": mode,
        "vsp_value": vsp_value,
        **kwargs
    }
    
    logger.info(f"PSP_{event}", **event_data)


def log_firewall_event(logger: structlog.stdlib.BoundLogger,
                       schema_id: str,
                       action: str,  # "admit", "quarantine", "reject"
                       reason: str,
                       confidence: float,
                       **kwargs: Any) -> None:
    """
    Log a schema firewall event.
    
    Args:
        logger: Logger instance
        schema_id: Schema ID
        action: Firewall action
        reason: Reason for action
        confidence: Confidence score
        **kwargs: Additional event data
    """
    event_data = {
        "schema_id": schema_id,
        "action": action,
        "reason": reason,
        "confidence": confidence,
        **kwargs
    }
    
    logger.info("FIREWALL", **event_data)


def log_cdp_event(logger: structlog.stdlib.BoundLogger,
                  cdp_id: str,
                  event: str,
                  depth: int,
                  **kwargs: Any) -> None:
    """
    Log a CDP (Catalyst Deliberation Protocol) event.
    
    Args:
        logger: Logger instance
        cdp_id: CDP session ID
        event: Event type
        depth: Current deliberation depth
        **kwargs: Additional event data
    """
    event_data = {
        "cdp_id": cdp_id,
        "event": event,
        "depth": depth,
        **kwargs
    }
    
    logger.info(f"CDP_{event}", **event_data)


def log_interop_event(logger: structlog.stdlib.BoundLogger,
                      packet_id: str,
                      event: str,
                      source_instance: str,
                      target_instance: str,
                      **kwargs: Any) -> None:
    """
    Log an inter-S.A.M. communication event.
    
    Args:
        logger: Logger instance
        packet_id: Packet ID
        event: Event type
        source_instance: Source instance ID
        target_instance: Target instance ID
        **kwargs: Additional event data
    """
    event_data = {
        "packet_id": packet_id,
        "event": event,
        "source_instance": source_instance,
        "target_instance": target_instance,
        **kwargs
    }
    
    logger.info(f"INTEROP_{event}", **event_data)