import { app } from "../../scripts/app.js";

const RANDOM_INT_NODE = "Mistralys_RandomInt";
const RANDOM_FLOAT_NODE = "Mistralys_RandomFloat";

function findWidget(node, name) {
    return node.widgets?.find((w) => w.name === name);
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
        }
    },

    nodeCreated(node) {
        if (node.comfyClass !== RANDOM_INT_NODE && node.comfyClass !== RANDOM_FLOAT_NODE) {
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
