"use strict";

// ---------------------------------------------------------------------------
// Texts and effect catalogue
// ---------------------------------------------------------------------------
const EFFECT_NAMES = {
  solid: "Static", static: "Custom", gradient: "Gradient", rainbow_wave: "Rainbow",
  color_wave: "Wave", spectrum: "Spectrum", breathing: "Breathing", ripple: "Ripple",
  starlight: "Starlight", points: "Imported map", image: "Image",
  plasma: "Plasma", rain: "Rain", scanner: "Scanner", fire: "Fire", heartbeat: "Heartbeat",
  reactive: "Key press",
};
const EFFECT_HELP = {
  solid: "One color on every key.",
  static: "Paint each key yourself.",
  gradient: "A fixed blend across the keyboard.",
  rainbow_wave: "The full rainbow rolling across.",
  color_wave: "Your own colors rolling across.",
  spectrum: "All keys cycle through every color.",
  breathing: "Fades in and out.",
  ripple: "Rings of light from the center.",
  starlight: "Random keys twinkle.",
  points: "Colors pinned to positions, imported from another keyboard.",
  image: "Samples a picture stretched over the keyboard.",
  plasma: "Blobs of color flowing into each other.",
  rain: "Drops falling down the keyboard.",
  scanner: "A bar of light sweeping back and forth.",
  fire: "Flames rising from the bottom.",
  heartbeat: "A double pulse, like a heartbeat.",
  reactive: "Lights up the keys you press. Unpressed keys show the layers below.",
};
// Effect tiles shown under the keyboard, in order.
const TILES = ["solid", "color_wave", "rainbow_wave", "gradient", "breathing", "spectrum", "plasma",
  "fire", "rain", "starlight", "ripple", "scanner", "heartbeat", "static"];
// Main controls per effect; anything else goes to Advanced.
const MAIN_PARAMS = {
  solid: ["color"],
  color_wave: ["colors", "speed", "angle", "wavelength"],
  rainbow_wave: ["speed", "angle", "wavelength"],
  gradient: ["colors", "angle"],
  breathing: ["colors", "period"],
  spectrum: ["speed"],
  ripple: ["colors", "speed", "thickness", "background"],
  starlight: ["colors", "background", "density", "period"],
  static: ["keys"],
  points: ["points"],
  image: ["path", "scroll"],
  plasma: ["colors", "speed", "scale"],
  rain: ["colors", "background", "speed", "density", "length"],
  scanner: ["color", "background", "speed", "width", "angle"],
  fire: ["colors", "speed", "height"],
  heartbeat: ["color", "bpm"],
  reactive: ["colors", "style", "duration", "speed", "background"],
};
const PARAM_NAMES = {
  color: "Color", colors: "Colors", speed: "Speed", angle: "Direction", wavelength: "Size",
  saturation: "Saturation", period: "Cycle", min: "Minimum brightness", center: "Center",
  thickness: "Ring width", background: "Background", density: "Amount", seed: "Variation",
  smooth: "Smoothing", scroll: "Scroll speed", path: "Image file", scale: "Size",
  length: "Trail", width: "Bar width", height: "Flame height", bpm: "Beats per minute",
  style: "Style", duration: "Fade",
};
// [min, max, step, left caption, right caption]; captions replace raw numbers where a
// number would mean nothing to the user.
const RANGES = {
  speed: [0, 1.5, 0.01, "Slow", "Fast"], wavelength: [0.2, 4, 0.05, "Tight", "Wide"],
  saturation: [0, 1, 0.01, "Pastel", "Vivid"], period: [0.2, 12, 0.1, "Quick", "Slow"],
  min: [0, 1, 0.01, "Dark", "Bright"], thickness: [0.02, 0.5, 0.01, "Thin", "Thick"],
  density: [0, 1, 0.01, "Few", "Many"], seed: [1, 99, 1, null, null], smooth: [0, 0.5, 0.01, "Sharp", "Soft"],
  scroll: [-1, 1, 0.01, "Left", "Right"], scale: [0.3, 3, 0.05, "Small", "Large"],
  length: [0.05, 1, 0.01, "Short", "Long"], width: [0.03, 0.5, 0.01, "Thin", "Wide"],
  height: [0.2, 1, 0.01, "Low", "High"], bpm: [30, 180, 1, null, null],
  duration: [0.1, 3, 0.05, "Quick", "Slow"],
  center_x: [0, 1, 0.01, "Left", "Right"], center_y: [0, 1, 0.01, "Top", "Bottom"],
};
const TAGS = ["animated", "static", "gaming", "chill", "nature", "neon", "productivity", "seasonal", "theme"];
const DIRECTIONS = [["→", 0], ["↘", 45], ["↓", 90], ["↙", 135], ["←", 180], ["↖", 225], ["↑", 270], ["↗", 315]];
const GROUP_NAMES = {
  wasd: "WASD", arrows: "Arrows", letters: "Letters", numbers: "Numbers",
  modifiers: "Modifiers", nav: "Navigation", fn_row: "F-keys", numpad: "Numpad",
};
const BLEND_NAMES = { normal: "Normal", add: "Add light", multiply: "Multiply", screen: "Screen" };
const PALETTE = ["#ff0030", "#ff8000", "#ffd000", "#00ff60", "#00e5ff", "#2050ff", "#a040ff", "#ff40c0", "#ffffff", "#7c5cff", "#00ffa0", "#000000"];
const RAINBOW = "linear-gradient(90deg,#ff0040,#ffd000,#00ff80,#00a0ff,#a040ff,#ff0040)";

// ---------------------------------------------------------------------------
// State and helpers
// ---------------------------------------------------------------------------
const S = {
  meta: null,
  profile: null,
  profileId: null,   // "mine:xxx" when editing a saved profile of yours
  sourceId: null,    // library entry it came from (highlighted)
  dirty: false,
  layer: 0,
  selection: new Set(),
  brush: "#ff0030",
  tab: "presets",
  tag: null,
  lib: { presets: [], mine: [], community: null },
  status: {},
  settings: {},
  history: [],
  future: [],
};
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const clone = (o) => JSON.parse(JSON.stringify(o));
const h = (tag, attrs = {}, ...kids) => {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "class") el.className = v;
    else if (k === "style") el.style.cssText = v;
    else if (v === true) el.setAttribute(k, "");
    else el.setAttribute(k, v);
  }
  for (const kid of kids.flat()) if (kid != null && kid !== false) el.append(kid);
  return el;
};
const store = {
  get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* private mode */ } },
};

async function api(path, body) {
  const opts = body === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  };
  const r = await fetch(path, opts);
  const data = await r.json().catch(() => ({ error: `Error ${r.status}` }));
  // errors come with an HTTP error status; a 200 with "error" is just state (e.g. OpenRGB is closed)
  if (!r.ok) throw new Error(data.error || `Error ${r.status}`);
  return data;
}

function toast(msg, kind = "") {
  const el = h("div", { class: `toast ${kind}` }, msg);
  $("#toasts").append(el);
  setTimeout(() => el.remove(), kind === "err" ? 6000 : 3000);
}

function hex(c) {
  if (Array.isArray(c)) return "#" + c.map((v) => Math.max(0, Math.min(255, v | 0)).toString(16).padStart(2, "0")).join("");
  if (typeof c !== "string") return "#000000";
  let s = c.trim().replace("#", "");
  if (s.length === 3) s = [...s].map((x) => x + x).join("");
  return /^[0-9a-f]{6}$/i.test(s) ? "#" + s.toLowerCase() : "#000000";
}

const currentLayer = () => S.profile.layers[S.layer];
const isPaintLayer = () => S.profile && currentLayer()?.effect === "static";

// ---------------------------------------------------------------------------
// Keyboard
// ---------------------------------------------------------------------------
const keyEls = {};
const lastColors = {};

function buildKeyboard() {
  const lay = S.meta.layout;
  const kb = $("#kb");
  kb.innerHTML = "";
  for (const id of Object.keys(keyEls)) { delete keyEls[id]; delete lastColors[id]; delete keyCol[id]; }
  kb.style.aspectRatio = `${lay.width} / ${lay.height}`;
  for (const k of lay.keys) {
    const el = h("div", {
      class: "key", "data-id": k.id,
      style: `left:${(k.x / lay.width) * 100}%;top:${(k.y / lay.height) * 100}%;` +
             `width:${(k.w / lay.width) * 100}%;height:${(k.h / lay.height) * 100}%`,
    }, h("div", { class: "cap" }, lay.labels[k.id] || ""));
    keyEls[k.id] = el;
    keyCol[k.id] = Math.min(GLOW_COLS - 1, Math.floor(((k.x + k.w / 2) / lay.width) * GLOW_COLS));
    kb.append(el);
  }
  kb.style.setProperty("--u", `${kb.clientWidth / lay.width}px`);
  if (kb.dataset.ready) return; // los eventos se enganchan una sola vez
  kb.dataset.ready = "1";
  new ResizeObserver(() => kb.style.setProperty("--u", `${kb.clientWidth / S.meta.layout.width}px`)).observe(kb);

  let mode = null; // paint | erase | select | deselect
  const act = (id) => {
    if (!id || !mode) return;
    if (mode === "paint") paintKey(id, S.brush);
    else if (mode === "erase") paintKey(id, null);
    else if (mode === "select") S.selection.add(id);
    else S.selection.delete(id);
    renderSelection();
  };
  kb.addEventListener("contextmenu", (e) => e.preventDefault());
  kb.addEventListener("pointerdown", (e) => {
    const id = e.target.closest(".key")?.dataset.id;
    if (!id) return;
    if (isPaintLayer()) {
      const cur = currentLayer().params.keys[id];
      mode = e.button === 2 || (cur && hex(cur) === hex(S.brush)) ? "erase" : "paint";
    } else {
      mode = S.selection.has(id) ? "deselect" : "select";
    }
    act(id);
  });
  kb.addEventListener("pointerover", (e) => act(e.target.closest(".key")?.dataset.id));
  window.addEventListener("pointerup", () => {
    if (mode === "paint" || mode === "erase") commit();
    mode = null;
  });
}

