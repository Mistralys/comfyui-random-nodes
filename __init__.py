"""Extension registration for ComfyUI Random Nodes."""

from typing_extensions import override
from comfy_api.latest import ComfyExtension, io

from .nodes import (
    RandomIntNode,
    RandomFloatNode,
    RandomFloatFromPresetNode,
)

WEB_DIRECTORY = "./js"


class RandomNodesExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [
            RandomIntNode,
            RandomFloatNode,
            RandomFloatFromPresetNode,
        ]


async def comfy_entrypoint() -> RandomNodesExtension:
    return RandomNodesExtension()
