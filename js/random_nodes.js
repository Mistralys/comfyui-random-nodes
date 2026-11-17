import { app } from "../../scripts/app.js";

const RANDOM_INT_NODE = "Mistralys_RandomInt";
const RANDOM_FLOAT_NODE = "Mistralys_RandomFloat";
const RANDOM_FLOAT_FROM_PRESET_NODE = "Mistralys_RandomFloatFromPreset";

function findWidget(node, name) {
    return node.widgets?.find((w) => w.name === name);
}

function parsePresets(str) {
    const values = (str || "")
        .split(",")
        .map((part) => parseFloat(part.trim()))
        .filter((n) => !Number.isNaN(n));
    return [...new Set(values)].sort((a, b) => a - b);
}

function generateClientRandomInt(node) {
    const low = findWidget(node, "range_from").value;
    const high = findWidget(node, "range_to").value;
    const from = Math.min(low, high);
    const to = Math.max(low, high);
    return Math.floor(Math.random() * (to - from + 1)) + from;
}

function generateClientRandomFloat(node) {
    const low = findWidget(node, "range_from").value;
    const high = findWidget(node, "range_to").value;
    const precision = findWidget(node, "precision").value;
    const from = Math.min(low, high);
    const to = Math.max(low, high);
    const raw = Math.random() * (to - from) + from;
    return parseFloat(raw.toFixed(precision));
}

function updateUseCurrentLabel(node, value) {
    const button = node._useCurrentButton;
    if (button) {
        button.name = `Use current: ${value}`;
    }
}

function setupRandomNode(node, generateFn) {
    const valueWidget = findWidget(node, "value");
    const randomizedWidget = findWidget(node, "randomized");
    node._lastGeneratedValue = valueWidget.value;

    node.addWidget("button", "New random value", null, () => {
        const generated = generateFn(node);
        valueWidget.value = generated;
        randomizedWidget.value = false;
        node._lastGeneratedValue = generated;
        updateUseCurrentLabel(node, generated);
    });

    node._useCurrentButton = node.addWidget(
        "button",
        `Use current: ${node._lastGeneratedValue}`,
        null,
        () => {
            valueWidget.value = node._lastGeneratedValue;
            randomizedWidget.value = false;
        }
    );
}

function setupPresetNode(node) {
    const presetsWidget = findWidget(node, "presets");
    const valueWidget = findWidget(node, "value");
    const modeWidget = findWidget(node, "mode");

    function currentPresets() {
        return parsePresets(presetsWidget.value);
    }

    function updatePresetUseCurrentLabel(value) {
        const button = node._useCurrentButton;
        if (button) {
            button.name = `Use current: ${value}`;
        }
    }

    const initialPresets = currentPresets();
    if (initialPresets.length > 0) {
        valueWidget.value = initialPresets[0];
    }
    node._lastGeneratedValue = valueWidget.value;

    node._presetComboWidget = node.addWidget(
        "combo",
        "preset",
        initialPresets.length > 0 ? String(initialPresets[0]) : "",
        (value) => {
            valueWidget.value = parseFloat(value);
            modeWidget.value = "fixed";
        },
        { values: initialPresets.map((v) => String(v)) }
    );

    node.addWidget("button", "New random value", null, () => {
        const presets = currentPresets();
        if (presets.length === 0) {
            return;
        }
        const generated = presets[Math.floor(Math.random() * presets.length)];
        valueWidget.value = generated;
        modeWidget.value = "fixed";
        node._lastGeneratedValue = generated;
        updatePresetUseCurrentLabel(generated);
    });

    node._useCurrentButton = node.addWidget(
        "button",
        `Use current: ${node._lastGeneratedValue}`,
        null,
        () => {
            valueWidget.value = node._lastGeneratedValue;
            modeWidget.value = "fixed";
        }
    );

    const origCallback = presetsWidget.callback;
    presetsWidget.callback = function (value) {
        origCallback?.apply(this, arguments);
        const presets = currentPresets();
        if (node._presetComboWidget) {
            node._presetComboWidget.options.values = presets.map((v) => String(v));
        }
        if (presets.length > 0) {
            valueWidget.value = presets[0];
        }
    };
}

app.registerExtension({
    name: "mistralys.random_nodes",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === RANDOM_INT_NODE) {
            const origOnCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                origOnCreated?.apply(this, arguments);
                setupRandomNode(this, generateClientRandomInt);
            };
        } else if (nodeData.name === RANDOM_FLOAT_NODE) {
            const origOnCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                origOnCreated?.apply(this, arguments);
                setupRandomNode(this, generateClientRandomFloat);
            };
        } else if (nodeData.name === RANDOM_FLOAT_FROM_PRESET_NODE) {
            const origOnCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                origOnCreated?.apply(this, arguments);
                setupPresetNode(this);
            };
        }
    },

    nodeCreated(node) {
        if (
            node.comfyClass !== RANDOM_INT_NODE &&
            node.comfyClass !== RANDOM_FLOAT_NODE &&
            node.comfyClass !== RANDOM_FLOAT_FROM_PRESET_NODE
        ) {
            return;
        }

        if (node.comfyClass === RANDOM_FLOAT_FROM_PRESET_NODE) {
            node.onExecuted = function (output) {
                const text = output?.text?.[0];
                if (text === undefined) {
                    return;
                }
                const valueWidget = findWidget(this, "value");
                const cycleIndexWidget = findWidget(this, "cycle_index");
                const button = this._useCurrentButton;

                if (text.includes("|")) {
                    const [rawValue, rawNextIndex] = text.split("|");
                    const value = parseFloat(rawValue);
                    const nextIndex = parseInt(rawNextIndex, 10);
                    if (Number.isNaN(value) || Number.isNaN(nextIndex)) {
                        return;
                    }
                    if (valueWidget) {
                        valueWidget.value = value;
                    }
                    if (cycleIndexWidget) {
                        cycleIndexWidget.value = nextIndex;
                    }
                    this._lastGeneratedValue = value;
                    const total = parsePresets(findWidget(this, "presets").value).length;
                    if (button && total > 0) {
                        const position = ((nextIndex - 1 + total) % total) + 1;
                        button.name = `Use current: ${value} (${position}/${total})`;
                    }
                } else {
                    const value = parseFloat(text);
                    if (Number.isNaN(value)) {
                        return;
                    }
                    if (valueWidget) {
                        valueWidget.value = value;
                    }
                    this._lastGeneratedValue = value;
                    if (button) {
                        button.name = `Use current: ${value}`;
                    }
                }
            };
            return;
        }

        const isInt = node.comfyClass === RANDOM_INT_NODE;
        node.onExecuted = function (output) {
            const text = output?.text?.[0];
            if (text === undefined) {
                return;
            }
            const parsed = isInt ? parseInt(text, 10) : parseFloat(text);
            if (Number.isNaN(parsed)) {
                return;
            }
            const valueWidget = findWidget(this, "value");
            if (valueWidget) {
                valueWidget.value = parsed;
            }
            this._lastGeneratedValue = parsed;
            updateUseCurrentLabel(this, parsed);
        };
    },
});
