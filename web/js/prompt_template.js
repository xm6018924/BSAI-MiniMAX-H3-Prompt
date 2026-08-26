/**
 * BSAI H3 Prompt Template - Visual Template Browser Extension
 *
 * Features:
 * - Search by keyword across all templates
 * - Three-level cascading selection: Category > Subcategory > Template
 * - GIF preview area on the right side
 * - Solid background (no transparency / no canvas bleed-through)
 * - Custom user_customization textarea integrated into the DOM widget
 */

import { app } from "../../../scripts/app.js";

const PREVIEW_BASE = "/extensions/BSAI-MiniMAX-H3-Prompt/previews/";
const DATA_URL = "/extensions/BSAI-MiniMAX-H3-Prompt/templates_data.json";

// ── CSS ──
const STYLE_ID = "bsai-h3-tpl-css";
if (!document.getElementById(STYLE_ID)) {
    const st = document.createElement("style");
    st.id = STYLE_ID;
    st.textContent = `
.bsai-tpl-wrap {
    display: flex; flex-direction: column; gap: 6px;
    padding: 8px; background: #1a1a1a !important;
    width: 100%; box-sizing: border-box; font-family: sans-serif;
}
.bsai-tpl-top {
    display: flex; gap: 8px; align-items: flex-start;
}
.bsai-tpl-left {
    flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 5px;
}
.bsai-tpl-right {
    width: 180px; flex-shrink: 0; display: flex; flex-direction: column; gap: 3px;
}
/* Search box */
.bsai-tpl-search-row {
    display: flex; gap: 5px; align-items: center;
    background: #222; border: 1px solid #444; border-radius: 4px; padding: 2px 6px;
}
.bsai-tpl-search-icon {
    font-size: 12px; color: #668; flex-shrink: 0;
}
.bsai-tpl-search-input {
    flex: 1; background: transparent; border: none; color: #ddd;
    font-size: 12px; outline: none; min-width: 0; padding: 4px 0;
}
.bsai-tpl-search-input::placeholder { color: #444; }
.bsai-tpl-search-clr {
    font-size: 14px; color: #666; cursor: pointer; flex-shrink: 0;
    display: none; line-height: 1;
}
.bsai-tpl-search-clr:hover { color: #a66; }
.bsai-tpl-search-result-path {
    font-size: 9px; color: #5688aa; margin-top: 2px;
}
/* Dropdowns */
.bsai-tpl-dd-row {
    display: flex; gap: 5px; align-items: center;
}
.bsai-tpl-dd-lbl {
    font-size: 11px; color: #88a; min-width: 80px; text-align: right;
    white-space: nowrap;
}
.bsai-tpl-dd {
    flex: 1; background: #2a2a2a; color: #ddd; border: 1px solid #444;
    border-radius: 4px; padding: 4px 6px; font-size: 12px;
    cursor: pointer; outline: none; min-width: 0; max-width: 100%;
}
.bsai-tpl-dd:hover { border-color: #5a8; }
.bsai-tpl-dd:focus { border-color: #3f789e; box-shadow: 0 0 4px rgba(63,120,158,0.3); }
.bsai-tpl-dd:disabled { opacity: 0.4; cursor: not-allowed; }
/* Template list */
.bsai-tpl-list {
    border: 1px solid #333; border-radius: 4px; max-height: 200px;
    overflow-y: auto; background: #111; min-height: 40px;
}
.bsai-tpl-list::-webkit-scrollbar { width: 5px; }
.bsai-tpl-list::-webkit-scrollbar-track { background: #1a1a1a; }
.bsai-tpl-list::-webkit-scrollbar-thumb { background: #444; border-radius: 3px; }
.bsai-tpl-item {
    padding: 6px 10px; border-bottom: 1px solid #222; cursor: pointer;
    transition: background 0.12s; user-select: none;
}
.bsai-tpl-item:last-child { border-bottom: none; }
.bsai-tpl-item:hover { background: #2a3a4a; }
.bsai-tpl-item.active {
    background: #2a4a6a; border-left: 3px solid #3f789e;
}
.bsai-tpl-item-nm { font-size: 12px; color: #cde; font-weight: 600; }
.bsai-tpl-item-ds { font-size: 10px; color: #777; margin-top: 2px; line-height: 1.3; }
.bsai-tpl-tags { display: flex; flex-wrap: wrap; gap: 3px; margin-top: 3px; }
.bsai-tpl-tag {
    font-size: 9px; background: #2a2a2a; color: #668;
    padding: 1px 5px; border-radius: 8px; border: 1px solid #333;
}
/* Preview */
.bsai-tpl-prev-box {
    width: 180px; height: 180px; border: 1px solid #333;
    border-radius: 4px; background: #0a0a0a; overflow: hidden;
    display: flex; align-items: center; justify-content: center;
}
.bsai-tpl-prev-img { max-width: 100%; max-height: 100%; object-fit: contain; }
.bsai-tpl-prev-ph { color: #444; font-size: 11px; text-align: center; padding: 16px; }
.bsai-tpl-prev-nm { font-size: 11px; color: #8cf; font-weight: 600; text-align: center; line-height: 1.3; }
.bsai-tpl-prev-md { font-size: 10px; color: #668; text-align: center; }
.bsai-tpl-prev-dur { font-size: 10px; color: #686; text-align: center; }
/* Info bar */
.bsai-tpl-bar {
    display: flex; gap: 8px; justify-content: space-between;
    align-items: center; padding: 2px 0;
}
.bsai-tpl-cnt { font-size: 10px; color: #556; }
.bsai-tpl-clr {
    font-size: 10px; color: #a66; cursor: pointer;
    padding: 2px 8px; border: 1px solid #433; border-radius: 3px; background: #2a1a1a;
}
.bsai-tpl-clr:hover { background: #3a2a2a; color: #c88; }
.bsai-tpl-empty { padding: 16px; text-align: center; color: #444; font-size: 11px; }
/* Multi-select: selection stack */
.bsai-tpl-sel { display: flex; flex-wrap: wrap; gap: 4px; min-height: 0; padding: 2px 0; }
.bsai-tpl-sel-empty { font-size: 10px; color: #556; padding: 2px 0; line-height: 1.3; }
.bsai-tpl-chip {
    display: inline-flex; align-items: center; gap: 4px;
    background: #2a4a3a; border: 1px solid #3a6a4a; color: #9d9;
    font-size: 10px; padding: 2px 7px; border-radius: 10px; line-height: 1.2;
}
.bsai-tpl-chip.primary { background: #2a4a6a; border-color: #3f789e; color: #9cf; }
.bsai-tpl-chip .ord { color: #8d8; font-weight: 700; }
.bsai-tpl-chip .x { cursor: pointer; color: #a88; font-weight: 700; padding: 0 2px; }
.bsai-tpl-chip .x:hover { color: #f88; }
.bsai-tpl-item.sel { background: #2a4a3a; border-left: 3px solid #5a8; }
.bsai-tpl-item.sel:hover { background: #2a5a4a; }
.bsai-tpl-item.sel.primary { background: #2a4a6a; border-left: 3px solid #3f789e; }
.bsai-tpl-ord-badge {
    display: inline-block; min-width: 15px; text-align: center;
    background: #5a8; color: #000; font-size: 9px; font-weight: 700;
    border-radius: 8px; padding: 0 3px; margin-right: 4px; line-height: 1.4;
}
.bsai-tpl-sel-hint { font-size: 9px; color: #446; padding: 0 2px; }
/* Multi-select mode switch */
.bsai-tpl-mode {
    display: flex; align-items: center; gap: 6px;
    font-size: 11px; color: #88a; padding: 2px 2px; user-select: none; cursor: pointer;
}
.bsai-tpl-mode input { cursor: pointer; accent-color: #3f789e; margin: 0; }
.bsai-tpl-mode .mode-tag { font-size: 9px; padding: 1px 6px; border-radius: 8px; border: 1px solid #335; color: #678; }
.bsai-tpl-mode .mode-tag.on { background: #2a4a3a; color: #9d9; border-color: #3a6a4a; }
.bsai-tpl-mode .mode-tag.off { background: #2a2a2a; color: #889; border-color: #444; }
/* Voice input button */
.bsai-tpl-voice-btn {
    margin-left: 6px; cursor: pointer; font-size: 13px; line-height: 1;
    padding: 3px 8px; border-radius: 6px; border: 1px solid #335;
    background: #222; color: #9bd; white-space: nowrap; user-select: none; flex: 0 0 auto;
}
.bsai-tpl-voice-btn:hover { background: #2a3a4a; border-color: #4a7a9a; }
/* Voice modal */
.bsai-voice-overlay {
    position: fixed; inset: 0; background: rgba(0,0,0,0.55); z-index: 99999;
    display: flex; align-items: center; justify-content: center;
}
.bsai-voice-card {
    width: 460px; max-width: 92vw; background: #1b1b1b; color: #ddd;
    border: 1px solid #334; border-radius: 12px; padding: 16px 18px;
    font-size: 13px; box-shadow: 0 8px 32px rgba(0,0,0,0.6);
}
.bsai-voice-title { font-size: 15px; font-weight: 700; margin-bottom: 10px; color: #9bd; }
.bsai-voice-status { font-size: 12px; color: #889; margin: 6px 0; min-height: 16px; }
.bsai-voice-status.rec { color: #e77; }
.bsai-voice-status.ok { color: #7d7; }
.bsai-voice-ta {
    width: 100%; min-height: 60px; box-sizing: border-box; background: #111; color: #ddd;
    border: 1px solid #334; border-radius: 8px; padding: 8px; font-size: 13px;
    resize: vertical; margin: 8px 0;
}
.bsai-voice-btns { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
.bsai-voice-btn {
    cursor: pointer; padding: 6px 12px; border-radius: 8px; border: 1px solid #446;
    background: #223; color: #cde; font-size: 13px;
}
.bsai-voice-btn:hover { background: #2a3a4a; }
.bsai-voice-btn.primary { background: #2a4a3a; border-color: #3a7a5a; color: #cfc; }
.bsai-voice-btn.danger { background: #4a2a2a; border-color: #7a3a3a; color: #fbb; }
.bsai-voice-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.bsai-voice-direct { margin-top: 8px; border-top: 1px solid #334; padding-top: 8px; }
.bsai-voice-chk { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #cde; cursor: pointer; flex-wrap: wrap; }
.bsai-voice-chk input { cursor: pointer; }
.bsai-voice-hint { font-size: 11px; color: #889; }
.bsai-voice-drow { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
/* Customization textarea */
.bsai-tpl-cust { margin-top: 6px; }
.bsai-tpl-cust-lbl { font-size: 11px; color: #88a; margin-bottom: 3px; }
.bsai-tpl-cust-ta {
    width: 100%; min-height: 40px; max-height: 100px; resize: vertical;
    background: #222; color: #ddd; border: 1px solid #444;
    border-radius: 4px; padding: 4px 6px; font-size: 11px;
    font-family: monospace; box-sizing: border-box; outline: none;
}
.bsai-tpl-cust-ta:focus { border-color: #3f789e; }
.bsai-tpl-cust-ta::placeholder { color: #444; }
`;
    document.head.appendChild(st);
}

