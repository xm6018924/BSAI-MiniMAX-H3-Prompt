// 极简稳定版：避免 OOM，修复 splitDeclarationBlocks
const fs = require('fs');
const path = require('path');

const ROOT = 'C:/BSAI/ComfyUI-BSAI_pro_v39/ComfyUI/custom_nodes/BSAI-MiniMAX-H3-Prompt';
const F_WEB = path.join(ROOT, 'web/templates_data.json');
const F_BACK = path.join(ROOT, 'templates/prompt_templates.json');
const OUT_DIR = path.join(ROOT, '_audit');

const FIELDS_13 = ['id','name','name_en','description','preview','generation_mode','duration','needs_image','needs_video','needs_audio','tags','prompt','text_fallback_mode'];

const ROLE_PATTERNS = {
  '人物':     [/[Pp]erson|[Cc]haracter|人物|^人$|人(?![员])|[Ff]ace|identity|人物铁证|全程同一人|人物参考|人物图|人[物]?/i],
  '服装':     [/[Oo]utfit|[Cc]lothing|[Ww]ardrobe|[Gg]arment|[Dd]ress|[Cc]ostume|服装|衣服|换装|衣/i],
  '场景':     [/[Ss]cene|[Bb]ackground|[Ee]nvironment|[Ss]etting|[Ll]ocation|场景|背景|环境|地点|氛围/i],
  '风格':     [/[Ss]tyle|[Aa]esthetic|风格|画风|滤镜/i],
  '道具/设备': [/[Pp]rop|[Dd]evice|[Tt]rigger|[Oo]bject|道具|设备|媒介|物件|物品|手持|工具|吊坠|手环|镜子|手机|魔杖|扇子|眼镜/i],
  '动作/姿势': [/[Mm]otion|[Pp]ose|[Aa]ction|动作|姿势|运镜/i],
};

function classifyRole(seg) {
  if (!seg) return null;
  for (const role of Object.keys(ROLE_PATTERNS)) {
    for (const re of ROLE_PATTERNS[role]) {
      if (re.test(seg)) return role;
    }
  }
  return null;
}

// 切分声明块 + 可选/必选标记的图N对齐
function splitDeclarationBlocks(text) {
  if (!text) return [];
  const positions = [];
  const reFig = /图\s*(\d+)/g;
  let m;
  while ((m = reFig.exec(text)) !== null) {
    positions.push({ n: parseInt(m[1],10), start: m.index, end: m.index + m[0].length });
  }
  if (positions.length === 0) return [];
  // 找所有可选/必选标记
  const optMarkers = [];
  const reOpt = /(可选|optional|未提供时|缺图时|没传|没图|无图|if\s*provided|not\s*provided|选?一?张?)/gi;
  while ((m = reOpt.exec(text)) !== null) {
    optMarkers.push({ start: m.index, end: m.index + m[0].length });
  }
  const reqMarkers = [];
  const reReq = /(必选|必须|required|must\s*provide)/gi;
  while ((m = reReq.exec(text)) !== null) {
    reqMarkers.push({ start: m.index, end: m.index + m[0].length });
  }
  // assign: 每个标记，分配到最近的"图N"（前后 4 字符内且中间无分隔符）
  function assign(markers) {
    const map = new Map();
    for (const mk of markers) {
      let best = null, bestDist = Infinity;
      for (const p of positions) {
        let d;
        if (p.end <= mk.start) d = mk.start - p.end;
        else if (mk.end <= p.start) d = p.start - mk.end;
        else d = Infinity;
        if (d < bestDist) { bestDist = d; best = p; }
      }
      if (best && bestDist <= 4) {
        const between = text.slice(Math.min(best.end, mk.end), Math.max(best.start, mk.start));
        if (!/[【】()；,，。；;\n]/.test(between)) {
          map.set(best.n, (map.get(best.n)||0)+1);
        }
      }
    }
    return map;
  }
  const optMap = assign(optMarkers);
  const reqMap = assign(reqMarkers);
  // 切 roleSeg
  const blocks = positions.map((p, idx) => {
    const next = positions[idx+1];
    const blockStart = p.end;
    const blockEnd = next ? next.start : text.length;
    let seg = text.slice(blockStart, blockEnd);
    seg = seg.replace(/(可选|必选|optional|required|未提供时|缺图时|没传|没图|无图|必须|must\s*provide|if\s*provided|not\s*provided|选?一?张?)/gi, '').trim();
    return { n: p.n, roleSeg: seg, optional: optMap.has(p.n), required: reqMap.has(p.n) };
  });
  return blocks;
}

