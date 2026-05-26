"""Utility functions and helpers."""

import logging
from typing import Any, Dict
import json


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Setup logging configuration.

    Args:
        level: Logging level

    Returns:
        Configured logger
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)


def serialize_data(data: Any) -> str:
    """Serialize data to JSON string."""
    try:
        return json.dumps(data, default=str)
    except Exception as e:
        logging.error(f"Error serializing data: {e}")
        return ""


def deserialize_data(data: str) -> Any:
    """Deserialize JSON string to Python object."""
    try:
        return json.loads(data)
    except Exception as e:
        logging.error(f"Error deserializing data: {e}")
        return None


def dict_to_str(data: Dict[str, Any]) -> str:
    """Convert dictionary to formatted string."""
    return json.dumps(data, indent=2, default=str)


def batch_iterator(items: list, batch_size: int):
    """Iterate over items in batches."""
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]