// ── Template data cache ──
let _tplData = null;

async function loadTemplateData() {
    if (_tplData) return _tplData;
    try {
        const resp = await fetch(DATA_URL);
        if (resp.ok) {
            _tplData = await resp.json();
            return _tplData;
        }
    } catch (e) {
        console.warn("[BSAI H3 Template] Failed to load template data:", e);
    }
    return null;
}

function findWidget(node, name) {
    if (!node.widgets) return null;
    for (let i = 0; i < node.widgets.length; i++) {
        if (node.widgets[i].name === name) return node.widgets[i];
    }
    return null;
}

function hideWidget(node, name) {
    const w = findWidget(node, name);
    if (!w) return;
    w.type = "hidden";
    w._bsaiHidden = true;
    w.computeSize = function() { return [0, 0]; };
    if (w.draw) w.draw = function() {};
    if (w.drawWidget) w.drawWidget = function() {};
    if (w.mouse) w.mouse = null;
    const els = [w.element, w.inputEl, w.labelEl, w.wrapper, w.container, w.domNode];
    els.forEach(function(el) {
        if (el && el.style) {
            el.style.display = "none";
            el.style.height = "0";
            el.style.overflow = "hidden";
        }
    });
    if (w.element && w.element.parentElement) {
        const parent = w.element.parentElement;
        if (parent && (parent.classList.contains("widget") || parent.classList.contains("widget-wrapper"))) {
            parent.style.display = "none";
            parent.style.height = "0";
            parent.style.overflow = "hidden";
        }
    }
}

