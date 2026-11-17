# AGENTS.md — ComfyUI Random Nodes

> **This file is the operating manual for AI agents entering this codebase.**
> Read it in full before making any changes.

---

## 1. Project Documentation — Start Here

| Document | Path | Purpose |
|----------|------|---------|
| Project Manifest | `docs/agents/project-manifest/README.md` | Structured overview of the codebase (tech stack, API surface, data flows, constraints) |
| Tech Stack | `docs/agents/project-manifest/tech-stack.md` | Runtime, dependencies, architectural patterns |
| API Surface | `docs/agents/project-manifest/api-surface.md` | Node class schemas and method signatures |
| Constraints | `docs/agents/project-manifest/constraints.md` | Non-negotiable design decisions and project conventions |
| File Tree | `docs/agents/project-manifest/file-tree.md` | Directory structure with annotations |
| Data Flows | `docs/agents/project-manifest/data-flows.md` | Execution paths through the nodes |
| README | `README.md` | User-facing project description |

> **Status: Implemented.** `nodes.py` (RandomIntNode, RandomFloatNode), `__init__.py`,
> `js/random_nodes.js`, `pyproject.toml`, and `changelog.md` exist. Consult the manifest
> for architectural intent before making further changes.

### Quick Start Workflow

1. **Read** `docs/agents/project-manifest/constraints.md` — understand the non-negotiable design rules before writing a single line.
2. **Read** `docs/agents/project-manifest/tech-stack.md` — understand the runtime, dependencies, and architecture pattern.
3. **Read** `docs/agents/project-manifest/api-surface.md` — understand the node schema.
4. **Read** the ComfyUI V3 API skills in the companion workspace `comfyui-custom-node-skills/plugins/comfyui-custom-nodes/skills/` — understand the API surface.
5. **Then** read source files as needed.

### Companion Workspace: ComfyUI Custom Node Skills

The multi-root workspace includes `comfyui-custom-node-skills`, which contains comprehensive V3 API documentation and reference implementations. Key resources:

| Resource | Path (relative to skills workspace root) | Use For |
|----------|------------------------------------------|---------|
| Node Basics Skill | `plugins/comfyui-custom-nodes/skills/comfyui-node-basics/SKILL.md` | V3 node class structure |
| Node Outputs Skill | `plugins/comfyui-custom-nodes/skills/comfyui-node-outputs/SKILL.md` | Data + UI output patterns, PreviewText |
| Node Inputs Skill | `plugins/comfyui-custom-nodes/skills/comfyui-node-inputs/SKILL.md` | Input definitions |
| Node Packaging Skill | `plugins/comfyui-custom-nodes/skills/comfyui-node-packaging/SKILL.md` | pyproject.toml, registration |
| Node Lifecycle Skill | `plugins/comfyui-custom-nodes/skills/comfyui-node-lifecycle/SKILL.md` | Caching, execution behavior, `not_idempotent` |
| Reference Implementation | `skill_test_nodes/` | Working V3 node examples |

---

## 2. Documentation Maintenance Rules

When making changes to the codebase, update the corresponding documentation:

| Change Made | Documents to Update |
|---|---|
| Node inputs/outputs modified | `docs/agents/project-manifest/api-surface.md`, `README.md` |
| File added or renamed | `docs/agents/project-manifest/file-tree.md`, active `plan.md` (if one exists) |
| Node behavior changed | `docs/agents/project-manifest/api-surface.md`, `docs/agents/project-manifest/data-flows.md`, `README.md` |
| Dependencies added | `pyproject.toml`, `docs/agents/project-manifest/tech-stack.md`, `README.md` |
| New plan created | `docs/agents/plans/` (new plan directory) |
| Project specification created or updated | `docs/agents/projects/` |
| Constraints or conventions changed | `docs/agents/project-manifest/constraints.md` |
| Author prefix or node category finalised | `docs/agents/project-manifest/constraints.md`, `docs/agents/project-manifest/api-surface.md` |

---

## 3. Efficiency Rules — Search Smart

- **Finding files?** Check `file-tree.md` FIRST.
- **Understanding node behavior or design intent?** Check `api-surface.md` and `constraints.md` FIRST.
- **Understanding V3 API patterns?** Check the skills in `comfyui-custom-node-skills` FIRST.
- **Understanding registration / packaging?** Check `comfyui-node-packaging` skill FIRST.
- **Understanding caching and idempotency?** Check `comfyui-node-lifecycle` skill FIRST.
- **Only then** read source files.

