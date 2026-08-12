# File Tree

```
comfyui-random-nodes/
  __init__.py           # Extension registration: RandomNodesExtension + comfy_entrypoint()
  nodes.py              # RandomIntNode, RandomFloatNode + module-level helpers
  pyproject.toml        # Package metadata (name, version, license, ComfyUI entry point)
  README.md             # User-facing documentation
  LICENSE               # MIT license
  AGENTS.md             # AI agent operating manual
  CLAUDE.md             # Claude companion (imports AGENTS.md)
  changelog.md          # Project changelog
  js/
    random_nodes.js      # Frontend extension: buttons + widget synchronization
  tests/
    verify_random_int.py    # Mock-based unit tests for RandomIntNode
    verify_random_float.py  # Mock-based unit tests for RandomFloatNode
  docs/
    agents/
      project-manifest/ # Structured codebase overview for AI agents
        README.md       #   Manifest index
        api-surface.md  #   Node class schemas and method signatures
        constraints.md  #   Design rules and conventions
        data-flows.md   #   Execution paths through the nodes
        file-tree.md    #   This file
        tech-stack.md   #   Runtime, dependencies, architecture
      plans/            # Implementation plans
      projects/         # Project specifications
```