// ── Search across all templates ──
function searchTemplates(keyword) {
    if (!_tplData) return [];
    const kw = keyword.toLowerCase().trim();
    if (!kw) return [];
    const results = [];
    (_tplData.categories || []).forEach(function(cat) {
        (cat.subcategories || []).forEach(function(sub) {
            (sub.templates || []).forEach(function(tpl) {
                const haystack = [
                    tpl.name, tpl.name_en, tpl.description,
                    cat.name, cat.name_en, sub.name, sub.name_en,
                    (tpl.tags || []).join(" "),
                ].join(" ").toLowerCase();
                if (haystack.indexOf(kw) >= 0) {
                    results.push({ cat: cat, sub: sub, tpl: tpl });
                }
            });
        });
    });
    return results;
}

// ── Build UI ──

function buildTemplateUI(node) {
    if (node._bsaiTplReady) return;
    node._bsaiTplReady = true;

    hideWidget(node, "template_select");
    hideWidget(node, "user_customization");
    hideWidget(node, "direct_prompt");

    const container = document.createElement("div");
    container.className = "bsai-tpl-wrap";

    // ── Search row ──
    const searchRow = document.createElement("div");
    searchRow.className = "bsai-tpl-search-row";
    const searchIcon = document.createElement("span");
    searchIcon.className = "bsai-tpl-search-icon";
    searchIcon.textContent = "🔍";
    const searchInput = document.createElement("input");
    searchInput.className = "bsai-tpl-search-input";
    searchInput.type = "text";
    searchInput.placeholder = "搜索模板 / Search templates...";
    const searchClr = document.createElement("span");
    searchClr.className = "bsai-tpl-search-clr";
    searchClr.textContent = "✕";
    const voiceBtn = document.createElement("span");
    voiceBtn.className = "bsai-tpl-voice-btn";
    voiceBtn.textContent = "🎤 语音 / Voice";
    voiceBtn.title = "语音输入指令（覆盖模板动作）/ Voice input command (overrides template action)";
    voiceBtn.onclick = function() { openVoiceModal(node); };
    searchRow.appendChild(searchIcon);
    searchRow.appendChild(searchInput);
    searchRow.appendChild(searchClr);
    searchRow.appendChild(voiceBtn);
    container.appendChild(searchRow);

    // ── Top section: dropdowns + list (left) | preview (right) ──
    const topDiv = document.createElement("div");
    topDiv.className = "bsai-tpl-top";

    const left = document.createElement("div");
    left.className = "bsai-tpl-left";

    // Category dropdown
    const catRow = document.createElement("div");
    catRow.className = "bsai-tpl-dd-row";
    const catLbl = document.createElement("span");
    catLbl.className = "bsai-tpl-dd-lbl";
    catLbl.textContent = "分类 / Category";
    const catSel = document.createElement("select");
    catSel.className = "bsai-tpl-dd";
    catSel.innerHTML = '<option value="">— 选择分类 / Select —</option>';
    catRow.appendChild(catLbl);
    catRow.appendChild(catSel);
    left.appendChild(catRow);

    // Subcategory dropdown
    const subRow = document.createElement("div");
    subRow.className = "bsai-tpl-dd-row";
    const subLbl = document.createElement("span");
    subLbl.className = "bsai-tpl-dd-lbl";
    subLbl.textContent = "子类 / Subcategory";
    const subSel = document.createElement("select");
    subSel.className = "bsai-tpl-dd";
    subSel.innerHTML = '<option value="">— 选择子类 / Select —</option>';
    subSel.disabled = true;
    subRow.appendChild(subLbl);
    subRow.appendChild(subSel);
    left.appendChild(subRow);

    // Info bar
    const bar = document.createElement("div");
    bar.className = "bsai-tpl-bar";
    const cntSpan = document.createElement("span");
    cntSpan.className = "bsai-tpl-cnt";
    cntSpan.textContent = "";
    const clrBtn = document.createElement("span");
    clrBtn.className = "bsai-tpl-clr";
    clrBtn.textContent = "✕ 清除 / Clear";
    clrBtn.style.display = "none";
    bar.appendChild(cntSpan);
    bar.appendChild(clrBtn);
    left.appendChild(bar);

    // Selection stack bar (multi-select)
    const selBar = document.createElement("div");
    selBar.className = "bsai-tpl-sel";
    selBar.innerHTML = '<div class="bsai-tpl-sel-empty">点击模板单选 / Click a template to select (single-select)</div>';
    left.appendChild(selBar);

    // Mode switch: Single (default) / Multi-Stack
    const modeRow = document.createElement("label");
    modeRow.className = "bsai-tpl-mode";
    modeRow.title = "默认单选：点击模板即选中并预览。开启后为多选叠加：点击多个模板合并为一个提示词 / Default single-select. Enable to stack multiple templates into one prompt.";
    const modeCb = document.createElement("input");
    modeCb.type = "checkbox";
    const modeTxt = document.createElement("span");
    modeTxt.textContent = "多选叠加 / Multi-Stack";
    const modeTag = document.createElement("span");
    modeTag.className = "mode-tag off";
    modeTag.textContent = "OFF · 单选";
    modeRow.appendChild(modeCb);
    modeRow.appendChild(modeTxt);
    modeRow.appendChild(modeTag);
    left.appendChild(modeRow);

    // Template list
    const listDiv = document.createElement("div");
    listDiv.className = "bsai-tpl-list";
    listDiv.innerHTML = '<div class="bsai-tpl-empty">请先选择分类 / Select a category first</div>';
    left.appendChild(listDiv);

    // Right panel - preview
    const right = document.createElement("div");
    right.className = "bsai-tpl-right";
    const prevBox = document.createElement("div");
    prevBox.className = "bsai-tpl-prev-box";
    prevBox.innerHTML = '<div class="bsai-tpl-prev-ph">选择模板后显示预览<br>Preview after selection</div>';
    right.appendChild(prevBox);
    const prevNm = document.createElement("div");
    prevNm.className = "bsai-tpl-prev-nm";
    right.appendChild(prevNm);
    const prevMd = document.createElement("div");
    prevMd.className = "bsai-tpl-prev-md";
    right.appendChild(prevMd);
    const prevDur = document.createElement("div");
    prevDur.className = "bsai-tpl-prev-dur";
    right.appendChild(prevDur);

    topDiv.appendChild(left);
    topDiv.appendChild(right);
    container.appendChild(topDiv);

    // Customization textarea
    const custDiv = document.createElement("div");
    custDiv.className = "bsai-tpl-cust";
    const custLbl = document.createElement("div");
    custLbl.className = "bsai-tpl-cust-lbl";
    custLbl.textContent = "补充修改 / Customization (Optional):";
    const custTa = document.createElement("textarea");
    custTa.className = "bsai-tpl-cust-ta";
    custTa.placeholder = "在此添加对模板的修改描述，如更换角色、场景等 / Add custom modifications here, e.g. change character, scene...";
    custDiv.appendChild(custLbl);
    custDiv.appendChild(custTa);
    container.appendChild(custDiv);

    // Store refs
    node._bsaiCat = catSel;
    node._bsaiSub = subSel;
    node._bsaiList = listDiv;
    node._bsaiPrevBox = prevBox;
    node._bsaiPrevNm = prevNm;
    node._bsaiPrevMd = prevMd;
    node._bsaiPrevDur = prevDur;
    node._bsaiClr = clrBtn;
    node._bsaiCnt = cntSpan;
    node._bsaiCustTa = custTa;
    node._bsaiSearchInput = searchInput;
    node._bsaiSearchClr = searchClr;
    node._bsaiTopDiv = topDiv;
    node._bsaiSelBar = selBar;
    node._bsaiSelection = [];
    node._bsaiMultiMode = false;  // default: single-select
    node._bsaiModeCb = modeCb;
    node._bsaiModeTag = modeTag;

    // Mode switch handler: single (default) <-> multi-stack
    modeCb.addEventListener("change", function() {
        node._bsaiMultiMode = modeCb.checked;
        if (!node._bsaiMultiMode && node._bsaiSelection.length > 1) {
            // back to single: keep only the base (first) template
            node._bsaiSelection = node._bsaiSelection.slice(0, 1);
        }
        syncModeUI(node);
        syncSelectionUI(node);
    });

    // Register as DOM widget
    if (typeof node.addDOMWidget === "function") {
        const dw = node.addDOMWidget("bsai_tpl_ui", "html", container, {
            getValue: function() { return ""; },
            setValue: function() {},
        });
        if (dw) {
            dw.options = dw.options || {};
            dw.options.minHeight = 300;
            // Report the real content size so LiteGraph grows the node to fit the whole UI
            dw.computeSize = function() {
                const w = Math.min(Math.max(container.scrollWidth || 440, 440), 640);
                return [w, Math.max(container.scrollHeight || 360, 300)];
            };
        }

        // Force the node to resize so the solid background fully covers the UI
        function refreshNodeSize() {
            if (!node) return;
            const h = Math.max(300, (container.scrollHeight || 360));
            if (node.size) {
                node.setSize([node.size[0], h]);
                if (node.graph) node.setDirtyCanvas(true, true);
            }
        }
        node._bsaiRefreshSize = refreshNodeSize;

        // Re-measure after layout settles
        setTimeout(refreshNodeSize, 80);
        // Re-measure when the user resizes the customization textarea
        custTa.addEventListener("resize", refreshNodeSize);
    } else {
        console.warn("[BSAI H3 Template] addDOMWidget not available");
    }

    // ── Sync customization textarea ──
    const custWidget = findWidget(node, "user_customization");
    custTa.addEventListener("input", function() {
        if (custWidget) {
            custWidget.value = custTa.value;
            if (node.graph) node.setDirtyCanvas(true, true);
        }
    });
    if (custWidget && custWidget.value) {
        custTa.value = custWidget.value;
    }

    // ── Search handler ──
    let searchTimer = null;
    searchInput.addEventListener("input", function() {
        const kw = searchInput.value.trim();
        searchClr.style.display = kw ? "block" : "none";

        if (searchTimer) clearTimeout(searchTimer);
        searchTimer = setTimeout(function() {
            if (!kw) {
                // Exit search mode — restore normal category view
                node._bsaiSearchMode = false;
                // If a category was selected, restore its template list
                if (catSel.value && subSel.value) {
                    catSel.onchange();
                    subSel.onchange();
                } else {
                    listDiv.innerHTML = '<div class="bsai-tpl-empty">请先选择分类 / Select a category first</div>';
                    cntSpan.textContent = "";
                    clrBtn.style.display = "none";
                }
                return;
            }
            // Enter search mode
            node._bsaiSearchMode = true;
            const results = searchTemplates(kw);
            renderSearchResults(node, results, listDiv, cntSpan, clrBtn);
        }, 200);
    });

    searchClr.onclick = function() {
        searchInput.value = "";
        searchClr.style.display = "none";
        searchInput.dispatchEvent(new Event("input"));
    };

    // ── Dropdown handlers ──
    catSel.onchange = function() {
        // If in search mode, exit it
        if (node._bsaiSearchMode) {
            searchInput.value = "";
            searchClr.style.display = "none";
            node._bsaiSearchMode = false;
        }
        const catId = catSel.value;
        subSel.innerHTML = '<option value="">— 选择子类 / Select —</option>';
        subSel.disabled = true;
        listDiv.innerHTML = '<div class="bsai-tpl-empty">请选择子类 / Select a subcategory</div>';
        cntSpan.textContent = "";
        clrBtn.style.display = "none";
        updatePreview(null, prevBox, prevNm, prevMd, prevDur);
        if (!catId || !_tplData) return;
        const cat = _tplData.categories.find(function(c) { return c.id === catId; });
        if (!cat) return;
        (cat.subcategories || []).forEach(function(sub) {
            const opt = document.createElement("option");
            opt.value = sub.id;
            opt.textContent = sub.name + " (" + sub.name_en + ")";
            subSel.appendChild(opt);
        });
        subSel.disabled = false;
    };

    subSel.onchange = function() {
        if (node._bsaiSearchMode) {
            searchInput.value = "";
            searchClr.style.display = "none";
            node._bsaiSearchMode = false;
        }
        const catId = catSel.value;
        const subId = subSel.value;
        if (!catId || !subId || !_tplData) {
            listDiv.innerHTML = '<div class="bsai-tpl-empty">请选择分类和子类 / Select category & subcategory</div>';
            cntSpan.textContent = "";
            clrBtn.style.display = "none";
            return;
        }
        const cat = _tplData.categories.find(function(c) { return c.id === catId; });
        if (!cat) return;
        const sub = cat.subcategories.find(function(s) { return s.id === subId; });
        if (!sub) return;
        renderTemplateList(node, sub, cat, listDiv);
    };

    clrBtn.onclick = function() {
        catSel.value = "";
        subSel.innerHTML = '<option value="">— 选择子类 / Select —</option>';
        subSel.disabled = true;
        listDiv.innerHTML = '<div class="bsai-tpl-empty">请先选择分类 / Select a category first</div>';
        cntSpan.textContent = "";
        clrBtn.style.display = "none";
        clearSelection(node);
        syncSelectionUI(node);
    };

    // ── Load data ──
    loadTemplateData().then(function(data) {
        if (!data) return;
        catSel.innerHTML = '<option value="">— 选择分类 / Select —</option>';
        (data.categories || []).forEach(function(cat) {
            const opt = document.createElement("option");
            opt.value = cat.id;
            opt.textContent = (cat.icon || "📁") + " " + cat.name + " (" + cat.name_en + ")";
            catSel.appendChild(opt);
        });
        const tplW = findWidget(node, "template_select");
        if (tplW && tplW.value && !tplW.value.startsWith("(")) {
            restoreSelection(node, tplW.value);
        }
        if (node._bsaiRefreshSize) setTimeout(node._bsaiRefreshSize, 120);
    });
}