function extractDeclaredRolesFromText(text) {
  const result = {};
  if (!text) return result;
  const blocks = splitDeclarationBlocks(text);
  for (const b of blocks) {
    if (result[b.n]) continue;
    const role = classifyRole(b.roleSeg);
    if (role) result[b.n] = role;
  }
  return result;
}

function extractOptionalFromText(text) {
  const optional = new Set();
  const required = new Set();
  if (!text) return { optional, required };
  const blocks = splitDeclarationBlocks(text);
  for (const b of blocks) {
    if (b.optional) optional.add(b.n);
    if (b.required) required.add(b.n);
  }
  return { optional, required };
}

// 拆成三次独立 exec（避免大 OR 正则的回溯爆炸）
function extractPictureRolesFromPrompt(prompt) {
  const result = {};
  if (!prompt) return result;
  // 1) "- <Picture N> = the CHARACTER" 形式
  const re1 = /<Picture\s*(\d+)>\s*[=＝:：]\s*(?:the\s+)?([A-Z][A-Za-z\s\-\/]{2,40})/g;
  let m;
  while ((m = re1.exec(prompt)) !== null) {
    const n = parseInt(m[1], 10);
    const seg = m[2].trim();
    const role = classifyRole(seg);
    if (role) result[n] = role;
  }
  // 2) "- <Picture N> = OUTFIT" 形式（少见）
  const re2 = /<Picture\s*(\d+)>\s*[=＝:：]\s*([A-Z][A-Z\s\-\/]{2,30})(?=\s*[\(,.。；;]|$)/g;
  while ((m = re2.exec(prompt)) !== null) {
    const n = parseInt(m[1], 10);
    if (result[n]) continue;
    const seg = m[2].trim();
    const role = classifyRole(seg);
    if (role) result[n] = role;
  }
  // 3) "图N是XX铁证" 形式
  const re3 = /图\s*(\d+)\s*是\s*([^\s。，；\n]{1,20})/g;
  while ((m = re3.exec(prompt)) !== null) {
    const n = parseInt(m[1], 10);
    if (result[n]) continue;
    const seg = m[2];
    const role = classifyRole(seg);
    if (role) result[n] = role;
  }
  return result;
}

function hasReferenceLockHead(prompt) {
  if (!prompt) return false;
  const head = prompt.slice(0, 1500);
  return /CRITICAL\s*REFERENCE\s*LOCK|参考图铁律|REFERENCE-DRIVEN|参考图是唯一真相|REFERENCE\s*IMAGES?\s*ARE\s*THE\s*SOLE\s*TRUTH|参考图驱动|禁止自由创作|MUST\s+reproduce|MUST\s+copy|图\d?\s*是.*铁证|是.*铁证|铁证|STRICT\s*MULTI-REFERENCE\s*COMPLIANCE|严格多参考声明/i.test(head);
}

// 拆成多次独立 regex 测试（避免单大正则回溯）
function hasFallbackMention(prompt, figN, role) {
  if (!prompt) return false;
  const roleKeywords = {
    '人物':     '(?:character|person|人物|角色|identity|face|人脸)',
    '服装':     '(?:outfit|clothing|wardrobe|garment|dress|costume|服装|衣服)',
    '场景':     '(?:scene|background|environment|setting|location|场景|背景|环境)',
    '风格':     '(?:style|aesthetic|风格|画风)',
    '道具/设备': '(?:prop|device|trigger|object|道具|设备|媒介|物件|物品|手持|工具)',
  };
  const rk = roleKeywords[role] || '';
  // 模式 1
  const re1 = new RegExp(`if\\s*(?:no\\s*)?(?:<Picture\\s*${figN}\\s*>|Picture\\s*${figN}|图\\s*${figN})[^\\n]{0,80}(not\\s*provided|missing|absent|undefined|not\\s*connected|fallback|preserve|use|use\\s+the)`, 'i');
  if (re1.test(prompt)) return true;
  // 模式 2
  const re2 = new RegExp(`<Picture\\s*${figN}\\s*>[^\\n]{0,40}\\(if\\s*provided\\)|<Picture\\s*${figN}\\s*>[^\\n]{0,40}（如有）|<Picture\\s*${figN}\\s*>[^\\n]{0,40}（可选）|图\\s*${figN}[^\\n]{0,40}\\(if\\s*provided\\)|图\\s*${figN}[^\\n]{0,40}（如有）|图\\s*${figN}[^\\n]{0,40}（可选）|图\\s*${figN}[^\\n]{0,40}未提供`, 'i');
  if (re2.test(prompt)) return true;
  // 模式 3
  if (rk) {
    const re3 = new RegExp(`if\\s*(?:no\\s*)?${rk}\\s*(?:image|reference|图|picture)?\\s*(?:is\\s*)?(?:not\\s*provided|missing|absent|undefined|not\\s*connected|fallback)|${rk}\\s*(?:image|reference|图|picture)?\\s*(?:is\\s*not\\s*provided|is\\s*missing|未提供|缺|没有)`, 'i');
    if (re3.test(prompt)) return true;
  }
  // 模式 4
  const re4 = new RegExp(`(?:如)?未提供\\s*图\\s*${figN}|缺\\s*图\\s*${figN}|没传\\s*图\\s*${figN}|没\\s*图\\s*${figN}|无图\\s*${figN}|如果\\s*图\\s*${figN}\\s*(?:未|缺|不)`, 'i');
  if (re4.test(prompt)) return true;
  // 模式 5
  const re5 = new RegExp(`<Picture\\s*${figN}\\s*>\\s*(?:is\\s*)?(?:not\\s*provided|missing|absent|undefined|not\\s*connected)`, 'i');
  if (re5.test(prompt)) return true;
  // 模式 6
  if (/(未提供|not\s*provided|missing)/i.test(prompt) && /(保留|沿用|preserve|fallback|use\s+the\s+<Picture\s*1\s*>\s*background)/i.test(prompt) && new RegExp(`(图\\s*${figN}|<Picture\\s*${figN}\\s*>)`, 'i').test(prompt)) {
    return true;
  }
  return false;
}

function promptMentionsPicture(prompt) {
  if (!prompt) return [];
  const re = /<Picture\s*(\d+)>/g;
  const nums = new Set();
  let m;
  while ((m = re.exec(prompt)) !== null) nums.add(parseInt(m[1], 10));
  return [...nums].sort((a,b)=>a-b);
}

function walkTemplates(obj, cb) {
  if (!obj) return;
  if (Array.isArray(obj)) { obj.forEach(x => walkTemplates(x, cb)); return; }
  if (typeof obj === 'object') {
    if (Array.isArray(obj.templates)) {
      obj.templates.forEach(t => { if (t && t.id) cb(t); });
    }
    for (const k in obj) walkTemplates(obj[k], cb);
  }
}

function loadTemplates(file) {
  const raw = fs.readFileSync(file, 'utf8');
  const j = JSON.parse(raw);
  const map = new Map();
  walkTemplates(j, t => { map.set(t.id, t); });
  return map;
}

function checkOneTemplate(t) {
  const findings = [];
  const desc = t.description || '';
  const gen = t.generation_mode || '';
  const descGenBlob = desc + '\n' + gen;
  const prompt = t.prompt || '';

  const declared = Object.assign({}, extractDeclaredRolesFromText(desc), extractDeclaredRolesFromText(gen));
  const opt = extractOptionalFromText(descGenBlob);
  const pictureNumsInPrompt = promptMentionsPicture(prompt);
  const actualRoles = extractPictureRolesFromPrompt(prompt);
  const hasLock = hasReferenceLockHead(prompt);

  for (const n of pictureNumsInPrompt) {
    const d = declared[n];
    const a = actualRoles[n];
    if (d && a && d !== a) {
      findings.push({ type: 'A_ROLE_MISMATCH', severity: 'high', field: `Picture ${n}`,
        msg: `图${n} 角色不一致：description/generation_mode 声明="${d}"，但 prompt 实际把 <Picture ${n}> 当成 "${a}"`,
        suggestion: `统一 description / generation_mode 中图${n} 的角色声明，与 prompt 中的赋值保持一致。` });
    }
  }
  for (const n of Object.keys(declared)) {
    const nInt = parseInt(n, 10);
    if (!pictureNumsInPrompt.includes(nInt)) {
      findings.push({ type: 'A_DECLARED_BUT_UNUSED', severity: 'low', field: `Picture ${n}`,
        msg: `description/generation_mode 声明了"图${n}=${declared[n]}"，但 prompt 完全没引用 <Picture ${n}>`,
        suggestion: `要么在 prompt 里补上 <Picture ${n}> 的引用，要么从 description 中删除该图编号声明。` });
    }
  }
  for (const n of opt.optional) {
    if (!pictureNumsInPrompt.includes(n)) continue;
    const role = declared[n] || actualRoles[n];
    if (!hasFallbackMention(prompt, n, role)) {
      findings.push({ type: 'B_OPTIONAL_NO_FALLBACK', severity: 'medium', field: `Picture ${n}`,
        msg: `图${n}（${role||'?'}）声明为"可选"，但 prompt 没有"if no <Picture ${n}>" / "未提供图${n}" / "${role||'该图'}<Picture ${n}> 缺图时"之类的回退说明`,
        suggestion: `在 prompt 头部或该图赋值句后追加"if <Picture ${n}> is not provided, ..."的回退逻辑。` });
    }
  }
  if (pictureNumsInPrompt.length > 0 && !hasLock) {
    findings.push({ type: 'C_MISSING_LOCK_HEAD', severity: 'high', field: 'prompt[head]',
      msg: `prompt 引用了 <Picture ${pictureNumsInPrompt.join(', ')}>，但开头没有 CRITICAL REFERENCE LOCK / 参考图铁律 强声明`,
      suggestion: `在 prompt 头部补 [CRITICAL REFERENCE LOCK / 参考图铁律 - HIGHEST PRIORITY] 块，并逐图明确 "<Picture N> = the ROLE" 的硬约束。` });
  }
  return { findings, pictureNumsInPrompt, declared, actualRoles, hasLock, optional: [...opt.optional], required: [...opt.required] };
}

function main() {
  const webMap = loadTemplates(F_WEB);
  const backMap = loadTemplates(F_BACK);
  console.log('web templates:', webMap.size, 'back templates:', backMap.size);

  const allIds = new Set([...webMap.keys(), ...backMap.keys()]);
  const perTemplate = {};
  const issuesList = [];

  let i = 0;
  for (const id of allIds) {
    const t = webMap.get(id) || backMap.get(id);
    const r = checkOneTemplate(t);
    perTemplate[id] = r;
    for (const f of r.findings) issuesList.push(Object.assign({id}, f));
    if (++i % 50 === 0) console.log('processed', i, '/', allIds.size);
  }

  const diffRows = [];
  for (const id of allIds) {
    const w = webMap.get(id);
    const b = backMap.get(id);
    if (!w || !b) {
      diffRows.push({ id, field: '(present)', web: w ? 'YES' : 'NO', back: b ? 'YES' : 'NO' });
      continue;
    }
    for (const f of FIELDS_13) {
      const wv = w[f];
      const bv = b[f];
      if (wv === bv) continue;
      if (wv == null && bv == null) continue;
      if (typeof wv === 'string' && typeof bv === 'string' && wv === bv) continue;
      if (Array.isArray(wv) && Array.isArray(bv)) { const sa = JSON.stringify([...wv].sort()); const sb = JSON.stringify([...bv].sort()); if (sa === sb) continue; }
      diffRows.push({ id, field: f, web: typeof wv === 'string' ? wv.slice(0, 200) : JSON.stringify(wv), back: typeof bv === 'string' ? bv.slice(0, 200) : JSON.stringify(bv) });
    }
  }

  fs.writeFileSync(path.join(OUT_DIR, 'audit_results.json'), JSON.stringify({ perTemplate, issuesList, diffRows }));

  const byType = {};
  for (const it of issuesList) (byType[it.type] = byType[it.type] || []).push(it);

  let md = '# BSAI-MiniMAX-H3-Prompt 模板体检 — 问题清单\n\n';
  md += '- 总模板数：**' + allIds.size + '**\n';
  md += '- 体检源文件 1：`web/templates_data.json`（前端，' + (fs.statSync(F_WEB).size/1024).toFixed(1) + 'KB）\n';
  md += '- 体检源文件 2：`templates/prompt_templates.json`（后端，' + (fs.statSync(F_BACK).size/1024).toFixed(1) + 'KB）\n';
  md += '- 体检时间：' + new Date().toISOString() + '\n\n';
  const typeName = {
    A_ROLE_MISMATCH: 'A · 图N 角色不一致（declared vs actual）—— HIGH',
    A_DECLARED_BUT_UNUSED: 'A · description 声明了图N 但 prompt 未引用 —— LOW（多数为 description 写法过度）',
    B_OPTIONAL_NO_FALLBACK: 'B · 声明可选但无回退分支 —— MEDIUM',
    C_MISSING_LOCK_HEAD: 'C · 缺参考图铁律头 —— HIGH',
  };
  const order = ['A_ROLE_MISMATCH','C_MISSING_LOCK_HEAD','B_OPTIONAL_NO_FALLBACK','A_DECLARED_BUT_UNUSED'];
  for (const t of order) {
    const list = byType[t] || [];
    md += '\n## ' + typeName[t] + '（' + list.length + ' 条）\n\n';
    if (list.length === 0) { md += '> 无\n\n'; continue; }
    md += '| id | 字段 | 严重度 | 现象 | 建议修法 |\n|---|---|---|---|---|\n';
    for (const x of list) {
      const esc = s => String(s).replace(/\|/g,'\\|').replace(/\n/g,' ');
      md += '| `' + x.id + '` | ' + x.field + ' | ' + x.severity + ' | ' + esc(x.msg) + ' | ' + esc(x.suggestion) + ' |\n';
    }
    md += '\n';
  }
  fs.writeFileSync(path.join(OUT_DIR, '问题清单.md'), md);

  const totalRef = Object.values(perTemplate).filter(r => r.pictureNumsInPrompt.length > 0).length;
  const totalWithIssue = new Set(issuesList.map(x => x.id)).size;
  const highSev = new Set(issuesList.filter(x => x.severity === 'high').map(x => x.id));
  const medSev = new Set(issuesList.filter(x => x.severity === 'medium').map(x => x.id));
  const lowSev = new Set(issuesList.filter(x => x.severity === 'low').map(x => x.id));
  let st = '# BSAI-MiniMAX-H3-Prompt 模板体检 — 统计\n\n';
  st += '- 总模板数：**' + allIds.size + '**\n';
  st += '- 走参考生视频（prompt 含 `<Picture N>`）条数：**' + totalRef + '**\n';
  st += '- 体检出至少 1 条问题的条数：**' + totalWithIssue + '**\n';
  st += '- 至少 1 条 HIGH 严重度的条数：**' + highSev.size + '**\n';
  st += '- 至少 1 条 MEDIUM 严重度的条数：**' + medSev.size + '**\n';
  st += '- 至少 1 条 LOW 严重度的条数：**' + lowSev.size + '**\n';
  st += '- 各类问题计数：\n';
  st += '  - A 角色不一致（declared vs actual）：**' + ((byType.A_ROLE_MISMATCH||[]).length) + '**\n';
  st += '  - A description 声明但 prompt 未引用：**' + ((byType.A_DECLARED_BUT_UNUSED||[]).length) + '**\n';
  st += '  - B 声明可选但无回退分支：**' + ((byType.B_OPTIONAL_NO_FALLBACK||[]).length) + '**\n';
  st += '  - C 缺参考图铁律头：**' + ((byType.C_MISSING_LOCK_HEAD||[]).length) + '**\n';
  st += '- 跨文件 13 字段差异行数：**' + diffRows.length + '**\n\n';
  st += '## 每条模板体检结果（按 id 排序）\n\n';
  st += '| id | 引用图 | 声明角色 | 实际角色 | 铁律头 | 声明可选 | 严重度 |\n|---|---|---|---|---|---|---|\n';
  const sortedIds = [...allIds].sort();
  for (const id of sortedIds) {
    const r = perTemplate[id];
    const dStr = Object.entries(r.declared).map(([k,v])=>'图'+k+'='+v).join(' / ') || '—';
    const aStr = Object.entries(r.actualRoles).map(([k,v])=>'图'+k+'='+v).join(' / ') || '—';
    const sevSet = new Set(r.findings.map(f => f.severity));
    const sevStr = [...sevSet].sort().join('+') || '—';
    st += '| `' + id + '` | ' + (r.pictureNumsInPrompt.join(',') || '—') + ' | ' + dStr + ' | ' + aStr + ' | ' + (r.hasLock?'✓':'✗') + ' | ' + (r.optional.map(n=>'图'+n).join(',')||'—') + ' | ' + sevStr + ' |\n';
  }
  fs.writeFileSync(path.join(OUT_DIR, '统计.md'), st);

  let csv = 'id,field,web_value,back_value\n';
  for (const r of diffRows) {
    const esc = s => '"' + String(s == null ? '' : s).replace(/"/g,'""').replace(/\r?\n/g,' ') + '"';
    csv += esc(r.id) + ',' + esc(r.field) + ',' + esc(r.web) + ',' + esc(r.back) + '\n';
  }
  fs.writeFileSync(path.join(OUT_DIR, '跨文件差异.csv'), csv);

  console.log('SUMMARY');
  console.log('total templates:', allIds.size);
  console.log('total ref-driven templates:', totalRef);
  console.log('templates with >=1 issue:', totalWithIssue);
  console.log('templates with HIGH severity:', highSev.size);
  console.log('templates with MEDIUM severity:', medSev.size);
  console.log('templates with LOW severity:', lowSev.size);
  console.log('A_ROLE_MISMATCH:', (byType.A_ROLE_MISMATCH||[]).length);
  console.log('A_DECLARED_BUT_UNUSED:', (byType.A_DECLARED_BUT_UNUSED||[]).length);
  console.log('B_OPTIONAL_NO_FALLBACK:', (byType.B_OPTIONAL_NO_FALLBACK||[]).length);
  console.log('C_MISSING_LOCK_HEAD:', (byType.C_MISSING_LOCK_HEAD||[]).length);
  console.log('cross-file diff rows:', diffRows.length);
}

main();