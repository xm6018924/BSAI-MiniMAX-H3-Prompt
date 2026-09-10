// BSAI H3 Direct Prompt (直通模式独立节点)
// 与模板节点完全分离，互不干扰。
// 功能：纯文本直通输出 + 语音输入 + 本地LLM扩写
import { app } from "../../../scripts/app.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";

// ── CSS for direct prompt node ──
const _css2 = `
.bsai-direct-wrap { padding: 10px; color: #ddd; font-family: system-ui, sans-serif; }
.bsai-direct-title { font-size: 14px; font-weight: 600; margin-bottom: 8px; color: #fff; }
.bsai-direct-sub { font-size: 11px; color: #888; margin-bottom: 8px; }
.bsai-direct-ta {
  width: 100%; min-height: 300px; background: #1a1a1a; color: #ddd;
  border: 1px solid #444; border-radius: 4px; padding: 8px;
  font-family: monospace; font-size: 12px; resize: vertical; box-sizing: border-box;
}
.bsai-direct-tools { display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap; }
.bsai-direct-btn {
  padding: 6px 12px; background: #2a6e3f; color: #fff; border: none;
  border-radius: 4px; cursor: pointer; font-size: 12px;
}
.bsai-direct-btn:hover { background: #3a8e5f; }
.bsai-direct-btn.secondary { background: #3a3a3a; }
.bsai-direct-btn.secondary:hover { background: #555; }
.bsai-direct-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.bsai-direct-status {
  margin-top: 6px; padding: 6px 8px; font-size: 11px;
  background: #2a2a2a; border-radius: 4px; color: #aaa;
  min-height: 16px;
}
.bsai-direct-status.ok { background: #1a3a1a; color: #8f8; }
.bsai-direct-status.warn { background: #3a2a1a; color: #fa5; }
.bsai-direct-cust-row { display: flex; gap: 6px; margin-top: 8px; align-items: center; }
.bsai-direct-cust-row label { font-size: 11px; color: #aaa; white-space: nowrap; }
.bsai-direct-cust-input {
  flex: 1; background: #1a1a1a; color: #ddd; border: 1px solid #444;
  border-radius: 4px; padding: 4px 6px; font-size: 12px;
}
`;

function _addCss2() {
    if (document.getElementById("bsai-direct-css")) return;
    const s = document.createElement("style");
    s.id = "bsai-direct-css";
    s.textContent = _css2;
    document.head.appendChild(s);
}

function findWidget(node, name) {
    if (!node.widgets) return null;
    for (let i = 0; i < node.widgets.length; i++) {
        if (node.widgets[i].name === name) return node.widgets[i];
    }
    return null;
}

function setWidgetText(node, name, text) {
    const w = findWidget(node, name);
    if (!w) return false;
    w.value = text;
    if (typeof w.callback === "function") { try { w.callback(text); } catch (e) {} }
    return true;
}