// ── Render search results ──
function renderSearchResults(node, results, listDiv, cntSpan, clrBtn) {
    listDiv.innerHTML = "";
    cntSpan.textContent = "搜索到 " + results.length + " 个模板 / " + results.length + " results";
    clrBtn.style.display = "";

    if (results.length === 0) {
        listDiv.innerHTML = '<div class="bsai-tpl-empty">未找到匹配的模板 / No matching templates found</div>';
        return;
    }

    results.forEach(function(item) {
        const cat = item.cat, sub = item.sub, tpl = item.tpl;

        const el = document.createElement("div");
        el.className = "bsai-tpl-item";
        el.setAttribute("data-id", tpl.id);
        el.setAttribute("data-name", tpl.name);
        if (isSelected(node, tpl)) {
            el.classList.add("sel");
        }

        const nmDiv = document.createElement("div");
        nmDiv.className = "bsai-tpl-item-nm";
        nmDiv.textContent = tpl.name + " | " + tpl.name_en;
        el.appendChild(nmDiv);

        // Show category path in search results
        const pathDiv = document.createElement("div");
        pathDiv.className = "bsai-tpl-search-result-path";
        pathDiv.textContent = cat.name + " > " + sub.name + " | " + cat.name_en + " > " + sub.name_en;
        el.appendChild(pathDiv);

        const dsDiv = document.createElement("div");
        dsDiv.className = "bsai-tpl-item-ds";
        dsDiv.textContent = tpl.description || "";
        el.appendChild(dsDiv);

        if (tpl.tags && tpl.tags.length) {
            const tagsDiv = document.createElement("div");
            tagsDiv.className = "bsai-tpl-tags";
            tpl.tags.slice(0, 6).forEach(function(tag) {
                const tagSpan = document.createElement("span");
                tagSpan.className = "bsai-tpl-tag";
                tagSpan.textContent = tag;
                tagsDiv.appendChild(tagSpan);
            });
            el.appendChild(tagsDiv);
        }

        el.onclick = function() {
            toggleSelection(node, cat, sub, tpl);
            // Sync dropdowns to reflect the clicked template's category/subcategory
            node._bsaiCat.value = cat.id;
            // Populate subcategories for this category
            node._bsaiSub.innerHTML = '<option value="">— 选择子类 —</option>';
            (cat.subcategories || []).forEach(function(s) {
                const opt = document.createElement("option");
                opt.value = s.id;
                opt.textContent = s.name + " (" + s.name_en + ")";
                if (s.id === sub.id) opt.selected = true;
                node._bsaiSub.appendChild(opt);
            });
            node._bsaiSub.disabled = false;
        };

        listDiv.appendChild(el);
    });
    if (node._bsaiRefreshSize) setTimeout(node._bsaiRefreshSize, 30);
}

