"""Deterministic source-level rendering of AST expressions and signatures."""

from __future__ import annotations

import ast


def expression(node: ast.AST | None) -> str:
    if node is None:
        return ""
    return ast.unparse(node)


def _parameter(parameter: ast.arg, prefix: str = "") -> str:
    result = f"{prefix}{parameter.arg}"
    if parameter.annotation is not None:
        result += f": {expression(parameter.annotation)}"
    return result


def function_signature(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    omit_first_parameter: bool = False,
) -> str:
    arguments = node.args
    parts: list[str] = []
    positional = [*arguments.posonlyargs, *arguments.args]
    defaults = [None] * (len(positional) - len(arguments.defaults)) + list(arguments.defaults)
    if omit_first_parameter and positional:
        positional = positional[1:]
        defaults = defaults[1:]
    for index, (parameter, default) in enumerate(zip(positional, defaults)):
        text = _parameter(parameter)
        if default is not None:
            text += f" = {expression(default)}"
        parts.append(text)
        if index == len(arguments.posonlyargs) - 1 and arguments.posonlyargs:
            parts.append("/")
    if arguments.vararg is not None:
        parts.append(_parameter(arguments.vararg, "*"))
    elif arguments.kwonlyargs:
        parts.append("*")
    for parameter, default in zip(arguments.kwonlyargs, arguments.kw_defaults):
        text = _parameter(parameter)
        if default is not None:
            text += f" = {expression(default)}"
        parts.append(text)
    if arguments.kwarg is not None:
        parts.append(_parameter(arguments.kwarg, "**"))
    result = ", ".join(parts)
    result = f"({result})"
    if node.returns is not None:
        result += f" -> {expression(node.returns)}"
    return result


def class_signature(name: str, bases: tuple[str, ...], constructor: ast.FunctionDef | ast.AsyncFunctionDef | None) -> str:
    if constructor is not None:
        return f"{name}{function_signature(constructor, omit_first_parameter=True)}"
    if bases:
        return f"{name}({', '.join(bases)})"
    return name