function drawFrame(ids, frame) {
  for (let i = 0; i < ids.length; i++) {
    if (lastColors[ids[i]] !== frame[i]) {
      lastColors[ids[i]] = frame[i];
      keyEls[ids[i]]?.style.setProperty("--c", "#" + frame[i]);
    }
  }
}

// Ambient light under the keyboard: the average color of each column of keys
const GLOW_COLS = 6;
const keyCol = {};
let glowAt = 0;

function updateGlow() {
  const sums = Array.from({ length: GLOW_COLS }, () => [0, 0, 0, 0]);
  for (const [id, c] of Object.entries(lastColors)) {
    const s = sums[keyCol[id]];
    if (!s || !c) continue;
    const n = parseInt(c, 16);
    s[0] += n >> 16; s[1] += (n >> 8) & 255; s[2] += n & 255; s[3]++;
  }
  const stops = sums.map(([r, g, b, n]) => (n ? `rgb(${r / n | 0},${g / n | 0},${b / n | 0})` : "transparent"));
  $("#kb-glow").style.setProperty("--glow", `linear-gradient(90deg,${stops.join(",")})`);
}

// Range inputs paint their filled part from --p
function syncRange(el) {
  const min = +el.min || 0, max = el.max === "" ? 100 : +el.max;
  el.style.setProperty("--p", `${((el.value - min) / (max - min || 1)) * 100}%`);
}
const syncRanges = () => $$("input[type=range]").forEach(syncRange);

function renderSelection() {
  for (const [id, el] of Object.entries(keyEls)) el.classList.toggle("sel", S.selection.has(id));
  updateHint();
  if (S.profile && !isPaintLayer()) renderLayerEditor(); // selection counts live in the editor
}

function updateHint() {
  let text = "";
  if (isPaintLayer()) text = "Click or drag over keys to paint them. Right-click erases.";
  else text = S.selection.size ? `${S.selection.size} keys selected · Esc to clear` : "Click or drag over keys to select them, then use them in a layer's Area.";
  $("#hint").textContent = text;
}

// ---------------------------------------------------------------------------
// Live preview: frames are computed by the real engine on the server
// ---------------------------------------------------------------------------
const P = { chunks: [], pending: false, gen: 0, fps: 30, t0: performance.now(), report: "" };
const nowT = () => (performance.now() - P.t0) / 1000;

const hasReactive = () => !!S.profile?.layers.some((l) => l.effect === "reactive");

function invalidatePreview() {
  P.gen++;
  P.chunks = [];
  P.pending = false;
}

async function requestFrames(start) {
  const gen = P.gen;
  P.pending = true;
  try {
    // reactive layers depend on keys pressed right now, so they are fetched almost live
    const r = await api("/api/frames", { profile: S.profile, start, count: hasReactive() ? 2 : 45, fps: P.fps });
    if (gen !== P.gen) return;
    P.chunks.push({ start, ids: r.keys, frames: r.frames });
    showReport(r.report);
  } catch (e) {
    if (gen === P.gen) showReport([e.message]);
    await new Promise((res) => setTimeout(res, 800));
  } finally {
    if (gen === P.gen) P.pending = false;
  }
}

function tick() {
  const t = nowT();
  P.chunks = P.chunks.filter((c) => c.start + c.frames.length / P.fps > t);
  const cur = P.chunks.find((c) => t >= c.start);
  if (cur) drawFrame(cur.ids, cur.frames[Math.min(cur.frames.length - 1, Math.floor((t - cur.start) * P.fps))]);
  if (t - glowAt > 0.2) { glowAt = t; updateGlow(); }
  if (!P.pending && S.profile) {
    const last = P.chunks[P.chunks.length - 1];
    const end = last ? last.start + last.frames.length / P.fps : null;
    if (end === null) requestFrames(t);
    else if (end - t < (hasReactive() ? 0.04 : 0.8)) requestFrames(end);
  }
}

// Adaptation notes (e.g. keys your keyboard doesn't have) are shown once per profile.
function showReport(lines) {
  const text = (lines || []).join(" · ");
  if (text && text !== P.report) toast(`Adapted to your keyboard: ${text}`);
  P.report = text;
}

// ---------------------------------------------------------------------------
// Profile and layers
// ---------------------------------------------------------------------------
function newLayer(effect) {
  const params = clone(S.meta.effects[effect].defaults);
  if (effect === "static") params.keys = {};
  return { effect, params };
}

function loadProfile(data, { id = null, sourceId = null } = {}) {
  S.profile = clone(data);
  S.profile.format = "keyglow/1";
  if (!Array.isArray(S.profile.layers) || !S.profile.layers.length) S.profile.layers = [newLayer("solid")];
  for (const l of S.profile.layers) {
    l.params = l.params || {};
    if (l.effect === "static") l.params.keys = l.params.keys || {};
  }
  S.profileId = id;
  S.sourceId = sourceId ?? id;
  S.layer = 0;
  S.dirty = false;
  S.history = [JSON.stringify(S.profile)];
  S.future = [];
  P.report = "";
  renderAll();
  pushLive();
}

let pushTimer = null;
function pushLive() {
  if (!S.status.running) return;
  clearTimeout(pushTimer);
  pushTimer = setTimeout(() => api("/api/apply", { profile: S.profile }).catch((e) => toast(e.message, "err")), 100);
}

function commit({ rerender = true } = {}) {
  const snap = JSON.stringify(S.profile);
  if (S.history[S.history.length - 1] !== snap) {
    S.history.push(snap);
    if (S.history.length > 80) S.history.shift();
    S.future = [];
  }
  S.dirty = true;
  invalidatePreview();
  if (rerender) renderEditor();
  renderHead();
  pushLive();
}

function undo() {
  if (S.history.length < 2) return;
  S.future.push(S.history.pop());
  restore(S.history[S.history.length - 1]);
}
function redo() {
  if (!S.future.length) return;
  const snap = S.future.pop();
  S.history.push(snap);
  restore(snap);
}
function restore(snap) {
  S.profile = JSON.parse(snap);
  S.layer = Math.min(S.layer, S.profile.layers.length - 1);
  S.dirty = true;
  invalidatePreview();
  renderEditor();
  renderHead();
  pushLive();
}

function paintKey(id, color) {
  const keys = currentLayer().params.keys;
  if (color) keys[id] = color; else delete keys[id];
  invalidatePreview();
}

function setBaseEffect(eff) {
  const base = S.profile.layers[0];
  const fresh = newLayer(eff);
  // fire's palette runs dark → bright, so other effects' colors don't make sense there
  if (eff !== "static" && eff !== "fire") fresh.params = carryColors(base.params || {}, fresh.params);
  S.profile.layers[0] = fresh;
  S.layer = 0;
  commit();
}

function carryColors(oldP, fresh) {
  const cs = oldP.colors || (oldP.color ? [oldP.color] : null);
  if (cs) {
    if ("colors" in fresh) fresh.colors = cs.length > 1 || fresh.colors.length === 1 ? clone(cs) : [cs[0], fresh.colors[1]];
    if ("color" in fresh) fresh.color = cs[0];
  }
  if ("speed" in oldP && "speed" in fresh) fresh.speed = Math.abs(oldP.speed);
  if ("angle" in oldP && "angle" in fresh) fresh.angle = oldP.angle;
  return fresh;
}

function layerSwatch(l) {
  const p = l.params || {};
  let cs = [];
  if (l.effect === "rainbow_wave" || l.effect === "spectrum") return RAINBOW;
  if (p.colors) cs = p.colors.map(hex);
  else if (p.color) cs = [hex(p.color)];
  else if (l.effect === "static") cs = [...new Set(Object.values(p.keys || {}).map(hex))].slice(0, 4);
  if (!cs.length) cs = ["#3a3f57"];
  return cs.length === 1 ? cs[0] : `linear-gradient(90deg, ${cs.join(", ")})`;
}