// ── Render template list (normal mode) ──
function renderTemplateList(node, sub, cat, listDiv) {
    const templates = sub.templates || [];
    listDiv.innerHTML = "";
    node._bsaiCnt.textContent = "共 " + templates.length + " 个模板 / " + templates.length + " templates";
    node._bsaiClr.style.display = "";

    if (templates.length === 0) {
        listDiv.innerHTML = '<div class="bsai-tpl-empty">该子类暂无模板 / No templates in this subcategory</div>';
        return;
    }

    templates.forEach(function(tpl) {
        const item = document.createElement("div");
        item.className = "bsai-tpl-item";
        item.setAttribute("data-id", tpl.id);
        item.setAttribute("data-name", tpl.name);
        if (isSelected(node, tpl)) {
            item.classList.add("sel");
        }

        const nmDiv = document.createElement("div");
        nmDiv.className = "bsai-tpl-item-nm";
        nmDiv.textContent = tpl.name + " | " + tpl.name_en;
        item.appendChild(nmDiv);

        const dsDiv = document.createElement("div");
        dsDiv.className = "bsai-tpl-item-ds";
        dsDiv.textContent = tpl.description || "";
        item.appendChild(dsDiv);

        if (tpl.tags && tpl.tags.length) {
            const tagsDiv = document.createElement("div");
            tagsDiv.className = "bsai-tpl-tags";
            tpl.tags.slice(0, 6).forEach(function(tag) {
                const tagSpan = document.createElement("span");
                tagSpan.className = "bsai-tpl-tag";
                tagSpan.textContent = tag;
                tagsDiv.appendChild(tagSpan);
            });
            item.appendChild(tagsDiv);
        }

        item.onclick = function() {
            toggleSelection(node, cat, sub, tpl);
        };

        listDiv.appendChild(item);
    });
    if (node._bsaiRefreshSize) setTimeout(node._bsaiRefreshSize, 30);
}

// ── Multi-select: selection stack ──
const MAX_SELECT = 5;

function syncModeUI(node) {
    const multi = !!node._bsaiMultiMode;
    if (node._bsaiModeCb) node._bsaiModeCb.checked = multi;
    if (node._bsaiModeTag) {
        node._bsaiModeTag.className = "mode-tag " + (multi ? "on" : "off");
        node._bsaiModeTag.textContent = multi ? "ON · 多选叠加" : "OFF · 单选";
    }
}

function isSelected(node, tpl) {
    return (node._bsaiSelection || []).some(function(it) { return it.tpl.id === tpl.id; });
}

function toggleSelection(node, cat, sub, tpl) {
    if (!node._bsaiSelection) node._bsaiSelection = [];
    if (!node._bsaiMultiMode) {
        // Single-select (default): replace the selection with this template and preview it
        node._bsaiSelection = [{ cat: cat, sub: sub, tpl: tpl }];
        syncSelectionUI(node);
        return;
    }
    // Multi-select: toggle add / remove
    const idx = node._bsaiSelection.findIndex(function(it) { return it.tpl.id === tpl.id; });
    if (idx >= 0) {
        node._bsaiSelection.splice(idx, 1);  // remove
    } else {
        if (node._bsaiSelection.length >= MAX_SELECT) return;  // cap
        node._bsaiSelection.push({ cat: cat, sub: sub, tpl: tpl });  // append -> insertion order
    }
    syncSelectionUI(node);
}

