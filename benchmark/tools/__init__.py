from benchmark.tools.core import ToolID, ToolRegistry
from benchmark.tools.dlv import DLV_WRAPPER_PATH, DlvTool
from benchmark.tools.vadalog import VADALOG_WRAPPER_PATH, VadalogTool

tool_registry = ToolRegistry()

tool_registry.register(
    ToolID.VADALOG,
    tool_cls=VadalogTool,
    binary_path=VADALOG_WRAPPER_PATH,
)
tool_registry.register(
    ToolID.DLV,
    tool_cls=DlvTool,
    binary_path=DLV_WRAPPER_PATH,
)