function layerSummary(l) {
  if (l.effect === "static") return `${Object.keys(l.params.keys || {}).length} keys painted`;
  if (l.keys && l.keys.length) {
    const groups = l.keys.filter((k) => k.startsWith("@")).map((k) => GROUP_NAMES[k.slice(1)] || k);
    const single = l.keys.filter((k) => !k.startsWith("@")).length;
    return [...groups, single ? `${single} keys` : null].filter(Boolean).join(", ");
  }
  return "All keys";
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------
function renderAll() {
  invalidatePreview();
  renderHead();
  renderEditor();
  renderCards();
}

function renderEditor() {
  renderTiles();
  renderLayers();
  renderLayerEditor();
  renderSelection();
}

function renderHead() {
  const name = $("#p-name");
  if (document.activeElement !== name) name.value = S.profile.name || "";
  name.style.width = `${Math.max(6, name.value.length + 2)}ch`;
  $("#dirty").hidden = !S.dirty;
}

function tileArt(eff) {
  const l = newLayer(eff);
  if (eff === "static") return "repeating-linear-gradient(90deg,#ff0030 0 14%,#1c1f2c 14% 20%,#00e5ff 20% 34%,#1c1f2c 34% 40%,#ffd000 40% 54%,#1c1f2c 54% 60%)";
  if (eff === "starlight") return "radial-gradient(circle at 20% 40%,#fff 0 3px,transparent 4px),radial-gradient(circle at 65% 65%,#80c0ff 0 3px,transparent 4px),radial-gradient(circle at 85% 25%,#fff 0 2px,transparent 3px),#0a0c20";
  if (eff === "ripple") return "radial-gradient(circle,transparent 0 22%,#00ffd0 24% 30%,transparent 33% 52%,#0040ff 54% 60%,transparent 63%),#000820";
  if (eff === "color_wave") return "linear-gradient(90deg,#ff0080,#7000ff,#00c0ff,#ff0080)";
  if (eff === "plasma") return "radial-gradient(circle at 25% 35%,#ff0080 0,transparent 45%),radial-gradient(circle at 75% 60%,#00c0ff 0,transparent 50%),radial-gradient(circle at 50% 100%,#00ff90 0,transparent 45%),#7000ff";
  if (eff === "fire") return "linear-gradient(0deg,#ffff80 0%,#ffb000 20%,#ff4000 45%,#a00000 70%,#000 100%)";
  if (eff === "rain") return "linear-gradient(180deg,transparent 10%,#00e5ff 30%,transparent 31%) 15% 0/2px 100% no-repeat,linear-gradient(180deg,transparent 40%,#fff 70%,transparent 71%) 45% 0/2px 100% no-repeat,linear-gradient(180deg,transparent 0,#00e5ff 45%,transparent 46%) 78% 0/2px 100% no-repeat,#000814";
  if (eff === "scanner") return "linear-gradient(90deg,#100000 0 35%,#ff0020 50%,#100000 65% 100%)";
  if (eff === "heartbeat") return "#ff0030";
  return layerSwatch(l);
}

function renderTiles() {
  const box = $("#effects");
  box.innerHTML = "";
  const base = S.profile.layers[0]?.effect;
  for (const eff of TILES) {
    const motion = ["color_wave", "rainbow_wave", "spectrum", "scanner"].includes(eff) ? "wave"
      : (["breathing", "heartbeat"].includes(eff) ? "breathe" : "");
    box.append(h("button", {
      class: `fx${base === eff ? " on" : ""}`, role: "radio", "aria-checked": String(base === eff),
      title: EFFECT_HELP[eff], onclick: () => setBaseEffect(eff),
    }, h("div", { class: `art ${motion}`, style: `background:${tileArt(eff)};background-size:${motion === "wave" ? "200% 100%" : "100% 100%"}` }),
    h("span", {}, EFFECT_NAMES[eff])));
  }
}

function field(label, control, value) {
  return h("div", { class: "field" },
    h("div", { class: "label flabel" }, h("span", {}, label), value ?? null), control);
}

// Editable number shown next to a slider, so exact values can be read, copied and typed in
function numBox(range, value, label, onValue) {
  const decimals = range.step >= 1 ? 0 : Math.min(3, Math.ceil(-Math.log10(range.step)));
  const fmt = (v) => (+v).toFixed(decimals);
  const box = h("input", { type: "number", class: "num", min: range.min, max: range.max, step: range.step,
    value: fmt(value), "aria-label": `${label} value` });
  const read = () => {
    const v = parseFloat(box.value);
    return Number.isFinite(v) ? Math.min(range.max, Math.max(range.min, v)) : null;
  };
  box.addEventListener("input", () => { const v = read(); if (v !== null) onValue(v, false); });
  box.addEventListener("change", () => { const v = read(); if (v === null) return; box.value = fmt(v); onValue(v, true); });
  box.addEventListener("keydown", (e) => { if (e.key === "Enter") box.blur(); });
  box.show = (v) => { if (document.activeElement !== box) box.value = fmt(v); };
  return box;
}

function slider(name, value, onChange, label) {
  const [min, max, step, lo, hi] = RANGES[name] || [0, 1, 0.01, null, null];
  label = label || PARAM_NAMES[name] || name;
  const inp = h("input", { type: "range", min, max, step, value, "aria-label": label });
  const num = numBox({ min, max, step }, value, label, (v, final) => { inp.value = v; syncRange(inp); onChange(v, final); });
  inp.addEventListener("input", () => { num.show(inp.value); onChange(+inp.value, false); });
  inp.addEventListener("change", () => onChange(+inp.value, true));
  const control = lo ? h("div", {}, inp, h("div", { class: "ends" }, h("span", {}, lo), h("span", {}, hi))) : inp;
  return field(label, control, num);
}

function percent(label, value, onChange) {
  const inp = h("input", { type: "range", min: 0, max: 100, step: 1, value, "aria-label": label });
  const num = numBox({ min: 0, max: 100, step: 1 }, value, label, (v, final) => { inp.value = v; syncRange(inp); onChange(v, final); });
  inp.addEventListener("input", () => { num.show(inp.value); onChange(+inp.value, false); });
  inp.addEventListener("change", () => onChange(+inp.value, true));
  return field(label, inp, h("span", { class: "num-wrap" }, num, "%"));
}

function colorInput(value, onChange, label = "Color") {
  const inp = h("input", { type: "color", value: hex(value), "aria-label": label });
  inp.addEventListener("input", () => onChange(inp.value, false));
  inp.addEventListener("change", () => onChange(inp.value, true));
  return inp;
}

function live(apply) {
  return (v, final) => {
    apply(v);
    if (final) commit({ rerender: false });
    else { invalidatePreview(); pushLive(); }
    renderLayers();
    renderTiles();
  };
}

function paramControl(l, name, def) {
  const val = l.params[name] ?? def;
  if (name === "keys" && l.effect === "static") return paintTools(l);
  if (name === "colors") return colorList(l, val);
  if (name === "color") {
    return field("Color", h("div", {},
      colorInput(val, live((v) => { l.params.color = v; })),
      swatchRow(val, (c) => { l.params.color = c; commit(); })));
  }
  if (name === "background") return backgroundField(l, val);
  if (name === "style") {
    const sel = h("select", { "aria-label": "Style" }, Object.entries(STYLE_NAMES).map(([k, v]) => h("option", { value: k, selected: val === k }, v)));
    sel.addEventListener("change", () => { l.params.style = sel.value; commit(); });
    return field("Style", sel);
  }
  if (name === "angle") return directionField(l, val);
  if (name === "center") return centerField(l, val);
  if (name === "points") return h("div", { class: "note" }, `${val.length} colors pinned to positions. It adapts to any layout on its own.`);
  if (name === "path") {
    const inp = h("input", { value: val, placeholder: "C:\\path\\to\\picture.png" });
    inp.addEventListener("change", () => { l.params.path = inp.value; commit({ rerender: false }); });
    return field("Image file", inp);
  }
  if (typeof def === "number") return slider(name, val, live((v) => { l.params[name] = name === "seed" ? Math.round(v) : v; }));
  return null;
}

function swatchRow(current, pick) {
  return h("div", { class: "swatches" }, PALETTE.slice(0, 12).map((c) =>
    h("button", { class: hex(current) === c ? "on" : "", style: `background:${c}`, title: c, "aria-label": c, onclick: () => pick(c) })));
}

// Drag a chip sideways to reorder; a plain click still opens the color picker.
function sortable(wrap, onMove) {
  let drag = null;
  wrap.addEventListener("pointerdown", (e) => {
    const chip = e.target.closest(".c");
    if (!chip || e.button !== 0 || e.target.closest(".x")) return;
    drag = { chip, from: [...wrap.children].indexOf(chip), x: e.clientX, y: e.clientY, moved: false };
  });
  wrap.addEventListener("pointermove", (e) => {
    if (!drag) return;
    if (!drag.moved) {
      if (Math.hypot(e.clientX - drag.x, e.clientY - drag.y) < 6) return;
      drag.moved = true;
      drag.chip.classList.add("dragging");
      wrap.setPointerCapture(e.pointerId);
    }
    // move the chip in the DOM next to the nearest other chip, on the side the pointer is
    const others = [...wrap.querySelectorAll(".c")].filter((c) => c !== drag.chip);
    let best = null, dist = Infinity;
    for (const c of others) {
      const r = c.getBoundingClientRect();
      const d = Math.hypot(e.clientX - (r.left + r.width / 2), e.clientY - (r.top + r.height / 2));
      if (d < dist) { dist = d; best = c; }
    }
    if (!best) return;
    const r = best.getBoundingClientRect();
    const after = e.clientX > r.left + r.width / 2;
    const ref = after ? best.nextSibling : best;
    if (ref !== drag.chip && ref !== drag.chip.nextSibling) wrap.insertBefore(drag.chip, ref);
  });
  const end = () => {
    if (!drag) return;
    const { chip, from, moved } = drag;
    drag = null;
    chip.classList.remove("dragging");
    if (!moved) return;
    // swallow the click that ends the drag, so it doesn't open the color picker
    const swallow = (ev) => { ev.preventDefault(); ev.stopPropagation(); };
    wrap.addEventListener("click", swallow, true);
    setTimeout(() => wrap.removeEventListener("click", swallow, true), 50);
    const to = [...wrap.querySelectorAll(".c")].indexOf(chip);
    if (to !== from) onMove(from, to);
  };
  wrap.addEventListener("pointerup", end);
  wrap.addEventListener("pointercancel", end);
}

function colorList(l, val) {
  const wrap = h("div", { class: "colors", title: "Drag a color to change the order" });
  const move = (from, to) => {
    const [c] = l.params.colors.splice(from, 1);
    l.params.colors.splice(to, 0, c);
    commit({ rerender: false }); draw(); renderTiles();
    wrap.querySelectorAll('input[type="color"]')[to]?.focus();
  };
  const draw = () => {
    wrap.innerHTML = "";
    l.params.colors = l.params.colors || clone(val);
    l.params.colors.forEach((c, i) => {
      const inp = colorInput(c, live((v) => { l.params.colors[i] = v; }), `Color ${i + 1} (Alt+arrows to move)`);
      inp.addEventListener("keydown", (e) => {
        const to = i + (e.key === "ArrowLeft" ? -1 : e.key === "ArrowRight" ? 1 : 0);
        if (!e.altKey || to === i || to < 0 || to >= l.params.colors.length) return;
        e.preventDefault();
        move(i, to);
      });
      wrap.append(h("div", { class: "c" }, inp,
        l.params.colors.length > 1 ? h("button", { class: "x", title: "Remove", "aria-label": "Remove color", onclick: () => { l.params.colors.splice(i, 1); commit({ rerender: false }); draw(); renderTiles(); } }, "✕") : null));
    });
    if (l.params.colors.length < 8) {
      wrap.append(h("button", { class: "add", title: "Add color", "aria-label": "Add color", onclick: () => {
        l.params.colors.push(PALETTE[(l.params.colors.length * 3) % PALETTE.length]);
        commit({ rerender: false }); draw(); renderTiles();
      } }, "+"));
    }
  };
  draw();
  sortable(wrap, move);
  return field("Colors", wrap);
}

function directionField(l, val) {
  const norm = ((val % 360) + 360) % 360;
  const nearest = DIRECTIONS.reduce((a, b) => (Math.abs(b[1] - norm) < Math.abs(a[1] - norm) ? b : a))[1];
  return field("Direction", h("div", { class: "dirs" }, DIRECTIONS.map(([arrow, deg]) =>
    h("button", { class: deg === nearest ? "on" : "", "aria-label": `${deg}°`, onclick: () => { l.params.angle = deg; commit(); } }, arrow))));
}

function backgroundField(l, val) {
  const on = val != null;
  const chk = h("input", { type: "checkbox", checked: on, "aria-label": "Use a background color" });
  const col = colorInput(val || "#000010", live((v) => { l.params.background = v; }), "Background color");
  col.disabled = !on;
  chk.addEventListener("change", () => { l.params.background = chk.checked ? col.value : null; col.disabled = !chk.checked; commit({ rerender: false }); });
  return field("Background", h("div", { class: "colors" }, chk, col));
}

function centerField(l, val) {
  const wrap = h("div", {});
  [["Center", "center_x"], ["Center height", "center_y"]].forEach(([label, axis], idx) => {
    wrap.append(slider(axis, val[idx], live((v) => {
      l.params.center = [...(l.params.center || val)];
      l.params.center[idx] = v;
    }), label));
  });
  return wrap;
}

function paintTools(l) {
  const count = Object.keys(l.params.keys).length;
  const brush = colorInput(S.brush, (v) => { S.brush = v; }, "Brush color");
  return h("div", {},
    field("Brush", h("div", {}, brush, swatchRow(S.brush, (c) => { S.brush = c; renderLayerEditor(); }))),
    h("div", { class: "field" },
      h("div", { class: "btn-row" },
        h("button", { onclick: () => { S.meta.layout.keys.forEach((k) => { l.params.keys[k.id] = S.brush; }); commit(); } }, "Fill all"),
        h("button", { disabled: !count, onclick: () => { l.params.keys = {}; commit(); } }, "Clear"),
        S.selection.size ? h("button", { onclick: () => { S.selection.forEach((id) => { l.params.keys[id] = S.brush; }); commit(); } }, `Paint ${S.selection.size} selected`) : null)),
    h("p", { class: "muted small" }, count ? `${count} keys painted. Unpainted keys show the layers below.` : "No keys painted yet."));
}

// ---------- Studio: every layer is an area + a color + an animation ----------
const ANIMS = [["none", "None (still)"], ["wave", "Wave"], ["breathing", "Breathing"], ["cycle", "Color cycle"],
  ["ripple", "Ripple"], ["twinkle", "Twinkle"], ["scanner", "Scanner"], ["plasma", "Plasma"], ["fire", "Fire"],
  ["rain", "Rain"], ["heartbeat", "Heartbeat"], ["reactive", "On key press"]];
const RAINBOW_COLORS = ["#ff0000", "#ff8000", "#ffff00", "#00ff00", "#00ffff", "#0040ff", "#8000ff", "#ff00c0"];
const ONE_ONLY = new Set(["scanner", "heartbeat"]);
const STYLE_NAMES = { key: "Light the key", ripple: "Ripple from the key", row: "Light the row" };
const COLOR_MODES = [["one", "One"], ["several", "Several"], ["rainbow", "Rainbow"], ["paint", "Paint"]];

const isRainbow = (cs) => Array.isArray(cs) && cs.map(hex).join() === RAINBOW_COLORS.join();
const layerColors = (l) => {
  const p = l.params || {};
  if (l.effect === "static") return [...new Set(Object.values(p.keys || {}).map(hex))].slice(0, 4);
  return (p.colors || (p.color ? [p.color] : [])).map(hex);
};

// Which color mode and animation a layer corresponds to.
function describeLayer(l) {
  const p = l.params || {};
  const cols = layerColors(l);
  const fromList = (anim) => {
    if (isRainbow(cols)) return { color: "rainbow", anim };
    if (cols.length === 1 || (cols.length === 2 && cols[1] === "#000000" && ["wave", "cycle", "plasma"].includes(anim))) {
      return { color: "one", anim };
    }
    return { color: "several", anim };
  };
  switch (l.effect) {
    case "solid": return { color: "one", anim: "none" };
    case "gradient": return fromList("none");
    case "static": return { color: "paint", anim: "none" };
    case "rainbow_wave": return { color: "rainbow", anim: "wave" };
    case "spectrum": return { color: "rainbow", anim: "cycle" };
    case "color_wave": return fromList((p.wavelength ?? 1) >= 20 ? "cycle" : "wave");
    case "breathing": return fromList("breathing");
    case "ripple": return fromList("ripple");
    case "starlight": return fromList("twinkle");
    case "plasma": return fromList("plasma");
    case "rain": return fromList("rain");
    case "reactive": return fromList("reactive");
    case "scanner": return { color: "one", anim: "scanner" };
    case "heartbeat": return { color: "one", anim: "heartbeat" };
    case "fire": return { color: "several", anim: "fire" };
    default: return { color: "other", anim: "other" };
  }
}

// Builds the layer for a color mode + animation, keeping whatever settings still apply.
function buildLayer(old, color, anim) {
  let cs = layerColors(old).filter((c, i, a) => a.indexOf(c) === i);
  if (!cs.length) cs = [S.brush];
  if (color === "rainbow") cs = RAINBOW_COLORS.slice();
  else if (color === "one") cs = [cs.find((c) => c !== "#000000") || cs[0]];
  else if (color === "several") {
    if (isRainbow(cs)) cs = ["#ff0080", "#7000ff", "#00c0ff"];
    // "One" with wave/cycle/plasma is stored as [color, black]: the black is filler, not a choice
    if (describeLayer(old).color === "one") cs = cs.filter((c) => c !== "#000000");
    if (!cs.length) cs = [S.brush];
    if (cs.length < 2) cs = [cs[0], cs[0] === "#00e5ff" ? "#ff0080" : "#00e5ff"];
  }
  const one = cs[0];
  const withDark = color === "one" ? [one, "#000000"] : cs;
  let effect, params;
  if (color === "paint") {
    effect = "static";
    params = { keys: old.effect === "static" ? old.params.keys : Object.fromEntries((S.selection.size ? [...S.selection] : []).map((k) => [k, one])) };
  } else {
    const table = {
      none: color === "one" ? ["solid", { color: one }] : ["gradient", { colors: cs }],
      wave: color === "rainbow" ? ["rainbow_wave", {}] : ["color_wave", { colors: withDark }],
      cycle: color === "rainbow" ? ["spectrum", {}] : ["color_wave", { colors: withDark, wavelength: 50 }],
      breathing: ["breathing", { colors: cs }],
      ripple: ["ripple", { colors: cs }],
      twinkle: ["starlight", { colors: cs }],
      scanner: ["scanner", { color: one }],
      plasma: ["plasma", { colors: withDark }],
      fire: ["fire", old.effect === "fire" ? { colors: old.params.colors } : {}],
      rain: ["rain", { colors: cs }],
      heartbeat: ["heartbeat", { color: one }],
      reactive: ["reactive", { colors: cs }],
    };
    [effect, params] = table[anim] || table.none;
  }
  const defaults = S.meta.effects[effect].defaults;
  const keep = {};
  for (const [k, v] of Object.entries(old.params || {})) {
    if (k in defaults && !["colors", "color", "keys", "wavelength"].includes(k)) keep[k] = v;
  }
  if (anim === "wave" && old.params?.wavelength != null && old.params.wavelength < 20) keep.wavelength = old.params.wavelength;
  const out = { effect, params: effect === "static" ? params : { ...clone(defaults), ...keep, ...params } };
  if (typeof out.params.speed === "number") out.params.speed = Math.abs(out.params.speed);
  if (effect !== "static" && old.keys) out.keys = old.keys;
  if (old.opacity !== undefined) out.opacity = old.opacity;
  if (old.blend !== undefined) out.blend = old.blend;
  return out;
}

function section(title, ...kids) {
  return h("section", { class: "ed-sec" }, h("div", { class: "label" }, title), ...kids);
}

function segmented(options, current, onPick, isDisabled = () => false) {
  return h("div", { class: "seg" }, options.map(([v, label]) =>
    h("button", { class: v === current ? "on" : "", disabled: isDisabled(v), onclick: () => onPick(v) }, label)));
}

// One editable color, whatever the effect stores it as.
function oneColorControl(l) {
  const get = () => (l.params.color !== undefined ? l.params.color : l.params.colors[0]);
  const put = (v) => { if (l.params.color !== undefined) l.params.color = v; else l.params.colors[0] = v; };
  const value = hex(get());
  return h("div", {}, colorInput(value, live(put)), swatchRow(value, (c) => { put(c); commit(); }));
}

function areaField(l) {
  const filtered = Array.isArray(l.keys) && l.keys.length > 0;
  const kids = [segmented([["all", "All keys"], ["some", "Some keys"]], filtered ? "some" : "all", (v) => {
    if (v === "all") delete l.keys;
    else l.keys = S.selection.size ? [...S.selection] : ["@wasd"];
    commit();
  })];
  if (filtered) {
    const groups = Object.entries(GROUP_NAMES).filter(([g]) => (S.meta.groups[g] || []).length);
    kids.push(h("div", { class: "chips area-chips" }, groups.map(([g, name]) => {
      const on = l.keys.includes(`@${g}`);
      return h("button", { class: on ? "on" : "", onclick: () => {
        l.keys = on ? l.keys.filter((k) => k !== `@${g}`) : [...l.keys, `@${g}`];
        if (!l.keys.length) delete l.keys;
        commit();
      } }, name);
    })));
    const resolved = resolveKeys(l.keys);
    kids.push(h("div", { class: "btn-row" },
      h("span", { class: "muted small", style: "align-self:center" }, `${resolved.length} keys`),
      h("button", { disabled: !S.selection.size, onclick: () => { l.keys = [...new Set([...l.keys, ...S.selection])]; commit(); } },
        `Add selected (${S.selection.size})`),
      h("button", { onclick: () => { S.selection = new Set(resolved); renderSelection(); renderLayerEditor(); } }, "Show")));
  }
  return section("Area", ...kids);
}

function resolveKeys(sels) {
  const out = new Set();
  for (const s of sels || []) {
    if (s === "@all") S.meta.layout.keys.forEach((k) => out.add(k.id));
    else if (s.startsWith("@")) (S.meta.groups[s.slice(1)] || []).forEach((k) => out.add(k));
    else out.add(s);
  }
  return [...out];
}

function renderLayerEditor() {
  const box = $("#layer-editor");
  box.innerHTML = "";
  const l = currentLayer();
  if (!l) return;
  // profiles may leave colors out and rely on the effect's defaults (e.g. Campfire)
  const defs = S.meta.effects[l.effect]?.defaults || {};
  l.params = l.params || {};
  for (const k of ["color", "colors"]) if (k in defs && l.params[k] === undefined) l.params[k] = clone(defs[k]);
  const d = describeLayer(l);
  const set = (color, anim) => { S.profile.layers[S.layer] = buildLayer(l, color, anim); commit(); };

  if (d.color === "other") {
    box.append(h("div", { class: "note" }, `${EFFECT_NAMES[l.effect] || l.effect}: ${EFFECT_HELP[l.effect] || ""} This layer was imported and can only be moved, mixed or deleted.`));
    box.append(mixingSection(l));
    return;
  }
  if (d.color !== "paint") box.append(areaField(l));

  // Color
  const allowed = (m) => (m === "paint" ? true : ONE_ONLY.has(d.anim) ? m === "one" : d.anim === "fire" ? m === "several" : true);
  const colorKids = [segmented(COLOR_MODES, d.color, (m) => set(m, m === "paint" ? "none" : d.anim), (m) => !allowed(m))];
  if (d.color === "one") colorKids.push(oneColorControl(l));
  else if (d.color === "several") {
    colorKids.push(colorList(l, l.params.colors));
    if (d.anim === "fire") colorKids.push(h("p", { class: "muted small" }, "From the base of the flame to its tip."));
  } else if (d.color === "paint") colorKids.push(paintTools(l));
  box.append(section("Color", ...colorKids));

  // Animation
  const anim = h("select", { "aria-label": "Animation" }, ANIMS.map(([v, label]) => h("option", { value: v, selected: v === d.anim }, label)));
  anim.addEventListener("change", () => {
    const a = anim.value;
    const color = ONE_ONLY.has(a) ? "one" : a === "fire" ? "several" : d.color === "paint" ? (a === "none" ? "paint" : "several") : d.color;
    set(color, a);
  });
  const animKids = [anim];
  if (EFFECT_HELP[l.effect] && d.anim !== "none") animKids.push(h("p", { class: "muted small" }, EFFECT_HELP[l.effect]));
  const defaults = S.meta.effects[l.effect]?.defaults || {};
  for (const name of MAIN_PARAMS[l.effect] || []) {
    if (["color", "colors", "keys"].includes(name) || !(name in defaults)) continue;
    if (d.anim === "cycle" && ["angle", "wavelength"].includes(name)) continue;
    if (l.effect === "reactive" && name === "speed" && l.params.style !== "ripple") continue;
    const c = paramControl(l, name, defaults[name]);
    if (c) animKids.push(c);
  }
  box.append(section("Animation", ...animKids));
  box.append(mixingSection(l));
}

function mixingSection(l) {
  if (S.profile.layers.length < 2) return h("div", {});
  const blend = h("select", { "aria-label": "Blend" }, Object.entries(BLEND_NAMES).map(([k, v]) => h("option", { value: k, selected: (l.blend || "normal") === k }, v)));
  blend.addEventListener("change", () => { if (blend.value === "normal") delete l.blend; else l.blend = blend.value; commit({ rerender: false }); });
  return section("Mixing",
    percent("Opacity", Math.round((l.opacity ?? 1) * 100), live((v) => { l.opacity = v / 100; if (l.opacity >= 1) delete l.opacity; })),
    field("Blend with layers below", blend));
}

function addLayer() {
  const l = S.selection.size
    ? { effect: "solid", params: { color: "#ffffff" }, keys: [...S.selection] }
    : { effect: "reactive", params: clone(S.meta.effects.reactive.defaults) };
  S.profile.layers.push(l);
  S.layer = S.profile.layers.length - 1;
  commit();
}

// ---------- layer list ----------
function renderLayers() {
  const ol = $("#layers");
  ol.innerHTML = "";
  const n = S.profile.layers.length;
  S.profile.layers.forEach((l, i) => {
    const stop = (fn) => (e) => { e.stopPropagation(); fn(); };
    ol.append(h("li", { class: `layer${i === S.layer ? " active" : ""}`, onclick: () => { S.layer = i; renderEditor(); } },
      h("div", { class: "swatch", style: `background:${layerSwatch(l)}` }),
      h("div", { class: "info" }, EFFECT_NAMES[l.effect] || l.effect,
        h("small", {}, layerSummary(l) + (l.opacity != null && l.opacity < 1 ? ` · ${Math.round(l.opacity * 100)}%` : ""))),
      h("div", { class: "tools" },
        h("button", { title: "Move up", "aria-label": "Move up", disabled: i === n - 1, onclick: stop(() => moveLayer(i, 1)) }, "▲"),
        h("button", { title: "Move down", "aria-label": "Move down", disabled: i === 0, onclick: stop(() => moveLayer(i, -1)) }, "▼"),
        h("button", { title: "Delete", "aria-label": "Delete layer", disabled: n === 1, onclick: stop(() => {
          S.profile.layers.splice(i, 1); S.layer = Math.max(0, Math.min(S.layer, n - 2)); commit();
        }) }, "✕"))));
  });
}

function moveLayer(i, d) {
  const L = S.profile.layers;
  const j = i + d;
  if (j < 0 || j >= L.length) return;
  [L[i], L[j]] = [L[j], L[i]];
  S.layer = j;
  commit();
}

// ---------------------------------------------------------------------------
// Library
// ---------------------------------------------------------------------------
const thumbs = new Map();

async function loadLibrary() {
  const r = await api("/api/library");
  S.lib.presets = r.presets;
  S.lib.mine = r.mine;
  renderCards();
}

async function loadCommunity() {
  try {
    S.lib.community = await api("/api/community");
  } catch (e) {
    S.lib.community = { name: "Community", source: S.settings.community_url, profiles: [], error: e.message };
  }
  renderCards();
}

function renderCards() {
  if ($("#library").hidden) return;
  const box = $("#cards");
  const q = $("#search").value.trim().toLowerCase();
  const list = S.tab === "community" ? S.lib.community?.profiles || [] : S.lib[S.tab] || [];
  const present = TAGS.filter((t) => list.some((e) => (e.tags || []).includes(t)));
  if (S.tag && !present.includes(S.tag)) S.tag = null;
  const tagBox = $("#tags");
  tagBox.innerHTML = "";
  if (present.length > 1) {
    for (const t of [null, ...present]) {
      tagBox.append(h("button", { class: S.tag === t ? "on" : "", onclick: () => { S.tag = t; renderCards(); } },
        t ? t[0].toUpperCase() + t.slice(1) : "All"));
    }
  }
  const items = list.filter((e) => (!S.tag || (e.tags || []).includes(S.tag)) && (!q || e.name.toLowerCase().includes(q) ||
    (e.tags || []).some((t) => t.toLowerCase().includes(q)) || (e.author || "").toLowerCase().includes(q)));
  box.innerHTML = "";
  thumbObserver.disconnect();
  if (S.tab === "community" && !S.lib.community) {
    box.append(h("li", { class: "empty" }, "Loading…"));
    loadCommunity();
  } else if (!items.length) {
    box.append(h("li", { class: "empty" }, S.tab === "mine" && !q ? "Nothing saved yet. Edit a profile and press Save."
      : S.lib.community?.error && S.tab === "community" ? `Couldn't load the gallery: ${S.lib.community.error}` : "No matches."));
  }
  for (const e of items) {
    const cv = h("canvas", { width: 112, height: 40 });
    box.append(h("li", { class: `card${S.sourceId === e.id ? " current" : ""}`, title: e.description || e.name, onclick: () => openEntry(e) },
      cv, h("span", { class: "name" }, e.name),
      e.kind === "mine" ? h("button", { class: "del", title: "Delete", "aria-label": `Delete ${e.name}`, onclick: (ev) => { ev.stopPropagation(); deleteEntry(e); } }, "✕") : null));
    cv.entry = e;
    thumbObserver.observe(cv);
  }
  const foot = $("#lib-foot");
  foot.innerHTML = "";
  if (S.tab === "community") {
    const c = S.lib.community;
    foot.append(c?.source ? `${c.name} · ` : "Built-in examples · ",
      h("a", { onclick: openSettings }, c?.source ? "Change gallery" : "Connect a gallery"));
  }
}

// Thumbnails are rendered only when their card scrolls into view (galleries can be long)
const thumbObserver = new IntersectionObserver((entries) => {
  for (const it of entries) {
    if (!it.isIntersecting) continue;
    thumbObserver.unobserve(it.target);
    drawThumb(it.target, it.target.entry);
  }
}, { rootMargin: "200px" });

async function drawThumb(cv, e) {
  let frame = null;
  if (e.data) {
    const key = e.id + JSON.stringify(e.data).length;
    frame = thumbs.get(key);
    if (!frame) {
      try {
        frame = (await api("/api/frames", { profile: e.data, start: 1.2, count: 1, fps: 30 })).frames[0];
        thumbs.set(key, frame);
      } catch { frame = null; }
    }
  }
  const ctx = cv.getContext("2d");
  const lay = S.meta.layout;
  const u = Math.min(cv.width / lay.width, cv.height / lay.height);
  const ox = (cv.width - u * lay.width) / 2, oy = (cv.height - u * lay.height) / 2;
  ctx.clearRect(0, 0, cv.width, cv.height);
  lay.keys.forEach((k, i) => {
    ctx.fillStyle = frame ? "#" + frame[i] : "#2a2e42";
    ctx.fillRect(ox + k.x * u + 0.6, oy + k.y * u + 0.6, k.w * u - 1.2, k.h * u - 1.2);
  });
}

async function openEntry(e) {
  try {
    let data = e.data;
    if (!data && e.url) {
      data = (await api("/api/import", { url: e.url })).data;
      e.data = data;
    }
    if (S.dirty && !confirm("Discard unsaved changes to the current profile?")) return;
    loadProfile(data, { id: e.kind === "mine" ? e.id : null, sourceId: e.id });
  } catch (err) { toast(err.message, "err"); }
}

async function deleteEntry(e) {
  if (!confirm(`Delete "${e.name}"? This removes the file.`)) return;
  try {
    await api("/api/delete", { id: e.id });
    if (S.profileId === e.id) S.profileId = null;
    await loadLibrary();
    toast("Profile deleted");
  } catch (err) { toast(err.message, "err"); }
}

function toggleLibrary(show = $("#library").hidden) {
  $("#library").hidden = !show;
  $("#btn-library").setAttribute("aria-expanded", String(show));
  store.set("keyglow.library", show);
  renderCards();
}

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------
async function setPower(on) {
  try {
    if (on) {
      const st = await api("/api/apply", { profile: S.profile });
      setStatus(st);
      if (!st.connected) toast("Lights are on, but OpenRGB isn't responding yet. Make sure it's open.", "err");
    } else {
      setStatus(await api("/api/off", {}));
    }
  } catch (e) { toast(e.message, "err"); }
}

async function save(copy) {
  S.profile.name = $("#p-name").value.trim() || "Untitled";
  try {
    const entry = await api("/api/save", { profile: S.profile, id: copy ? null : S.profileId });
    S.profileId = entry.id;
    S.sourceId = entry.id;
    S.dirty = false;
    renderHead();
    await loadLibrary();
    toast(`Saved "${entry.name}" to My profiles`);
  } catch (e) { toast(e.message, "err"); }
}

const EXPORT_NOTES = {
  keyglow: "The full profile, animations included. Open it in KeyGlow on any keyboard.",
  openrgb: "Copy it into OpenRGB's profiles folder (%APPDATA%\\OpenRGB\\profiles) and restart OpenRGB. It is made for the keyboard KeyGlow is connected to.",
  "keys-openrgb": "A {key: color} map with OpenRGB key names, for scripts and other tools.",
  "keys-web": "A {key: color} map with browser key codes (KeyboardEvent.code), for web tools.",
  "keys-qmk": "A {keycode: color} map with QMK keycodes, handy when setting up custom firmware lighting.",
  csv: "One row per key: key,color. Opens in any spreadsheet.",
};

function openExport() {
  const sel = $("#exp-format");
  if (!sel.options.length) {
    for (const [k, v] of Object.entries(S.meta.export_formats)) sel.append(h("option", { value: k }, v));
    sel.addEventListener("change", updateExportNote);
  }
  updateExportNote();
  $("#dlg-export").showModal();
}

function updateExportNote() {
  const fmt = $("#exp-format").value;
  $("#exp-note").textContent = EXPORT_NOTES[fmt] + (fmt === "keyglow" ? "" : " Other programs can't play KeyGlow's animations, so this saves the colors at one moment.");
  $("#exp-at-wrap").hidden = fmt === "keyglow";
}

async function exportProfile() {
  try {
    const r = await api("/api/export", { profile: S.profile, format: $("#exp-format").value, at: +$("#exp-at").value || 0 });
    const blob = new Blob([r.content], { type: r.filename.endsWith(".csv") ? "text/csv" : "application/json" });
    const a = h("a", { href: URL.createObjectURL(blob), download: r.filename });
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
    toast(`Exported ${r.filename}`);
  } catch (err) { toast(err.message, "err"); }
}

async function saveToKeyboard() {
  try {
    const { summary } = await api("/api/device/save", { profile: S.profile });
    if (!confirm(`Save to the keyboard's memory: ${summary}.

The keyboard will keep it without KeyGlow running. KeyGlow stops controlling the lights so you see what was saved.`)) return;
    const r = await api("/api/device/save", { profile: S.profile, confirm: true });
    setStatus(r);
    toast("Saved to the keyboard's memory");
  } catch (err) { toast(err.message, "err"); }
}

function newProfile() {
  if (S.dirty && !confirm("Discard unsaved changes and start a new profile?")) return;
  loadProfile({ format: "keyglow/1", name: "My profile", layers: [{ effect: "solid", params: { color: "#7c5cff" } }] });
  S.dirty = true;
  renderHead();
}

async function doImport(payload) {
  try {
    const r = await api("/api/import", payload);
    loadProfile(r.data);
    S.dirty = true;
    renderHead();
    toast(r.report.length ? `Imported and adapted: ${r.report.join(" · ")}` : "Profile imported");
    $("#dlg-import").close();
  } catch (e) { toast(e.message, "err"); }
}

function openDetails() {
  $("#p-author").value = S.profile.author || "";
  $("#p-tags").value = (S.profile.tags || []).join(", ");
  $("#p-desc").value = S.profile.description || "";
  $("#dlg-details").showModal();
}

function setupDialogs() {
  // import
  const dlg = $("#dlg-import");
  const file = $("#imp-file");
  const drop = $("#drop");
  // sent as base64: OpenRGB .orp profiles are binary
  const readFile = (f) => f.arrayBuffer().then((buf) => {
    let bin = "";
    const bytes = new Uint8Array(buf);
    for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
    return doImport({ data: btoa(bin), filename: f.name });
  });
  file.addEventListener("change", () => file.files[0] && readFile(file.files[0]));
  drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("over"); });
  drop.addEventListener("dragleave", () => drop.classList.remove("over"));
  drop.addEventListener("drop", (e) => { e.preventDefault(); drop.classList.remove("over"); if (e.dataTransfer.files[0]) readFile(e.dataTransfer.files[0]); });
  $("#imp-go").addEventListener("click", (e) => {
    e.preventDefault();
    const url = $("#imp-url").value.trim();
    if (!url) { toast("Choose a file or paste a link."); return; }
    doImport({ url });
  });
  window.addEventListener("dragover", (e) => e.preventDefault());
  window.addEventListener("drop", (e) => {
    if (dlg.open) return;
    e.preventDefault();
    if (e.dataTransfer.files[0]) readFile(e.dataTransfer.files[0]);
  });

  // details
  $("#exp-go").addEventListener("click", exportProfile);
  $("#set-layout-export").addEventListener("click", exportLayout);
  $("#set-workshop-check").addEventListener("click", checkWorkshop);
  $("#details-ok").addEventListener("click", () => {
    const author = $("#p-author").value.trim();
    const desc = $("#p-desc").value.trim();
    const tags = $("#p-tags").value.split(",").map((t) => t.trim()).filter(Boolean);
    if (author) S.profile.author = author; else delete S.profile.author;
    if (desc) S.profile.description = desc; else delete S.profile.description;
    if (tags.length) S.profile.tags = tags; else delete S.profile.tags;
    commit({ rerender: false });
  });

  // settings
  $("#btn-settings").addEventListener("click", openSettings);
  $("#set-save").addEventListener("click", async (e) => {
    e.preventDefault();
    try {
      const old = S.settings.community_url;
      S.settings = await api("/api/settings", {
        community_url: $("#set-community").value.trim(),
        fps: Math.max(5, Math.min(60, +$("#set-fps").value || 30)),
        apply_last_on_start: $("#set-last").checked,
        start_with_windows: $("#set-autostart").checked,
        start_openrgb: $("#set-openrgb").checked,
        layout: $("#set-layout").value,
        layout_updates: $("#set-layout-updates").checked,
        openrgb_device: $("#set-device").value.trim(),
      });
      pollStatus(); // picks up a layout change
      if (old !== S.settings.community_url) { S.lib.community = null; renderCards(); }
      $("#dlg-settings").close();
      toast("Settings saved");
    } catch (err) { toast(err.message, "err"); }
  });
  $("#btn-quit").addEventListener("click", async () => {
    if (!confirm("Quit KeyGlow? The keyboard keeps its last colors.")) return;
    await api("/api/quit", {}).catch(() => {});
    document.body.innerHTML = '<div class="empty" style="padding-top:30vh;font-size:16px">KeyGlow has closed. You can close this window.</div>';
  });
}