function syncSelectionUI(node) {
    let sel = node._bsaiSelection || [];
    // Single-select (default) never keeps more than one template
    if (!node._bsaiMultiMode && sel.length > 1) {
        sel = sel.slice(0, 1);
        node._bsaiSelection = sel;
    }
    const selBar = node._bsaiSelBar;
    const tplW = findWidget(node, "template_select");

    // Hidden widget value: labels joined by "|||"
    if (tplW) {
        if (sel.length === 0) {
            tplW.value = "(None / 自定义 / Custom)";
        } else {
            tplW.value = sel.map(function(it) {
                return it.cat.name + " > " + it.sub.name + " > " + it.tpl.name;
            }).join(" ||| ");
        }
    }

    // Selection bar (chips)
    if (selBar) {
        selBar.innerHTML = "";
        if (sel.length === 0) {
            const h = document.createElement("div");
            h.className = "bsai-tpl-sel-empty";
            h.textContent = node._bsaiMultiMode
                ? "多选模式：点击模板叠加（第1个为主体）/ Multi: click to stack (1st = base)"
                : "点击模板单选并预览 / Click a template to select & preview";
            selBar.appendChild(h);
        } else {
            sel.forEach(function(it, i) {
                const chip = document.createElement("span");
                chip.className = "bsai-tpl-chip" + (i === 0 ? " primary" : "");
                const ord = document.createElement("span");
                ord.className = "ord";
                ord.textContent = (i + 1);
                const nm = document.createElement("span");
                nm.textContent = it.tpl.name + " | " + (it.tpl.name_en || "");
                const x = document.createElement("span");
                x.className = "x";
                x.textContent = "×";
                x.title = "移除 / Remove";
                x.onclick = function(e) {
                    e.stopPropagation();
                    node._bsaiSelection.splice(i, 1);
                    syncSelectionUI(node);
                };
                chip.appendChild(ord);
                chip.appendChild(nm);
                chip.appendChild(x);
                selBar.appendChild(chip);
            });
        }
    }

    // Mark list items
    (node._bsaiList || []).querySelectorAll ? node._bsaiList.querySelectorAll(".bsai-tpl-item").forEach(function(el) {
        const id = el.getAttribute("data-id");
        el.classList.remove("sel", "primary");
        sel.forEach(function(it, i) {
            if (it.tpl.id === id) {
                el.classList.add("sel");
                if (i === 0) el.classList.add("primary");
            }
        });
    }) : null;

    // Preview: show primary (first selected); name shows combined list
    if (sel.length === 0) {
        updatePreview(null, node._bsaiPrevBox, node._bsaiPrevNm, node._bsaiPrevMd, node._bsaiPrevDur);
    } else {
        const primary = sel[0].tpl;
        updatePreview(primary, node._bsaiPrevBox, node._bsaiPrevNm, node._bsaiPrevMd, node._bsaiPrevDur);
        if (node._bsaiPrevNm) {
            node._bsaiPrevNm.textContent = sel.map(function(it) {
                return it.tpl.name + " | " + (it.tpl.name_en || "");
            }).join("  +  ");
        }
        if (node._bsaiPrevMd && sel.length > 1) {
            node._bsaiPrevMd.textContent = "多模板叠加 Multi-Stack (" + sel.length + ")";
        }
    }

    if (node.graph) node.setDirtyCanvas(true, true);
    if (node._bsaiRefreshSize) setTimeout(node._bsaiRefreshSize, 20);
}

function clearSelection(node) {
    node._bsaiSelection = [];
    syncSelectionUI(node);
}

function updatePreview(tpl, prevBox, prevNm, prevMd, prevDur) {
    if (!tpl) {
        if (prevBox) prevBox.innerHTML = '<div class="bsai-tpl-prev-ph">选择模板后显示预览<br>Preview after selection</div>';
        if (prevNm) prevNm.textContent = "";
        if (prevMd) prevMd.textContent = "";
        if (prevDur) prevDur.textContent = "";
        return;
    }
    if (prevNm) prevNm.textContent = tpl.name + " | " + (tpl.name_en || "");
    if (prevMd) prevMd.textContent = tpl.generation_mode || "";
    if (prevDur) prevDur.textContent = (tpl.duration || 0) + "s | 时长 | 需图片/Image: " + (tpl.needs_image ? "是/Yes" : "否/No");
    if (prevBox) {
        if (tpl.preview) {
            prevBox.innerHTML = '<img class="bsai-tpl-prev-img" src="' + PREVIEW_BASE + tpl.preview + '" alt="preview">';
        } else {
            prevBox.innerHTML = '<div class="bsai-tpl-prev-ph">' +
                '<div style="font-size:22px;margin-bottom:6px;">🎬</div>' +
                '暂无预览动画<br>No preview available<br>' +
                '<span style="font-size:9px;color:#555;">点击选择此模板 / Click to select</span></div>';
        }
    }
}

// ════════════════════════════════════════════════════════════════════════════
//  Voice input: record mic → encode 16k mono WAV → POST /bsai_h3/asr → fill widget
// ════════════════════════════════════════════════════════════════════════════
var _voice = { ctx: null, src: null, proc: null, stream: null, chunks: [], rec: false, rate: 16000 };

function setWidgetText(node, name, text) {
    var w = (node.widgets || []).find(function(x) { return x.name === name; });
    if (!w) return false;
    w.value = text;
    if (typeof w.callback === "function") { try { w.callback(text); } catch (e) {} }
    return true;
}

