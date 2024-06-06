from collections.abc import Callable
import copy
import inspect
import traceback
from types import GenericAlias
from typing import Optional, get_origin, Annotated


from dataclasses import dataclass
from typing import Any


@dataclass
class ToolObservation:
    content_type: str
    text: str
    image_url: Optional[str] = None
    role_metadata: Optional[str] = None
    metadata: Any = None


class ToolsManager:
    def __init__(self):

        self._TOOL_HOOKS = {}

        self._TOOL_DESCRIPTIONS = []

    def register_tool(self, func: Callable):
        tool_name = func.__name__
        tool_description = inspect.getdoc(func)
        if tool_description is not None:
            tool_description = tool_description.strip()
        else:
            tool_description = "No description provided."
        python_params = inspect.signature(func).parameters
        tool_params = []

        for name, param in python_params.items():
            annotation = param.annotation
            if annotation is inspect.Parameter.empty:
                raise TypeError(f"Parameter `{name}` missing type annotation")
            if get_origin(annotation) != Annotated:
                raise TypeError(
                    f"Annotation type for `{name}` must be typing.Annotated")

            typ, (description, required) = annotation.__origin__, annotation.__metadata__
            typ: str = str(typ) if isinstance(
                typ, GenericAlias) else typ.__name__
            if not isinstance(description, str):
                raise TypeError(f"Description for `{name}` must be a string")
            if not isinstance(required, bool):
                raise TypeError(f"Required for `{name}` must be a bool")

            tool_params.append(
                {
                    "name": name,
                    "description": description,
                    "type": typ,
                    "required": required,
                }
            )
        tool_def = {
            "name": tool_name,
            "description": tool_description,
            "params": tool_params
        }
        self._TOOL_HOOKS[tool_name] = func
        self._TOOL_DESCRIPTIONS.append(tool_def)

        return func

    def dispatch_tool(self, tool_name: str, tool_params: dict) -> list[ToolObservation]:
        if tool_name not in self._TOOL_HOOKS:
            err = f"Tool `{tool_name}` not found. Please use a provided tool."
            return [ToolObservation("system_error", err)]

        tool_hook = self._TOOL_HOOKS[tool_name]
        try:
            ret: str = tool_hook(**tool_params)
            return [ToolObservation(tool_name, str(ret))]
        except:
            err = traceback.format_exc()
            return [ToolObservation("system_error", err)]

    def get_tools(self) -> list[dict]:
        return copy.deepcopy(self._TOOL_DESCRIPTIONS)