// ---------- game profiles ----------
let runningApps = [];

function profileSelect(selected, onChange) {
  const sel = h("select", { "aria-label": "Profile" },
    h("optgroup", { label: "My profiles" }, S.lib.mine.map((e) => h("option", { value: e.id, selected: e.id === selected }, e.name))),
    h("optgroup", { label: "Presets" }, S.lib.presets.map((e) => h("option", { value: e.id, selected: e.id === selected }, e.name))));
  if (!S.lib.mine.length) sel.firstChild.remove();
  sel.addEventListener("change", () => onChange(sel.value));
  return sel;
}

async function saveRules(rules) {
  try {
    S.settings = await api("/api/settings", { game_rules: rules, game_switching: $("#games-on").checked, auto_games: $("#games-auto").checked });
  } catch (e) { toast(e.message, "err"); }
  renderRules();
}

function renderRules() {
  renderFound();
  const ul = $("#game-rules");
  ul.innerHTML = "";
  const rules = S.settings.game_rules || [];
  if (!rules.length) ul.append(h("li", { class: "empty", style: "display:block;border:none" }, "No games yet. Open your game, then add it below."));
  rules.forEach((r, i) => {
    ul.append(h("li", {},
      h("div", { class: "rule-app" }, h("b", {}, r.name || r.exe), h("small", {}, r.exe)),
      profileSelect(r.profile_id, (id) => { const next = clone(rules); next[i].profile_id = id; saveRules(next); }),
      h("button", { class: "x", type: "button", title: "Remove", "aria-label": `Remove ${r.name || r.exe}`, onclick: () => saveRules(rules.filter((_, j) => j !== i)) }, "✕")));
  });
  const sel = $("#game-app");
  const taken = new Set(rules.map((r) => r.exe));
  sel.innerHTML = "";
  sel.append(h("option", { value: "" }, runningApps.length ? "Choose an open app…" : "Choose…"));
  for (const a of runningApps) if (!taken.has(a.exe)) sel.append(h("option", { value: a.exe }, `${a.title} (${a.exe})`));
  sel.append(h("option", { value: "__other" }, "Other: type the .exe name…"));
  $("#game-exe").hidden = true;
}

