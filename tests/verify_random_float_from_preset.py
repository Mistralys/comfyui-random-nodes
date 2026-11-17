"""Mock-based verification script for RandomFloatFromPresetNode acceptance criteria."""
import os
import sys
from unittest.mock import MagicMock


class _io:
    class Schema:
        def __init__(self, *, node_id, display_name, category, inputs=None, outputs=None,
                     is_output_node=False, not_idempotent=False,
                     description=None, search_aliases=None):
            self.node_id = node_id
            self.display_name = display_name
            self.category = category
            self.description = description
            self.search_aliases = search_aliases or []
            self.inputs = inputs or []
            self.outputs = outputs or []

    class Int:
        @staticmethod
        def Input(p, **kw): return dict(__ii__=True, param=p, **kw)
        @staticmethod
        def Output(l, **kw): return dict(__io__=True, label=l, **kw)

    class Float:
        @staticmethod
        def Input(p, **kw): return dict(__fi__=True, param=p, **kw)
        @staticmethod
        def Output(l, **kw): return dict(__fo__=True, label=l, **kw)

    class Boolean:
        @staticmethod
        def Input(p, **kw): return dict(__bi__=True, param=p, **kw)
        @staticmethod
        def Output(l, **kw): return dict(__bo__=True, label=l, **kw)

    class String:
        @staticmethod
        def Input(p, **kw): return dict(__si__=True, param=p, **kw)
        @staticmethod
        def Output(l, **kw): return dict(__so__=True, label=l, **kw)

    class Combo:
        @staticmethod
        def Input(p, **kw): return dict(__ci__=True, param=p, **kw)
        @staticmethod
        def Output(l, **kw): return dict(__co__=True, label=l, **kw)

    class NodeOutput:
        def __init__(self, *a, ui=None):
            self.values = a
            self.ui = ui

    class ComfyNode:
        pass


class _PreviewText:
    def __init__(self, text):
        self.text = text


class _ui:
    PreviewText = _PreviewText


cm = MagicMock()
cm.latest.io = _io
cm.latest.ui = _ui
cm.latest.ComfyExtension = object
sys.modules['comfy_api'] = cm
sys.modules['comfy_api.latest'] = cm.latest
sys.modules['typing_extensions'] = MagicMock()

repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo)
import nodes as nd

N = nd.RandomFloatFromPresetNode

passed = 0
failed = 0


def ok(name):
    global passed
    passed += 1
    print(f"  PASS: {name}")


def fail(name, msg):
    global failed
    failed += 1
    print(f"  FAIL: {name} -- {msg}")


# AC-01: node_id, display_name, category
schema = N.define_schema()
assert schema.node_id == 'Mistralys_RandomFloatFromPreset', schema.node_id
assert schema.category == 'random', schema.category
assert schema.description, 'description must be set'
assert schema.search_aliases, 'search_aliases must be set'
ok("AC-01: node_id='Mistralys_RandomFloatFromPreset', category='random'")

# AC-02: _parse_presets returns sorted unique floats from comma-separated input
values = nd._parse_presets("3.2, 4.2, 4.8, 5.2")
assert values == [3.2, 4.2, 4.8, 5.2], values
ok("AC-02: _parse_presets returns sorted unique floats")

# AC-06: _parse_presets handles whitespace, duplicates, invalid entries, empty string
values = nd._parse_presets(" 2.0 , 2.0, abc, 1.0,, 3.0 ")
assert values == [1.0, 2.0, 3.0], values
assert nd._parse_presets("") == []
assert nd._parse_presets("abc, def") == []
ok("AC-06: _parse_presets handles whitespace, duplicates, invalid entries, empty string")

# AC-03: execute with mode="random" returns a member of the parsed presets
presets_str = "1.0, 2.0, 3.0"
for _ in range(20):
    result = N.execute(presets=presets_str, value=0.0, mode="random", cycle_index=0)
    assert result.values[0] in nd._parse_presets(presets_str), result.values
    assert result.values[1] == presets_str, result.values
ok("AC-03: execute(mode='random') returns a member of the parsed presets")

# AC-03: execute with mode="random" returns PreviewText UI output with value only
result = N.execute(presets=presets_str, value=0.0, mode="random", cycle_index=0)
assert result.ui is not None and "|" not in result.ui.text
assert result.ui.text == str(result.values[0])
ok("AC-03: execute(mode='random') returns PreviewText UI output with value only")

# AC-04 / AC-04a: execute with mode="fixed" returns stored value and passes through cycle_index/presets
result = N.execute(presets=presets_str, value=2.5, mode="fixed", cycle_index=7)
assert result.values[0] == 2.5, result.values
assert result.values[1] == presets_str, result.values
assert result.values[2] == 7, result.values
ok("AC-04/AC-04a: execute(mode='fixed') returns stored value, passes through presets and cycle_index")

# AC-05: execute with mode="cycle" returns presets[cycle_index % len] and includes "value|next_index"
result = N.execute(presets=presets_str, value=0.0, mode="cycle", cycle_index=1)
assert result.values[0] == 2.0, result.values
assert result.values[2] == 1, result.values
assert result.ui.text == "2.0|2", result.ui.text
ok("AC-05: execute(mode='cycle') returns presets[cycle_index % len] with 'value|next_index' PreviewText")

# AC-05a: execute with mode="cycle" wraps cycle_index correctly
result = N.execute(presets=presets_str, value=0.0, mode="cycle", cycle_index=3)
assert result.values[0] == 1.0, result.values
assert result.values[2] == 0, result.values
assert result.ui.text == "1.0|1", result.ui.text
ok("AC-05a: execute(mode='cycle') wraps cycle_index correctly")

# AC-06: validate_inputs rejects empty/invalid presets, accepts valid presets
assert N.validate_inputs(presets="") != True
assert N.validate_inputs(presets="abc, def") != True
assert N.validate_inputs(presets="1.0, 2.0") is True
ok("AC-06: validate_inputs rejects empty/invalid presets, accepts valid presets")

# AC-07: fingerprint_inputs returns deterministic string for mode="fixed", time.time() otherwise
fp1 = N.fingerprint_inputs(presets=presets_str, value=1.0, mode="fixed", cycle_index=0)
fp2 = N.fingerprint_inputs(presets=presets_str, value=1.0, mode="fixed", cycle_index=0)
assert fp1 == fp2, (fp1, fp2)
fp3 = N.fingerprint_inputs(presets=presets_str, value=2.0, mode="fixed", cycle_index=0)
assert fp3 != fp1, (fp1, fp3)
fp_random = N.fingerprint_inputs(presets=presets_str, value=1.0, mode="random", cycle_index=0)
assert isinstance(fp_random, float), type(fp_random)
fp_cycle = N.fingerprint_inputs(presets=presets_str, value=1.0, mode="cycle", cycle_index=0)
assert isinstance(fp_cycle, float), type(fp_cycle)
ok("AC-07: fingerprint_inputs deterministic for 'fixed', time.time() for 'random'/'cycle'")

print(f"\nResult: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
