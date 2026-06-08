"""Function signature to MCP inputSchema conversion."""

from __future__ import annotations
import enum
import inspect
import types
from typing import Any, get_args, get_origin, get_type_hints

_PRIMITIVE_MAP = {
    str: {"type": "string"},
    int: {"type": "integer"},
    float: {"type": "number"},
    bool: {"type": "boolean"},
}


def annotationToJsonSchema(annotation: Any) -> dict:
    if annotation is inspect.Parameter.empty:
        return {"type": "string"}
    if annotation in _PRIMITIVE_MAP:
        return dict(_PRIMITIVE_MAP[annotation])
    if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        return {"type": "string", "enum": [m.value for m in annotation]}
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is list:
        item = {"type": "string"}
        if args:
            item = annotationToJsonSchema(args[0])
        return {"type": "array", "items": item}
    isUnion = origin is types.UnionType if hasattr(types, "UnionType") else False
    try:
        import typing

        isUnion = isUnion or (origin is typing.Union)
    except AttributeError:
        pass
    if isUnion and args:
        nonNone = [a for a in args if a is not type(None)]
        if nonNone:
            return annotationToJsonSchema(nonNone[0])
    if origin is dict:
        return {"type": "object"}
    return {"type": "string"}


def functionToInputSchema(func) -> dict:
    sig = inspect.signature(func)
    typeHints = get_type_hints(func)
    props: dict = {}
    required: list = []
    for name, param in sig.parameters.items():
        if name == "self":
            continue
        annotation = typeHints.get(name, param.annotation)
        props[name] = annotationToJsonSchema(annotation)
        if param.default is not inspect.Parameter.empty:
            default = param.default
            if isinstance(default, enum.Enum):
                default = default.value
            props[name]["default"] = default
        if param.default is inspect.Parameter.empty:
            required.append(name)
    schema = {"type": "object", "properties": props}
    if required:
        schema["required"] = required
    return schema


def functionToMcpToolSchema(func, riskLevel: str | None = None) -> dict:
    tool = {
        "name": func.__name__,
        "description": inspect.getdoc(func) or f"Execute {func.__name__}.",
        "inputSchema": functionToInputSchema(func),
    }
    if riskLevel:
        tool["annotations"] = {
            "riskLevel": riskLevel,
            "readOnlyHint": riskLevel == "read_only",
            "destructiveHint": riskLevel == "dangerous",
        }
    return tool


def functionToToolSchema(func) -> dict:
    """Backward-compatible OpenAI tools schema for legacy callers."""
    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": (func.__doc__ or "").strip().split("\n")[0],
            "parameters": functionToInputSchema(func),
        },
    }