let installedGames = [];

function renderFound() {
  const ul = $("#games-found");
  ul.innerHTML = "";
  const rules = S.settings.game_rules || [];
  const name = (id) => S.lib.presets.find((e) => e.id === id)?.name || id;
  for (const g of installedGames) {
    const custom = rules.find((r) => r.exe === g.exe);
    ul.append(h("li", {},
      h("div", { class: "rule-app" }, h("b", {}, g.name), h("small", {}, `${g.genre_name} · ${g.source}`)),
      h("span", { class: "genre" }, custom ? "Your profile" : `Recommended: ${name(g.profile_id)}`),
      custom ? h("span", {}) : h("button", { type: "button", class: "mini-btn", onclick: () =>
        saveRules([...rules, { exe: g.exe, name: g.name, profile_id: g.profile_id }]) }, "Customize")));
  }
  if (!installedGames.length) ul.append(h("li", { class: "empty", style: "display:block;border:none" }, "No known games found on this PC."));
}

async function openGames() {
  $("#games-on").checked = S.settings.game_switching !== false;
  $("#games-auto").checked = !!S.settings.auto_games;
  renderRules();
  $("#dlg-games").showModal();
  const [apps, games] = await Promise.all([api("/api/apps").catch(() => ({ apps: [] })), api("/api/games").catch(() => ({ installed: [] }))]);
  runningApps = apps.apps;
  installedGames = games.installed;
  renderRules();
}