function openVoiceModal(node) {
    if (!node) return;
    var old = document.querySelector(".bsai-voice-overlay");
    if (old) old.remove();
    var ov = document.createElement("div");
    ov.className = "bsai-voice-overlay";
    ov.innerHTML =
        '<div class="bsai-voice-card">' +
        '<div class="bsai-voice-title">🎤 语音指令 / Voice Command</div>' +
        '<div class="bsai-voice-status">点击"开始录音"，说完后点击"停止并转写" / Click Start, speak, then Stop & Transcribe</div>' +
        '<textarea class="bsai-voice-ta" placeholder="转写结果 / Transcription…"></textarea>' +
        '<div class="bsai-voice-direct">' +
        '  <label class="bsai-voice-chk"><input type="checkbox" data-act="drtgl" /> ⚡ 直通模式 / Direct Mode <span class="bsai-voice-hint">将文字直接扩写为完整 H3 提示词（绕过模板）/ expand into a full H3 prompt, bypassing templates</span></label>' +
        '  <div class="bsai-voice-drow" data-act="drow" style="display:none">' +
        '    <button class="bsai-voice-btn primary" data-act="gen" disabled>⚡ 生成 H3 提示词 / Generate H3</button>' +
        '    <button class="bsai-voice-btn" data-act="direct" disabled>➤ 填入直通输出 / Set as direct_prompt</button>' +
        '  </div>' +
        '</div>' +
        '<div class="bsai-voice-btns">' +
        '  <button class="bsai-voice-btn primary" data-act="rec">● 开始录音 / Start</button>' +
        '  <button class="bsai-voice-btn" data-act="stop" disabled>■ 停止并转写 / Stop & Transcribe</button>' +
        '  <button class="bsai-voice-btn" data-act="ext" disabled>➤ 填入外部提示词（覆盖动作）/ Set as external_prompt</button>' +
        '  <button class="bsai-voice-btn" data-act="cust" disabled>✎ 填入补充修改 / Set as customization</button>' +
        '  <button class="bsai-voice-btn danger" data-act="close">✕ 关闭 / Close</button>' +
        '</div></div>';
    document.body.appendChild(ov);
    var status = ov.querySelector(".bsai-voice-status");
    var ta = ov.querySelector(".bsai-voice-ta");
    var btnRec = ov.querySelector('[data-act="rec"]');
    var btnStop = ov.querySelector('[data-act="stop"]');
    var btnExt = ov.querySelector('[data-act="ext"]');
    var btnCust = ov.querySelector('[data-act="cust"]');
    var chkDirect = ov.querySelector('[data-act="drtgl"]');
    var rowDirect = ov.querySelector('[data-act="drow"]');
    var btnGen = ov.querySelector('[data-act="gen"]');
    var btnDirect = ov.querySelector('[data-act="direct"]');

    function setStatus(txt, cls) {
        status.textContent = txt;
        status.className = "bsai-voice-status" + (cls ? " " + cls : "");
    }
    function enableFill() {
        var has = !!(ta.value && ta.value.trim());
        btnExt.disabled = !has;
        btnCust.disabled = !has;
        btnGen.disabled = !(chkDirect.checked && has);
        btnDirect.disabled = !(chkDirect.checked && has);
    }
    ta.addEventListener("input", enableFill);
    chkDirect.addEventListener("change", function() {
        rowDirect.style.display = chkDirect.checked ? "flex" : "none";
        enableFill();
    });

    // ── Direct mode: expand text into a full H3 prompt via local LLM ──
    btnGen.onclick = function() {
        var txt = (ta.value || "").trim();
        if (!txt) return;
        btnGen.disabled = true;
        var old = ta.value;
        setStatus("⚡ 正在生成 H3 提示词（本地模型，首次约 1 分钟）… / Generating H3 prompt (local LLM, ~1 min first time)…");
        fetch("/bsai_h3/direct", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: txt })
        }).then(function(r) { return r.json(); }).then(function(j) {
            if (j && j.ok && j.prompt) {
                ta.value = j.prompt;
                setStatus("✅ H3 直通提示词已生成，可编辑后填入 / H3 prompt generated — edit, then fill", "ok");
            } else {
                ta.value = old;
                setStatus("生成失败：" + ((j && j.error) || "unknown") + " / Generate failed", "");
            }
            enableFill();
        }).catch(function(e) {
            ta.value = old;
            setStatus("网络错误 / Network error: " + e, "");
            enableFill();
        });
    };
    btnDirect.onclick = function() {
        if (setWidgetText(node, "direct_prompt", ta.value.trim())) {
            node.graph && node.graph.setDirtyCanvas && node.graph.setDirtyCanvas(true, true);
        }
        ov.remove();
    };

    btnRec.onclick = function() {
        if (_voice.rec) return;
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            setStatus("此浏览器不支持麦克风录音 / Microphone not supported (needs HTTPS or localhost)", "");
            return;
        }
        setStatus("请求麦克风权限… / Requesting mic…");
        navigator.mediaDevices.getUserMedia({ audio: true }).then(function(stream) {
            var AC = window.AudioContext || window.webkitAudioContext;
            _voice.ctx = new AC();
            _voice.src = _voice.ctx.createMediaStreamSource(stream);
            _voice.proc = _voice.ctx.createScriptProcessor(4096, 1, 1);
            _voice.chunks = [];
            _voice.stream = stream;
            _voice.rate = _voice.ctx.sampleRate || 48000;
            _voice.proc.onaudioprocess = function(e) {
                if (!_voice.rec) return;
                _voice.chunks.push(new Float32Array(e.inputBuffer.getChannelData(0)));
            };
            _voice.src.connect(_voice.proc);
            _voice.proc.connect(_voice.ctx.destination);
            _voice.rec = true;
            btnRec.disabled = true;
            btnStop.disabled = false;
            setStatus("● 正在录音… 请说话，说完点击「停止并转写」/ Recording… speak now", "rec");
        }).catch(function(err) {
            setStatus("无法访问麦克风：" + (err && err.name ? err.name : err) + " / Mic access denied", "");
        });
    };

    btnStop.onclick = function() {
        if (!_voice.rec) return;
        _voice.rec = false;
        // collect samples
        var total = 0;
        _voice.chunks.forEach(function(a) { total += a.length; });
        var all = new Float32Array(total), off = 0;
        _voice.chunks.forEach(function(a) { all.set(a, off); off += a.length; });
        // cleanup
        try { _voice.proc.disconnect(); } catch (e) {}
        try { _voice.src.disconnect(); } catch (e) {}
        try { _voice.stream.getTracks().forEach(function(t) { t.stop(); }); } catch (e) {}
        try { _voice.ctx.close(); } catch (e) {}
        _voice.proc = _voice.src = _voice.stream = _voice.ctx = null;
        btnRec.disabled = false;
        btnStop.disabled = true;
        if (all.length < 1600) {
            setStatus("录音太短，请重试 / Recording too short", "");
            return;
        }
        setStatus("正在转写… / Transcribing…");
        // downsample to 16k
        var s16 = downsampleTo16k(all, _voice.rate);
        var wav = encodeWavPcm16(s16, 16000);
        fetch("/bsai_h3/asr", { method: "POST", body: wav }).then(function(r) { return r.json(); }).then(function(j) {
            if (j && j.ok) {
                ta.value = j.text || "";
                setStatus("转写完成 / Done", "ok");
            } else {
                setStatus("转写失败：" + ((j && j.error) || "unknown") + " / ASR failed", "");
            }
            enableFill();
        }).catch(function(e) {
            setStatus("网络错误 / Network error: " + e, "");
        });
    };

    btnExt.onclick = function() {
        if (setWidgetText(node, "external_prompt", ta.value.trim())) {
            node.graph && node.graph.setDirtyCanvas && node.graph.setDirtyCanvas(true, true);
        }
        ov.remove();
    };
    btnCust.onclick = function() {
        if (setWidgetText(node, "user_customization", ta.value.trim())) {
            node.graph && node.graph.setDirtyCanvas && node.graph.setDirtyCanvas(true, true);
        }
        ov.remove();
    };
    ov.querySelector('[data-act="close"]').onclick = function() {
        if (_voice.rec) { try { _voice.proc && _voice.proc.disconnect(); } catch (e) {} try { _voice.src && _voice.src.disconnect(); } catch (e) {} try { _voice.stream && _voice.stream.getTracks().forEach(function(t) { t.stop(); }); } catch (e) {} try { _voice.ctx && _voice.ctx.close(); } catch (e) {} _voice.rec = false; }
        ov.remove();
    };
    ov.addEventListener("click", function(e) { if (e.target === ov) { ov.remove(); } });
}