---

## 4. Failure Protocol & Decision Matrix

| Scenario | Action | Priority |
|---|---|---|
| Ambiguous requirement | Consult `constraints.md` for intent; use most restrictive interpretation | MUST |
| Documentation/code conflict | Trust the manifest (`constraints.md`, `api-surface.md`), flag code for fix | MUST |
| Missing documentation | Flag gap, do not invent facts | MUST |
| Unsure about V3 API usage | Consult the skills in `comfyui-custom-node-skills`; check `skill_test_nodes/` for working examples | MUST |
| V3 API pattern not covered by skills | Check ComfyUI source if accessible; flag gap in skills workspace | SHOULD |
| Untested code path | Proceed with caution, add manual test recommendation | SHOULD |
| Tempted to add features beyond the agreed node set | Do not. Confirm scope with the user; update `docs/agents/projects/` before implementing | MUST |
| Node outputs non-reproducible results (`randomized=True`) | Verify `fingerprint_inputs()` returns `time.time()` for that case; do not use `not_idempotent=True` | MUST |

---

## 5. Project Stats

| Property | Value |
|---|---|
| **Language** | Python 3.10+ |
| **Architecture** | ComfyUI V3 custom nodes for random number generation, registered as a single extension |
| **API** | ComfyUI V3 (`comfy_api.latest`) — no V1 fallback |
| **Package Manager** | pip (installed via ComfyUI `custom_nodes/`) |
| **Build Tool** | None (pure Python) |
| **Test Framework** | Mock-based unit tests (`verify_*.py`) + manual testing in ComfyUI |
| **External Dependencies** | None (stdlib + ComfyUI builtins only) |
| **License** | MIT |

---

## 6. Project File Layout

```
comfyui-random-nodes/
  __init__.py           # Extension registration: RandomNodesExtension + comfy_entrypoint()
  nodes.py              # RandomIntNode, RandomFloatNode, RandomFloatFromPresetNode + module-level helpers
  pyproject.toml        # Package metadata (name, version, license, ComfyUI entry point)
  README.md             # User-facing documentation
  LICENSE               # MIT license
  AGENTS.md             # This file
  CLAUDE.md             # Claude companion (imports AGENTS.md)
  changelog.md          # Project changelog
  js/
    random_nodes.js      # Frontend extension: buttons + widget synchronization
  tests/
    verify_random_int.py                 # Mock-based unit tests for RandomIntNode
    verify_random_float.py               # Mock-based unit tests for RandomFloatNode
    verify_random_float_from_preset.py   # Mock-based unit tests for RandomFloatFromPresetNode
  docs/
    agents/
      project-manifest/ # Structured codebase overview for AI agents
        README.md       #   Manifest index
        api-surface.md  #   Node class schemas and method signatures
        constraints.md  #   Design rules and conventions
        data-flows.md   #   Execution paths through the nodes
        file-tree.md    #   Directory structure
        tech-stack.md   #   Runtime, dependencies, architecture
      plans/            # Implementation plans
      projects/         # Project specifications
```

---

## 7. Key Design Decisions

These decisions are documented in `constraints.md` and are **not negotiable** without explicit user approval:

- **V3 API only** — no V1 compatibility layer.
- **No external dependencies** — stdlib (`random`, `math`, etc.) and ComfyUI builtins only.
- **`randomized` boolean toggle, no seed input** — a socketless `randomized` boolean controls generation: `True` generates a new value, `False` returns the stored `value` widget value. Any future seed support must be a new, separate node variant (e.g. `Mistralys_SeededRandomInt`), never a seed input on the existing nodes.
- **Conditional `fingerprint_inputs` caching** — `fingerprint_inputs()` returns `time.time()` when `randomized=True` (forces re-execution) and a deterministic fingerprint when `randomized=False` (allows caching). `not_idempotent=True` is not used.
- **Author prefix `Mistralys_`** — all node IDs use this prefix (e.g. `Mistralys_RandomInt`).
- **Node category `random`** — all nodes share this flat category string.
- **Two-tier testing** — every node ships with a `verify_*.py` mock-based unit test **and** is validated inside a live ComfyUI instance.
