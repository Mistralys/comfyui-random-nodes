import random
import time
from comfy_api.latest import io, ui


def _generate_random_int(low, high):
    """Generate a random integer in [low, high], swapping bounds if inverted."""
    if low > high:
        low, high = high, low
    return random.randint(low, high)


def _snap_to_step(value, low, high, step):
    """Snap value to the nearest step grid point anchored at low, clamped to high."""
    if step <= 0:
        return value
    snapped = low + round((value - low) / step) * step
    return min(snapped, high)


def _generate_random_float(low, high, precision, step):
    """Generate a random float in [low, high], apply step snapping, and round to precision."""
    if low > high:
        low, high = high, low
    value = random.uniform(low, high)
    value = _snap_to_step(value, low, high, step)
    return round(value, precision)


class RandomIntNode(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="Mistralys_RandomInt",
            display_name="Random Int",
            category="random",
            inputs=[
                io.Int.Input("range_from", default=0,
                    tooltip="Minimum integer value to generate.",
                ),
                io.Int.Input("range_to", default=1,
                    tooltip="Maximum integer value to generate.",
                ),
                io.Int.Input("value", default=0, socketless=True,
                    tooltip="The randomized value. Reused when 'randomized' is off.",
                ),
                io.Boolean.Input("randomized", default=False, socketless=True,
                    tooltip="Whether to generate a new random value on the next run.",
                ),
            ],
            outputs=[
                io.Int.Output("VALUE",
                    tooltip="The generated (or stored) integer value.",
                ),
                io.Int.Output("RANGE_FROM",
                    tooltip="Passthrough of the input value.",
                ),
                io.Int.Output("RANGE_TO",
                    tooltip="Passthrough of the input value.",
                ),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, range_from, range_to, value, randomized):
        if randomized:
            return time.time()
        return f"{value}"

    @classmethod
    def execute(cls, range_from, range_to, value, randomized):
        if randomized:
            result = _generate_random_int(range_from, range_to)
            return io.NodeOutput(result, range_from, range_to, ui=ui.PreviewText(str(result)))
        return io.NodeOutput(value, range_from, range_to)


class RandomFloatNode(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="Mistralys_RandomFloat",
            display_name="Random Float",
            category="random",
            inputs=[
                io.Float.Input("range_from", default=0.0,
                    tooltip="Minimum float value to generate.",
                ),
                io.Float.Input("range_to", default=1.0,
                    tooltip="Maximum float value to generate.",
                ),
                io.Int.Input("precision", default=2, min=1,
                    tooltip="Number of decimal places.",
                ),
                io.Float.Input("step", default=0.0, min=0.0,
                    tooltip="Snap generated values to this step grid. 0.0 means no stepping.",
                ),
                io.Float.Input("value", default=0.0, socketless=True,
                    tooltip="The randomized value. Reused when 'randomized' is off.",
                ),
                io.Boolean.Input("randomized", default=False, socketless=True,
                    tooltip="Whether to generate a new random value on the next run.",
                ),
            ],
            outputs=[
                io.Float.Output("VALUE",
                    tooltip="The generated (or stored) float value.",
                ),
                io.Float.Output("RANGE_FROM",
                    tooltip="Passthrough of the input value.",
                ),
                io.Float.Output("RANGE_TO",
                    tooltip="Passthrough of the input value.",
                ),
                io.Int.Output("PRECISION",
                    tooltip="Passthrough of the input value.",
                ),
                io.Float.Output("STEP",
                    tooltip="Passthrough of the input value.",
                ),
            ],
        )

    @classmethod
    def validate_inputs(cls, precision):
        if precision < 1:
            return "precision must be at least 1"
        return True

    @classmethod
    def fingerprint_inputs(cls, range_from, range_to, precision, step, value, randomized):
        if randomized:
            return time.time()
        return f"{value}"

    @classmethod
    def execute(cls, range_from, range_to, precision, step, value, randomized):
        if randomized:
            result = _generate_random_float(range_from, range_to, precision, step)
            return io.NodeOutput(result, range_from, range_to, precision, step, ui=ui.PreviewText(str(result)))
        return io.NodeOutput(round(value, precision), range_from, range_to, precision, step)
