# Tech Stack & Patterns

## Runtime

| Property | Value |
|---|---|
| Language | Python 3.10+ |
| Host Platform | ComfyUI (custom node) |
| API | ComfyUI V3 (`comfy_api.latest`) — no V1 fallback |

## Dependencies

| Dependency | Source | Purpose |
|---|---|---|
| `comfy_api.latest` | ComfyUI built-in | V3 node API (`io`, `ui`, `ComfyNode`, `ComfyExtension`) |
| `typing_extensions` | ComfyUI built-in | `@override` decorator for `get_node_list()` |
| `random` | Python stdlib | Random number generation |

No external (pip) dependencies.

## Architecture

A set of ComfyUI V3 custom nodes for random number generation, registered as a single extension. Two nodes are implemented: `RandomIntNode` and `RandomFloatNode`.

| Pattern | Description |
|---|---|
| V3 Node class | `io.ComfyNode` subclass with `define_schema()` + `execute()` classmethods |
| V3 Registration | `ComfyExtension` subclass + module-level `comfy_entrypoint()` |

## Build & Packaging

| Property | Value |
|---|---|
| Package manager | pip (installed via ComfyUI `custom_nodes/`) |
| Build tool | None (pure Python) |
| Package metadata | `pyproject.toml` |
| Test framework | Mock-based unit tests (`verify_*.py`) + manual testing in ComfyUI |
