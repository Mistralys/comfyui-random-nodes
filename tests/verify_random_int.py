"""Mock-based verification script for RandomIntNode acceptance criteria."""
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

N = nd.RandomIntNode

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
assert schema.node_id == 'Mistralys_RandomInt', schema.node_id
assert schema.category == 'random', schema.category
assert schema.description, 'description must be set'
assert schema.search_aliases, 'search_aliases must be set'
ok("AC-09: node_id='Mistralys_RandomInt', category='random'")

# AC-01: _generate_random_int respects bounds and swaps inverted ranges
for _ in range(50):
    v = nd._generate_random_int(1, 5)
    assert 1 <= v <= 5, v
v = nd._generate_random_int(5, 1)
assert 1 <= v <= 5, v
ok("_generate_random_int: respects bounds, swaps inverted ranges")

# AC-01: execute with randomized=True returns value in range
result = N.execute(range_from=1, range_to=5, value=0, randomized=True)
assert 1 <= result.values[0] <= 5, result.values
assert result.ui is not None and result.ui.text == str(result.values[0])
ok("AC-01: execute(randomized=True) returns value within range and PreviewText ui")

# AC-01: execute with randomized=False returns stored value
result = N.execute(range_from=1, range_to=5, value=42, randomized=False)
assert result.values[0] == 42, result.values
ok("AC-01: execute(randomized=False) returns stored value")

# AC-03: passthrough outputs match inputs
result = N.execute(range_from=3, range_to=9, value=0, randomized=False)
assert result.values[1] == 3 and result.values[2] == 9, result.values
ok("AC-03: passthrough outputs (range_from, range_to) match inputs")

# AC-04: fingerprint_inputs
fp_random = N.fingerprint_inputs(range_from=1, range_to=5, value=0, randomized=True)
assert isinstance(fp_random, float), type(fp_random)
fp1 = N.fingerprint_inputs(range_from=1, range_to=5, value=7, randomized=False)
fp2 = N.fingerprint_inputs(range_from=1, range_to=5, value=7, randomized=False)
assert fp1 == fp2, (fp1, fp2)
fp3 = N.fingerprint_inputs(range_from=1, range_to=5, value=8, randomized=False)
assert fp3 != fp1, (fp1, fp3)
ok("AC-04: fingerprint_inputs returns time when randomized, deterministic string otherwise")

# AC-05: equal range returns the single possible value
result = N.execute(range_from=4, range_to=4, value=0, randomized=True)
assert result.values[0] == 4, result.values
ok("AC-05: execute with equal range returns the single possible value")

print(f"\nResult: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
