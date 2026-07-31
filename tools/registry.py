import logging
import importlib
from typing import Any, Callable

logger = logging.getLogger(__name__)

_tool_registry: dict[str, dict] = {}


def register_tool(
    name: str | None = None,
    description: str = "",
    parameters: dict | None = None,
):
    def decorator(func: Callable):
        tool_name = name or func.__name__
        _tool_registry[tool_name] = {
            "func": func,
            "description": description or func.__doc__ or "",
            "parameters": parameters or {"type": "object", "properties": {}},
        }
        logger.debug(f"Registered tool: {tool_name}")
        return func
    return decorator


def get_tool_schemas() -> list[dict]:
    schemas = []
    for name, info in _tool_registry.items():
        schemas.append({
            "type": "function",
            "function": {
                "name": name,
                "description": info["description"],
                "parameters": info["parameters"],
            },
        })
    return schemas


async def execute_tool(name: str, arguments: dict) -> Any:
    if name not in _tool_registry:
        raise ValueError(f"Unknown tool: {name}")
    func = _tool_registry[name]["func"]
    if importlib.util.find_spec("asyncio") and hasattr(func, "__call__"):
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return await func(**arguments)
    return func(**arguments)


def get_registered_tools() -> list[str]:
    return list(_tool_registry.keys())
