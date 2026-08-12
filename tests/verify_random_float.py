"""Mock-based verification script for RandomFloatNode acceptance criteria."""
import os
import sys
from unittest.mock import MagicMock


class _io:
    class Schema:
        def __init__(self, *, node_id, display_name, category, inputs=None, outputs=None,
                     is_output_node=False, not_idempotent=False):
            self.node_id = node_id
            self.display_name = display_name
            self.category = category
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

N = nd.RandomFloatNode

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


# AC-09: node_id and category
schema = N.define_schema()
assert schema.node_id == 'Mistralys_RandomFloat', schema.node_id
assert schema.category == 'random', schema.category
ok("AC-09: node_id='Mistralys_RandomFloat', category='random'")

# AC-02: _generate_random_float respects bounds, precision, and swaps inverted ranges
for _ in range(50):
    v = nd._generate_random_float(1.0, 2.0, 3, 0.0)
    assert 1.0 <= v <= 2.0, v
    assert len(str(v).split('.')[-1]) <= 3, v
v = nd._generate_random_float(2.0, 1.0, 2, 0.0)
assert 1.0 <= v <= 2.0, v
ok("_generate_random_float: respects bounds, precision, swaps inverted ranges")

# _snap_to_step: correct snapping and edge cases
assert nd._snap_to_step(1.23, 1.0, 2.0, 0.0) == 1.23, "step=0 should pass through"
snapped = nd._snap_to_step(1.24, 1.0, 2.0, 0.25)
assert snapped == 1.25, snapped
snapped_high_clamp = nd._snap_to_step(1.99, 1.0, 2.0, 3.0)
assert snapped_high_clamp <= 2.0, snapped_high_clamp
ok("_snap_to_step: snaps to grid, passes through when step=0, clamps to high")

# AC-02: execute with randomized=True returns value with correct precision and step alignment
result = N.execute(range_from=0.0, range_to=1.0, precision=2, step=0.25, value=0.0, randomized=True)
value = result.values[0]
assert 0.0 <= value <= 1.0, value
remainder = round((value - 0.0) / 0.25)
assert abs(value - remainder * 0.25) < 1e-9, value
assert result.ui is not None and result.ui.text == str(value)
ok("AC-02: execute(randomized=True) returns value within range, step-aligned, with PreviewText ui")

# AC-02: execute with randomized=False returns stored value (rounded to precision)
result = N.execute(range_from=0.0, range_to=1.0, precision=2, step=0.0, value=0.12345, randomized=False)
assert result.values[0] == 0.12, result.values
ok("AC-02: execute(randomized=False) returns stored value rounded to precision")

# AC-03: passthrough outputs match inputs
result = N.execute(range_from=2.0, range_to=8.0, precision=3, step=0.5, value=0.0, randomized=False)
assert result.values[1] == 2.0 and result.values[2] == 8.0, result.values
assert result.values[3] == 3 and result.values[4] == 0.5, result.values
ok("AC-03: passthrough outputs (range_from, range_to, precision, step) match inputs")

# AC-04: fingerprint_inputs conditional behavior
fp_random = N.fingerprint_inputs(range_from=0.0, range_to=1.0, precision=2, step=0.0, value=0.0, randomized=True)
assert isinstance(fp_random, float), type(fp_random)
fp1 = N.fingerprint_inputs(range_from=0.0, range_to=1.0, precision=2, step=0.0, value=0.5, randomized=False)
fp2 = N.fingerprint_inputs(range_from=0.0, range_to=1.0, precision=2, step=0.0, value=0.5, randomized=False)
assert fp1 == fp2, (fp1, fp2)
fp3 = N.fingerprint_inputs(range_from=0.0, range_to=1.0, precision=2, step=0.0, value=0.6, randomized=False)
assert fp3 != fp1, (fp1, fp3)
ok("AC-04: fingerprint_inputs returns time when randomized, deterministic string otherwise")

# AC-05: validate_inputs rejects precision < 1, accepts valid params
assert N.validate_inputs(precision=0) != True
assert N.validate_inputs(precision=1) is True
ok("AC-05: validate_inputs rejects precision < 1, accepts valid params")

# AC-05: equal range returns the single possible value
result = N.execute(range_from=3.5, range_to=3.5, precision=2, step=0.0, value=0.0, randomized=True)
assert result.values[0] == 3.5, result.values
ok("AC-05: execute with equal range returns the single possible value")

print(f"\nResult: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