function buildDirectUI(node) {
    if (node._bsaiDirectReady) return;
    node._bsaiDirectReady = true;

    _addCss2();

    // Hide the raw widgets — we'll use our own UI
    const promptW = findWidget(node, "prompt");
    const custW = findWidget(node, "user_customization");
    const narrW = findWidget(node, "narration");

    if (promptW) { promptW.type = "hidden"; promptW.computeSize = function() { return [0, 0]; }; }
    if (custW) { custW.type = "hidden"; custW.computeSize = function() { return [0, 0]; }; }
    if (narrW) { narrW.type = "hidden"; narrW.computeSize = function() { return [0, 0]; }; }

    const container = document.createElement("div");
    container.className = "bsai-direct-wrap";

    // Title
    const title = document.createElement("div");
    title.className = "bsai-direct-title";
    title.textContent = "⚡ 直通模式 / Direct Mode";
    container.appendChild(title);

    const sub = document.createElement("div");
    sub.className = "bsai-direct-sub";
    sub.textContent = "直接输出 H3 提示词到下游 / Output H3 prompt directly to downstream nodes";
    container.appendChild(sub);

    // Main textarea
    const ta = document.createElement("textarea");
    ta.className = "bsai-direct-ta";
    ta.placeholder = "在此输入或粘贴完整的 H3 提示词...\nEnter or paste your complete H3 prompt here...";
    ta.value = promptW ? (promptW.value || "") : "";
    ta.addEventListener("input", function() {
        setWidgetText(node, "prompt", ta.value);
        if (node.graph) node.graph.setDirtyCanvas && node.graph.setDirtyCanvas(true, true);
    });
    container.appendChild(ta);
    node._bsaiDirectTa = ta;

    // Customization row
    const custRow = document.createElement("div");
    custRow.className = "bsai-direct-cust-row";
    const custLbl = document.createElement("label");
    custLbl.textContent = "自定义修改 / Customize:";
    const custInput = document.createElement("input");
    custInput.className = "bsai-direct-cust-input";
    custInput.type = "text";
    custInput.placeholder = "可选：自定义修改（如 加一点微笑、穿红色衣服 等）";
    custInput.value = custW ? (custW.value || "") : "";
    custInput.addEventListener("input", function() {
        setWidgetText(node, "user_customization", custInput.value);
        if (node.graph) node.graph.setDirtyCanvas && node.graph.setDirtyCanvas(true, true);
    });
    custRow.appendChild(custLbl);
    custRow.appendChild(custInput);
    container.appendChild(custRow);

    // Tool buttons
    const tools = document.createElement("div");
    tools.className = "bsai-direct-tools";

    // Voice button (reuse voice module from prompt_template.js if available)
    const voiceBtn = document.createElement("button");
    voiceBtn.className = "bsai-direct-btn";
    voiceBtn.textContent = "🎤 语音输入";
    voiceBtn.title = "麦克风语音输入（本地离线识别）";
    voiceBtn.onclick = function() {
        // The voice module is in prompt_template.js as global _voice
        // We open a simple voice dialog
        _openVoiceDialog(node, ta);
    };
    tools.appendChild(voiceBtn);

    // Expand to H3 button
    const expandBtn = document.createElement("button");
    expandBtn.className = "bsai-direct-btn secondary";
    expandBtn.textContent = "✨ 扩写为 H3 三段式";
    expandBtn.title = "用本地LLM将简短描述扩写为完整 H3 提示词";
    expandBtn.onclick = function() {
        const text = ta.value.trim();
        if (!text) { _setStatus("请先输入文字 / Please enter text first", "warn"); return; }
        _setStatus("⏳ 正在扩写… / Expanding…", "");
        expandBtn.disabled = true;
        fetch("/bsai_h3/skill_three", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: text }),
        }).then(function(r) { return r.json().catch(function() { return {}; }); })
        .then(function(j) {
            const out = (j && j.ok && j.prompt) ? j.prompt : "";
            if (out) {
                ta.value = out;
                setWidgetText(node, "prompt", out);
                _setStatus("✅ 已生成 H3 三段式提示词 / H3 3-part prompt generated", "ok");
            } else {
                _setStatus("⚠️ 生成失败，请检查网络或LLM配置 / Generation failed", "warn");
            }
        }).catch(function() {
            _setStatus("⚠️ 网络错误 / Network error", "warn");
        }).then(function() {
            expandBtn.disabled = false;
            if (node.graph) node.graph.setDirtyCanvas && node.graph.setDirtyCanvas(true, true);
        });
    };
    tools.appendChild(expandBtn);

    // Clear button
    const clearBtn = document.createElement("button");
    clearBtn.className = "bsai-direct-btn secondary";
    clearBtn.textContent = "🗑 清空";
    clearBtn.onclick = function() {
        ta.value = "";
        custInput.value = "";
        setWidgetText(node, "prompt", "");
        setWidgetText(node, "user_customization", "");
        _setStatus("已清空 / Cleared", "");
        if (node.graph) node.graph.setDirtyCanvas && node.graph.setDirtyCanvas(true, true);
    };
    tools.appendChild(clearBtn);

    container.appendChild(tools);

    // Status bar
    const status = document.createElement("div");
    status.className = "bsai-direct-status";
    status.textContent = "就绪 / Ready";
    container.appendChild(status);
    node._bsaiDirectStatus = status;

    function _setStatus(msg, type) {
        status.textContent = msg;
        status.className = "bsai-direct-status" + (type ? " " + type : "");
    }

    // Add as DOM widget
    const w = node.addDOMWidget("bsai_direct_ui", "bsai_direct_ui", container, function() {}, {});
    w.computeSize = function() { return [420, 400]; };

    // Update size after layout
    setTimeout(function() {
        if (node.setSize) node.setSize([440, 450]);
        if (node.graph && node.graph.setDirtyCanvas) node.graph.setDirtyCanvas(true, true);
    }, 50);
}

// ── Simple voice dialog for direct node ──
// Reuses the ASR endpoint from the template node
function _openVoiceDialog(node, ta) {
    if (typeof window._bsaiVoiceDialog === "function") {
        // Use the shared voice dialog from prompt_template.js if available
        window._bsaiVoiceDialog(node, function(text) {
            ta.value = text;
            setWidgetText(node, "prompt", text);
            if (node.graph) node.graph.setDirtyCanvas && node.graph.setDirtyCanvas(true, true);
        });
        return;
    }
    // Fallback: simple alert
    alert("语音输入功能需要模板节点的语音模块。\n请先在工作流中添加一个 BSAI H3 Prompt Template 节点以启用语音功能。\n\nVoice input requires the template node's voice module.\nAdd a BSAI H3 Prompt Template node to your workflow first to enable voice.");
}

app.registerExtension({
    name: "bsai.h3.direct",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "BSAI_H3_DirectPrompt") return;

        const origCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function() {
            if (origCreated) origCreated.apply(this, arguments);
            const node = this;
            setTimeout(function() {
                try {
                    buildDirectUI(node);
                } catch (e) {
                    console.error("[BSAI H3 DirectPrompt] buildDirectUI failed:", e);
                }
            }, 50);
        };

        const origConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function(data) {
            if (origConfigure) origConfigure.apply(this, arguments);
            const node = this;
            if (node._bsaiDirectReady) {
                setTimeout(function() {
                    const pw = findWidget(node, "prompt");
                    if (pw && node._bsaiDirectTa) {
                        node._bsaiDirectTa.value = pw.value || "";
                    }
                    const cw = findWidget(node, "user_customization");
                    if (cw && node._bsaiDirectCustInput) {
                        // find the cust input in the DOM
                        const inputs = node._bsaiDirectTa.parentElement.querySelectorAll(".bsai-direct-cust-input");
                        if (inputs[0]) inputs[0].value = cw.value || "";
                    }
                }, 100);
            }
        };

        // Ensure minimum node width
        const origComputeSize = nodeType.prototype.computeSize;
        nodeType.prototype.computeSize = function() {
            const orig = origComputeSize ? origComputeSize.apply(this, arguments) : [200, 100];
            if (orig[0] < 420) orig[0] = 420;
            return orig;
        };
    },
});