function setupGames() {
  $("#btn-games").addEventListener("click", openGames);
  $("#games-on").addEventListener("change", () => saveRules(S.settings.game_rules || []));
  $("#games-auto").addEventListener("change", () => saveRules(S.settings.game_rules || []));
  $("#game-app").addEventListener("change", () => {
    $("#game-exe").hidden = $("#game-app").value !== "__other";
    if (!$("#game-exe").hidden) $("#game-exe").focus();
  });
  $("#game-add").addEventListener("click", () => {
    const v = $("#game-app").value;
    let exe = v === "__other" ? $("#game-exe").value.trim().toLowerCase() : v;
    if (!exe) { toast("Choose an app first."); return; }
    if (!exe.endsWith(".exe")) exe += ".exe";
    const app = runningApps.find((a) => a.exe === exe);
    const profile = S.profileId || (S.sourceId?.startsWith("preset:") ? S.sourceId : "preset:aurora");
    saveRules([...(S.settings.game_rules || []), { exe, name: app ? app.title : exe.replace(/\.exe$/, ""), profile_id: profile }]);
  });
}

// Where the keyboard drawing comes from (see layout.from_device)
function layoutInfo(lay) {
  const [kind, base] = (lay.source || "").split(":");
  const title = (S.meta.layouts.find((l) => l.name === base) || {}).title || base;
  const fix = " If it doesn't match your keyboard, export it, fix it and share it (see the Compatibility docs).";
  if (kind === "model") {
    const from = base === "workshop" ? ", from the KeyGlow workshop" : "";
    const untested = lay.verified === false ? " Not tested on real hardware yet." : "";
    return `Exact layout for the ${lay.title}${from}.${untested}`;
  }
  if (kind === "standard") return `Detected: standard ${title} layout.` + fix;
  if (kind === "adapted") return `Detected: adapted from ${title} using OpenRGB's key map.` + fix;
  if (kind === "matrix") return "Detected: built from OpenRGB's key map (approximate)." + fix;
  return `Using the ${lay.title} layout.`;
}