function downsampleTo16k(samples, fromRate) {
    var toRate = 16000;
    if (fromRate === toRate) return samples;
    var n = Math.max(1, Math.floor(samples.length * toRate / fromRate));
    var out = new Float32Array(n);
    for (var i = 0; i < n; i++) {
        var pos = i * fromRate / toRate;
        var j = Math.floor(pos);
        if (j + 1 < samples.length) {
            var f = pos - j;
            out[i] = samples[j] * (1 - f) + samples[j + 1] * f;
        } else {
            out[i] = samples[samples.length - 1] || 0;
        }
    }
    return out;
}

function encodeWavPcm16(samples, sampleRate) {
    var buffer = new ArrayBuffer(44 + samples.length * 2);
    var view = new DataView(buffer);
    function wStr(off, s) { for (var i = 0; i < s.length; i++) view.setUint8(off + i, s.charCodeAt(i)); }
    wStr(0, "RIFF"); view.setUint32(4, 36 + samples.length * 2, true); wStr(8, "WAVE");
    wStr(12, "fmt "); view.setUint32(16, 16, true); view.setUint16(20, 1, true);
    view.setUint16(22, 1, true); view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
    wStr(36, "data"); view.setUint32(40, samples.length * 2, true);
    var off = 44;
    for (var i = 0; i < samples.length; i++) {
        var s = Math.max(-1, Math.min(1, samples[i]));
        view.setInt16(off, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
        off += 2;
    }
    return new Blob([buffer], { type: "audio/wav" });
}

function restoreSelection(node, savedValue) {
    if (!_tplData) return;
    node._bsaiSelection = [];
    const labels = (savedValue || "").split("|||").map(function(s) { return s.trim(); }).filter(function(s) { return s; });
    // Multi-mode is auto-enabled when the saved value contains stacked labels
    const multi = labels.length > 1;
    node._bsaiMultiMode = multi;
    syncModeUI(node);
    let first = null;
    labels.forEach(function(label) {
        const parts = label.split(" > ");
        if (parts.length !== 3) return;
        const catName = parts[0], subName = parts[1], tplName = parts[2];
        const cat = _tplData.categories.find(function(c) { return c.name === catName; });
        if (!cat) return;
        const sub = cat.subcategories.find(function(s) { return s.name === subName; });
        if (!sub) return;
        const tpl = sub.templates.find(function(t) { return t.name === tplName; });
        if (!tpl) return;
        node._bsaiSelection.push({ cat: cat, sub: sub, tpl: tpl });
        if (!first) first = { cat: cat, sub: sub, tpl: tpl };
    });
    // Point the dropdowns at the primary (first) selected template
    if (first) {
        node._bsaiCat.value = first.cat.id;
        node._bsaiCat.onchange();
        node._bsaiSub.value = first.sub.id;
        node._bsaiSub.onchange();
    }
    syncSelectionUI(node);
    if (node._bsaiRefreshSize) setTimeout(node._bsaiRefreshSize, 60);
}

// ── ComfyUI Extension Registration ──

app.registerExtension({
    name: "BSAI.H3.PromptTemplate",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "BSAI_H3_PromptTemplate") return;

        const origCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function() {
            if (origCreated) origCreated.apply(this, arguments);
            const node = this;
            setTimeout(function() { buildTemplateUI(node); }, 50);
        };

        const origConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function(data) {
            if (origConfigure) origConfigure.apply(this, arguments);
            const node = this;
            if (node._bsaiTplReady) {
                setTimeout(function() {
                    const tplW = findWidget(node, "template_select");
                    if (tplW && tplW.value && !tplW.value.startsWith("(")) {
                        loadTemplateData().then(function() {
                            restoreSelection(node, tplW.value);
                        });
                    }
                    const custW = findWidget(node, "user_customization");
                    if (custW && node._bsaiCustTa) {
                        node._bsaiCustTa.value = custW.value || "";
                    }
                }, 100);
            }
        };

        // ── Fix: Draw solid background to prevent canvas bleed-through ──
        const origDrawBG = nodeType.prototype.onDrawBackground;
        nodeType.prototype.onDrawBackground = function(ctx) {
            if (origDrawBG) origDrawBG.apply(this, arguments);
            // Draw solid background filling the entire node body
            ctx.fillStyle = "#1a1a1a";
            ctx.fillRect(0, 0, this.size[0], this.size[1]);
        };

        // Ensure minimum node width
        const origComputeSize = nodeType.prototype.computeSize;
        nodeType.prototype.computeSize = function() {
            const orig = origComputeSize ? origComputeSize.apply(this, arguments) : [200, 100];
            if (orig[0] < 430) orig[0] = 430;
            return orig;
        };

        // Set initial size when added to graph (grow to content height)
        const origAddedToGraph = nodeType.prototype.onAdded;
        nodeType.prototype.onAdded = function() {
            if (origAddedToGraph) origAddedToGraph.apply(this, arguments);
            const node = this;
            setTimeout(function() {
                if (node.setSize) {
                    if (node._bsaiRefreshSize) {
                        node._bsaiRefreshSize();
                    } else {
                        node.setSize([440, 360]);
                    }
                }
            }, 120);
        };
    },
});