function exportLayout() {
  const lay = S.meta.layout;
  const out = {
    title: S.status.device || lay.title,
    ...(lay.usb ? { usb: [lay.usb] } : {}),
    ...(S.status.device ? { names: [S.status.device] } : {}),
    keys: lay.keys,
  };
  const name = (out.title || "keyboard").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  const blob = new Blob([JSON.stringify(out, null, 2) + "\n"], { type: "application/json" });
  const a = h("a", { href: URL.createObjectURL(blob), download: `${name}.json` });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

async function showWorkshopInfo() {
  const box = $("#set-workshop-info");
  try {
    const w = await api("/api/layouts");
    box.textContent = w.fetched
      ? `${w.count} layouts in the workshop, checked ${new Date(w.fetched * 1000).toLocaleString()}.`
      : "Not downloaded yet.";
  } catch { box.textContent = ""; }
}

async function checkWorkshop() {
  const box = $("#set-workshop-info");
  box.textContent = "Checking…";
  try {
    const r = await api("/api/layouts/refresh", {});
    if (r.error) toast(`Couldn't reach the workshop: ${r.error}`, "err");
    await showWorkshopInfo();
    pollStatus(); // a better layout may have arrived
  } catch (e) { box.textContent = ""; toast(e.message, "err"); }
}

function openSettings() {
  const sel = $("#set-layout");
  sel.innerHTML = "";
  sel.append(h("option", { value: "auto" }, "Automatic (as OpenRGB reports it)"),
    ...S.meta.layouts.map((l) => h("option", { value: l.name }, l.title)));
  sel.value = S.settings.layout || "auto";
  $("#set-layout-info").textContent = layoutInfo(S.meta.layout);
  $("#set-layout-updates").checked = S.settings.layout_updates !== false;
  showWorkshopInfo();
  $("#set-device").value = S.settings.openrgb_device || "";
  $("#set-community").value = S.settings.community_url || "";
  $("#set-fps").value = S.settings.fps || 30;
  $("#set-last").checked = !!S.settings.apply_last_on_start;
  $("#set-autostart").checked = !!S.settings.start_with_windows;
  $("#set-openrgb").checked = !!S.settings.start_openrgb;
  $("#set-dir").textContent = S.meta.user_dir;
  $("#dlg-settings").showModal();
}

function setupMenu() {
  const menu = $("#more-menu");
  const btn = $("#btn-more");
  const close = () => { menu.hidden = true; };
  btn.addEventListener("click", (e) => { e.stopPropagation(); menu.hidden = !menu.hidden; });
  document.addEventListener("click", close);
  menu.addEventListener("click", async (e) => {
    const act = e.target.closest("button")?.dataset.act;
    close();
    if (act === "new") newProfile();
    else if (act === "copy") save(true);
    else if (act === "details") openDetails();
    else if (act === "import") { $("#imp-file").value = ""; $("#imp-url").value = ""; $("#dlg-import").showModal(); }
    else if (act === "export") openExport();
    else if (act === "onboard") saveToKeyboard();
    else if (act === "capture") {
      try { const r = await api("/api/capture", {}); loadProfile(r.data); S.dirty = true; renderHead(); toast("Captured the keyboard's current colors"); }
      catch (err) { toast(err.message, "err"); }
    }
  });
}

// ---------------------------------------------------------------------------
// Keyboard status
// ---------------------------------------------------------------------------
// The keyboard layout can change at runtime (another keyboard, or a different layout in Settings)
async function reloadLayout() {
  S.meta = await api("/api/meta");
  S.selection.clear();
  thumbs.clear();
  buildKeyboard();
  invalidatePreview();
  if (S.profile) renderEditor();
}

function setStatus(st) {
  if (S.meta && st.layout_rev !== undefined && st.layout_rev !== S.meta.layout_rev) {
    S.meta.layout_rev = st.layout_rev;
    reloadLayout();
  }
  S.status = st;
  // the first time the keyboard stays unreachable for a few seconds, explain how to connect it
  offlinePolls = st.connected ? 0 : offlinePolls + 1;
  if (offlinePolls >= 3 && !connectShown && !document.querySelector("dialog[open]")) { connectShown = true; openConnect(); }
  if (st.connected) connectShown = true;
  const dev = $("#device");
  dev.classList.toggle("ok", !!st.connected);
  dev.classList.toggle("bad", !st.connected);
  $("#device-text").textContent = st.connected ? st.device : "Keyboard not connected";
  dev.title = st.connected ? "Connected through OpenRGB" : `${st.error || "Open OpenRGB and start its SDK Server."}\nClick to retry.`;
  const pw = $("#power");
  pw.classList.toggle("on", !!st.running);
  pw.setAttribute("aria-checked", String(!!st.running));
  $("#power-text").textContent = st.running ? "On" : "Off";
  const pill = $("#game-pill");
  pill.hidden = !st.override;
  if (st.override) {
    pill.textContent = `${st.override.reason} · ${st.override.profile}`;
    pill.title = `Playing ${st.override.reason}: using "${st.override.profile}"`;
  }
}

// First-run help: what's missing for KeyGlow to reach the keyboard
function openConnect() {
  const box = $("#con-install");
  box.innerHTML = "";
  box.append(S.meta.openrgb_path
    ? `Found at ${S.meta.openrgb_path}.`
    : h("span", {}, "Not found. ", h("a", { href: S.meta.openrgb_url, target: "_blank", rel: "noopener" }, "Download OpenRGB"), ", install it, then come back."));
  $("#con-start").hidden = !S.meta.openrgb_path;
  $("#con-error").textContent = S.status.error || "";
  $("#con-error").hidden = !S.status.error;
  const dlg = $("#dlg-connect");
  if (!dlg.open) dlg.showModal();
}

async function reconnect() {
  try {
    const st = await api("/api/connect", {});
    setStatus(st);
    if (st.connected) { $("#dlg-connect").close(); toast(`Connected to ${st.device}`); }
    else if ($("#dlg-connect").open) openConnect();
    else toast(st.error, "err");
  } catch (e) { toast(e.message, "err"); }
}

let offlinePolls = 0;
let connectShown = false;

async function pollStatus() {
  try { setStatus(await api("/api/status")); } catch { /* server closed */ }
}

// ---------------------------------------------------------------------------
// Start
// ---------------------------------------------------------------------------
async function init() {
  [S.meta, S.settings] = await Promise.all([api("/api/meta"), api("/api/settings")]);
  buildKeyboard();

  $("#add-layer").addEventListener("click", addLayer);

  $$(".library .seg button").forEach((b) => b.addEventListener("click", () => {
    $$(".library .seg button").forEach((x) => x.classList.toggle("on", x === b));
    S.tab = b.dataset.tab;
    renderCards();
  }));
  $("#search").addEventListener("input", renderCards);
  $("#btn-library").addEventListener("click", () => toggleLibrary());

  const name = $("#p-name");
  name.addEventListener("input", () => { S.profile.name = name.value; S.dirty = true; renderHead(); });
  name.addEventListener("change", () => commit({ rerender: false }));
  name.addEventListener("keydown", (e) => { if (e.key === "Enter") name.blur(); });

  $("#power").addEventListener("click", () => setPower(!S.status.running));
  $("#device").addEventListener("click", () => (S.status.connected ? reconnect() : openConnect()));
  $("#con-retry").addEventListener("click", reconnect);
  $("#con-start").addEventListener("click", async () => {
    try { await api("/api/openrgb/start", {}); toast("Starting OpenRGB… this can take a few seconds"); setTimeout(reconnect, 5000); }
    catch (e) { toast(e.message, "err"); }
  });
  const br = $("#brightness");
  br.value = Math.round((S.settings.brightness ?? 1) * 100);
  br.title = `Brightness ${br.value}%`;
  let brTimer;
  br.addEventListener("input", () => {
    br.title = `Brightness ${br.value}%`;
    clearTimeout(brTimer);
    brTimer = setTimeout(() => api("/api/settings", { brightness: br.value / 100 }).then((s) => { S.settings = s; }), 80);
  });
  $("#btn-save").addEventListener("click", () => save(false));
  window.addEventListener("keydown", (e) => {
    if (e.target.matches("input, textarea")) return;
    const k = e.key.toLowerCase();
    if (e.ctrlKey && k === "z") { e.preventDefault(); e.shiftKey ? redo() : undo(); }
    else if (e.ctrlKey && k === "y") { e.preventDefault(); redo(); }
    else if (e.ctrlKey && k === "s") { e.preventDefault(); save(false); }
    else if (e.key === "Escape") { S.selection.clear(); renderSelection(); }
  });
  document.addEventListener("input", (e) => { if (e.target.matches?.("input[type=range]")) syncRange(e.target); });
  new MutationObserver(syncRanges).observe(document.body, { childList: true, subtree: true });
  syncRanges();
  setupMenu();
  setupDialogs();
  setupGames();

  await Promise.all([loadLibrary(), pollStatus()]);
  if (store.get("keyglow.library", false)) toggleLibrary(true);
  const start = S.settings.last_profile || S.lib.presets[0]?.data;
  loadProfile(start || { name: "My profile", layers: [newLayer("solid")] }, {
    sourceId: S.lib.presets.find((p) => p.data?.name === start?.name)?.id ?? null,
  });
  setInterval(pollStatus, 2000);
  setInterval(tick, 1000 / 40);
}

init().catch((e) => {
  document.body.innerHTML = `<div class="empty" style="padding-top:30vh">KeyGlow couldn't start: ${e.message}</div>`;
});
