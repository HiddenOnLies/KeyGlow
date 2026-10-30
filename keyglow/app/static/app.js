"use strict";

// ---------------------------------------------------------------------------
// Texts and effect catalogue
// ---------------------------------------------------------------------------
const EFFECT_NAMES = {
  solid: "Static", static: "Custom", gradient: "Gradient", rainbow_wave: "Rainbow",
  color_wave: "Wave", spectrum: "Spectrum", breathing: "Breathing", ripple: "Ripple",
  starlight: "Starlight", points: "Imported map", image: "Image",
  plasma: "Plasma", rain: "Rain", scanner: "Scanner", fire: "Fire", heartbeat: "Heartbeat",
  reactive: "Key press", music: "Music", swirl: "Swirl", comet: "Comet", bounce: "Bounce", glitch: "Glitch",
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
  music: "Follows the sound playing on your PC: spectrum bars, a pulse with the bass, or a volume meter.",
  swirl: "Colors turning around a point, like a pinwheel.",
  comet: "A comet running across every row, with a tail.",
  bounce: "A ball of light bouncing off the edges.",
  glitch: "Bits of rows flashing, like a broken signal.",
};
// Effect tiles shown under the keyboard, in order.
const TILES = ["solid", "color_wave", "rainbow_wave", "gradient", "breathing", "spectrum", "plasma",
  "fire", "rain", "starlight", "ripple", "scanner", "heartbeat", "swirl", "comet", "bounce", "glitch", "music", "static"];
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
  music: ["colors", "style", "sensitivity", "background"],
  swirl: ["colors", "speed", "twist", "center"],
  comet: ["color", "background", "speed", "length"],
  bounce: ["color", "background", "speed", "size"],
  glitch: ["colors", "background", "density", "speed"],
};
const PARAM_NAMES = {
  color: "Color", colors: "Colors", speed: "Speed", angle: "Direction", wavelength: "Size",
  saturation: "Saturation", period: "Cycle", min: "Minimum brightness", center: "Center",
  thickness: "Ring width", background: "Background", density: "Amount", seed: "Variation",
  smooth: "Smoothing", scroll: "Scroll speed", path: "Image file", scale: "Size",
  length: "Trail", width: "Bar width", height: "Flame height", bpm: "Beats per minute",
  style: "Style", duration: "Fade", twist: "Twist", size: "Ball size", sensitivity: "Sensitivity",
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
  duration: [0.1, 3, 0.05, "Quick", "Slow"], twist: [-4, 4, 0.1, "Left", "Right"],
  size: [0.04, 0.4, 0.01, "Small", "Large"], sensitivity: [0.2, 3, 0.05, "Calm", "Lively"],
  center_x: [0, 1, 0.01, "Left", "Right"], center_y: [0, 1, 0.01, "Top", "Bottom"],
};
const TAGS = ["animated", "static", "reactive", "gaming", "chill", "nature", "neon", "productivity", "seasonal", "theme"];
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
  editing: false,    // the layer editor is open
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
const keySx = {}; // horizontal position of each key, 0..1, for the light sweep

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
    keySx[k.id] = (k.x + k.w / 2) / lay.width;
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
    if (!id || !S.editing) return;
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
  const tr = lightTransition.current;
  const now = performance.now();
  if (tr && now > tr.end) lightTransition.current = null;
  for (let i = 0; i < ids.length; i++) {
    let c = frame[i];
    if (tr && now <= tr.end && tr.from[ids[i]]) {
      const p = Math.min(1, Math.max(0, (now - tr.start - (keySx[ids[i]] || 0) * tr.spread) / tr.dur));
      if (p < 1) c = mixHex(tr.from[ids[i]], c, p * p * (3 - 2 * p));
    }
    if (lastColors[ids[i]] !== c) {
      lastColors[ids[i]] = c;
      keyEls[ids[i]]?.style.setProperty("--c", "#" + c);
    }
  }
}

function mixHex(a, b, t) {
  const x = parseInt(a, 16), y = parseInt(b, 16);
  const ch = (s) => Math.round(((x >> s) & 255) * (1 - t) + ((y >> s) & 255) * t);
  return ((ch(16) << 16) | (ch(8) << 8) | ch(0)).toString(16).padStart(6, "0");
}

// The keyboard moves from the colors it shows to the next ones instead of jumping:
// "sweep" runs left to right like a scanner (switching profiles), "fade" is a quick crossfade (hover previews).
const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
function lightTransition(kind) {
  if (reducedMotion.matches) return;
  const [spread, dur] = kind === "sweep" ? [420, 260] : [0, 160];
  const start = performance.now();
  const from = Object.fromEntries(Object.keys(keyEls).map((id) => [id, lastColors[id] || "000000"])); // at startup: from dark
  lightTransition.current = { from, start, spread, dur, end: start + spread + dur };
}
lightTransition.current = null;

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
const P = { chunks: [], pending: false, gen: 0, fps: 30, t0: performance.now(), report: "", peek: null };
const nowT = () => (performance.now() - P.t0) / 1000;

const shown = () => P.peek || S.profile; // a library card being hovered wins
// key-press and music layers depend on what happens right now, so their preview is fetched almost live
const hasReactive = (p = shown()) => !!p?.layers?.some((l) => l.effect === "reactive" || l.effect === "music");

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
    const peeking = !!P.peek;
    const r = await api("/api/frames", { profile: shown(), start, count: hasReactive() ? 2 : 45, fps: P.fps });
    if (gen !== P.gen) return;
    P.chunks.push({ start, ids: r.keys, frames: r.frames });
    if (!peeking) showReport(r.report);
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
  if (!P.pending && shown()) {
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
  lightTransition("sweep");
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
  lightTransition("sweep");
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
  renderHintsEditor();
  renderSelection();
}

// ---------- Shortcut lights: per profile, shown while holding Ctrl, Alt or Win ----------
const HINT_EFFECTS = [["solid", "Solid color"], ["pulse", "Pulse"], ["blink", "Blink"], ["sparkle", "Sparkle"],
  ["gradient", "Gradient"], ["wave", "Wave"], ["rainbow", "Rainbow"], ["profile", "Profile colors"]];
const HINT_HELP = {
  solid: "The shortcut keys light up in one color.",
  pulse: "The shortcut keys breathe in one color.",
  blink: "The shortcut keys flash on and off.",
  sparkle: "The shortcut keys glow in one color and flash white now and then.",
  gradient: "Your colors spread across the shortcut keys, left to right.",
  wave: "Your colors move along the shortcut keys.",
  rainbow: "A rainbow runs across the shortcut keys.",
  profile: "The shortcut keys keep this profile's colors at full brightness.",
};
const HINT_ONE_COLOR = new Set(["solid", "pulse", "blink", "sparkle"]);
const HINT_COLORS = new Set(["gradient", "wave"]);
const HINT_MOVING = new Set(["pulse", "blink", "sparkle", "wave", "rainbow"]);
RANGES.hint_speed = [0.2, 3, 0.05, "Slow", "Fast"];
RANGES.hint_delay = [0, 1.5, 0.05, "Instant", "Long hold"];

function renderHintsEditor() {
  const box = $("#hints-editor");
  box.innerHTML = "";
  const cfg = { enabled: true, effect: "solid", ...(S.profile.shortcut_hints || {}) };
  const attach = () => { S.profile.shortcut_hints = cfg; }; // the profile keeps this object from now on
  const put = (patch) => {
    Object.assign(cfg, patch);
    if (HINT_COLORS.has(cfg.effect) && !cfg.colors) cfg.colors = ["#ff0080", "#00e5ff"];
    attach();
    commit({ rerender: false });
    renderHintsEditor();
    if (patch.effect || patch.color) previewHints();
  };
  // sliders: apply while dragging, save and preview when released
  const tweak = (name) => (v, final) => { cfg[name] = v; attach(); if (final) { commit({ rerender: false }); previewHints(); } };
  const kids = [h("p", { class: "muted small" }, "Hold Ctrl, Alt or Win for a moment: the rest of the keyboard dims and the keys of its shortcuts light up.")];
  kids.push(segmented([["on", "On"], ["off", "Off"]], cfg.enabled ? "on" : "off", (v) => put({ enabled: v === "on" })));
  if (cfg.enabled) {
    const sel = h("select", { "aria-label": "Shortcut light effect" }, HINT_EFFECTS.map(([v, label]) => h("option", { value: v, selected: v === cfg.effect }, label)));
    sel.addEventListener("change", () => put({ effect: sel.value }));
    kids.push(field("Effect", sel), h("p", { class: "muted small" }, HINT_HELP[cfg.effect]));
    if (HINT_ONE_COLOR.has(cfg.effect)) {
      const value = cfg.color || "#ffffff";
      kids.push(field("Color", h("div", {},
        colorInput(value, (v, final) => { cfg.color = v; attach(); if (final) { commit({ rerender: false }); previewHints(); } }),
        swatchRow(value, (c) => put({ color: c })))));
    } else if (HINT_COLORS.has(cfg.effect)) {
      if (!cfg.colors) { cfg.colors = ["#ff0080", "#00e5ff"]; attach(); }
      kids.push(colorList({ params: cfg }, cfg.colors));
    }
    if (HINT_MOVING.has(cfg.effect)) kids.push(slider("hint_speed", cfg.speed ?? 1, tweak("speed"), "Speed"));
    kids.push(percent("Rest of the keyboard", Math.round((cfg.dim ?? 0.18) * 100), (v, final) => tweak("dim")(v / 100, final)));
    kids.push(slider("hint_delay", cfg.delay ?? 0.35, tweak("delay"), "Hold time (seconds)"));
    kids.push(h("p", { class: "muted small" }, "Hold time is how long you hold the key before the shortcuts light up, so quick shortcuts like Ctrl+C don't flash."));
    kids.push(h("button", { class: "mini-btn", type: "button", onclick: previewHints }, "Preview on keyboard"));
  }
  box.append(section("Shortcut lights", ...kids));
}

async function previewHints() {
  if (!S.status.running) { toast("Turn the lights on to preview it on the keyboard"); return; }
  const cfg = { enabled: true, effect: "solid", ...(S.profile.shortcut_hints || {}) };
  try { await api("/api/hints/preview", { config: cfg }); } catch (e) { toast(e.message, "err"); }
}

function renderHead() {
  const name = $("#p-name");
  if (document.activeElement !== name) name.value = S.profile.name || "";
  name.style.width = `${Math.max(6, name.value.length + 2)}ch`;
  $("#dirty").hidden = !S.dirty;
  $("#p-meta").textContent = profileMeta();
}

// Where the current profile comes from, under its name
function profileMeta() {
  const all = [...S.lib.presets, ...S.lib.mine, ...(S.lib.community?.profiles || [])];
  const e = all.find((x) => x.id === S.sourceId);
  // not found (e.g. a community profile before the gallery has loaded): its author says enough
  const kind = !e ? (S.profile.author ? null : "New profile")
    : e.kind === "preset" ? "Preset" : e.kind === "mine" ? "Your profile" : "Community";
  const author = (!e || e.kind === "community") && S.profile.author ? S.profile.author.split(" · ")[0] : null;
  const n = S.profile.layers.length;
  return [kind, author, hasReactive(S.profile) ? "reacts to typing" : null, `${n} layer${n > 1 ? "s" : ""}`]
    .filter(Boolean).join(" · ");
}

function setEditing(on) {
  S.editing = on;
  document.body.classList.toggle("editing", on);
  const btn = $("#btn-edit");
  btn.textContent = on ? "Done" : "Edit";
  btn.setAttribute("aria-pressed", String(on));
  store.set("keyglow.editing", on);
  if (!on && S.selection.size) { S.selection.clear(); renderSelection(); }
  updateHint();
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
  if (eff === "music") return "linear-gradient(0deg,#00e5ff 0 30%,transparent 30%) 8% 100%/12% 100% no-repeat,linear-gradient(0deg,#7000ff 0 75%,transparent 75%) 30% 100%/12% 100% no-repeat,linear-gradient(0deg,#ff00c8 0 50%,transparent 50%) 52% 100%/12% 100% no-repeat,linear-gradient(0deg,#00e5ff 0 85%,transparent 85%) 74% 100%/12% 100% no-repeat,linear-gradient(0deg,#7000ff 0 40%,transparent 40%) 96% 100%/12% 100% no-repeat,#05000a";
  if (eff === "swirl") return "conic-gradient(#ff0080,#ffb000,#00e5ff,#7000ff,#ff0080)";
  if (eff === "comet") return "linear-gradient(90deg,#000010 0 30%,#003a50 50%,#00e5ff 72%,#000010 74% 100%)";
  if (eff === "bounce") return "radial-gradient(circle at 70% 35%,#ffb000 0 16%,#5a2a00 26%,#100400 40%)";
  if (eff === "glitch") return "linear-gradient(180deg,#05000a 0 20%,transparent 20% 34%,#05000a 34% 62%,transparent 62% 74%,#05000a 74%),linear-gradient(90deg,#00e5ff 0 30%,#05000a 30% 55%,#ff00c8 55% 80%,#fff 80%)";
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
    const names = l.effect === "music" ? MUSIC_STYLES : STYLE_NAMES;
    const sel = h("select", { "aria-label": "Style" }, Object.entries(names).map(([k, v]) => h("option", { value: k, selected: val === k }, v)));
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
  ["rain", "Rain"], ["heartbeat", "Heartbeat"], ["swirl", "Swirl"], ["comet", "Comet"], ["bounce", "Bounce"],
  ["glitch", "Glitch"], ["reactive", "On key press"], ["music", "Music"]];
const RAINBOW_COLORS = ["#ff0000", "#ff8000", "#ffff00", "#00ff00", "#00ffff", "#0040ff", "#8000ff", "#ff00c0"];
const ONE_ONLY = new Set(["scanner", "heartbeat", "comet", "bounce"]);
const STYLE_NAMES = { key: "Light the key", ripple: "Ripple from the key", row: "Light the row",
  cross: "Light its row and column", burst: "Burst from the key" };
const MUSIC_STYLES = { bars: "Spectrum bars", pulse: "Pulse with the bass", vu: "Volume meter" };
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
    case "music": return fromList("music");
    case "scanner": return { color: "one", anim: "scanner" };
    case "heartbeat": return { color: "one", anim: "heartbeat" };
    case "swirl": return fromList("swirl");
    case "glitch": return fromList("glitch");
    case "comet": return { color: "one", anim: "comet" };
    case "bounce": return { color: "one", anim: "bounce" };
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
      music: ["music", { colors: cs }],
      swirl: ["swirl", { colors: color === "one" ? [one, "#000000"] : cs }],
      glitch: ["glitch", { colors: cs }],
      comet: ["comet", { color: one }],
      bounce: ["bounce", { color: one }],
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
  if (l.effect === "music" && S.status.audio?.error) animKids.push(h("p", { class: "note" }, S.status.audio.error));
  const defaults = S.meta.effects[l.effect]?.defaults || {};
  for (const name of MAIN_PARAMS[l.effect] || []) {
    if (["color", "colors", "keys"].includes(name) || !(name in defaults)) continue;
    if (d.anim === "cycle" && ["angle", "wavelength"].includes(name)) continue;
    if (l.effect === "reactive" && name === "speed" && !["ripple", "burst"].includes(l.params.style)) continue;
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
  if (S.profile) renderHead();
}

const GALLERY_REPO = "https://github.com/HiddenOnLies/KeyGlow-profiles";

async function refreshGallery() {
  try {
    const r = await api("/api/community/refresh", {});
    if (r.error) toast(`Couldn't reach the gallery: ${r.error}`, "err");
    else toast(`${r.count} community profiles`);
  } catch (e) { toast(e.message, "err"); }
  S.lib.community = null;
  renderCards();
}

async function loadCommunity() {
  try {
    S.lib.community = await api("/api/community");
  } catch (e) {
    S.lib.community = { name: "Community", source: S.settings.community_url, profiles: [], error: e.message };
  }
  renderCards();
  if (S.profile) renderHead();
}

function renderCards() {
  if (document.body.classList.contains("lib-closed")) return;
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
    const cv = h("canvas", { width: 224, height: 80 });
    const reacts = e.data?.layers?.some((l) => l.effect === "reactive");
    const card = h("li", {
      class: `card${S.sourceId === e.id ? " current" : ""}`, title: e.description || e.name, tabindex: "0",
      onclick: () => openEntry(e),
      onkeydown: (ev) => { if (ev.key === "Enter") openEntry(e); },
      onmouseenter: () => schedulePeek(e, card),
      onmouseleave: () => stopPeek(),
    }, cv, h("span", { class: "name" }, e.name),
    reacts ? h("span", { class: "badge", title: "Reacts to typing" }, "Reacts") : null,
    e.kind === "mine" ? h("button", { class: "del", title: "Delete", "aria-label": `Delete ${e.name}`, onclick: (ev) => { ev.stopPropagation(); deleteEntry(e); } }, "✕") : null);
    box.append(card);
    cv.entry = e;
    thumbObserver.observe(cv);
  }
  const foot = $("#lib-foot");
  foot.innerHTML = "";
  if (S.tab === "community") {
    const c = S.lib.community;
    if (c?.source) {
      foot.append(`${c.name} · `, h("a", { onclick: openSettings }, "Change gallery"));
    } else {
      const when = c?.fetched ? `updated ${new Date(c.fetched * 1000).toLocaleDateString()}` : "included with the app";
      foot.append(`${c?.name || "KeyGlow community"} · ${when} · `,
        h("a", { onclick: refreshGallery }, "Check for new"), " · ",
        h("a", { href: GALLERY_REPO, target: "_blank", rel: "noopener" }, "Add yours"));
    }
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
  stopPeek();
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

function toggleLibrary(show = document.body.classList.contains("lib-closed")) {
  document.body.classList.toggle("lib-closed", !show);
  $("#btn-library").setAttribute("aria-expanded", String(show));
  store.set("keyglow.libraryOpen", show);
  renderCards();
}

// ---------- Hovering a profile previews it: on screen, and on the keyboard while the lights are on ----------
let peekTimer = null, peekRenew = null, peekCard = null;

function schedulePeek(e, card) {
  clearTimeout(peekTimer);
  if (!e.data || e.id === S.sourceId) return;
  peekTimer = setTimeout(() => startPeek(e, card), 280);
}

function startPeek(e, card) {
  peekCard?.classList.remove("peeking");
  peekCard = card;
  card.classList.add("peeking");
  P.peek = e.data;
  lightTransition("fade");
  invalidatePreview();
  const label = $("#peek-label");
  label.textContent = `Preview: ${e.name} · click to use it`;
  label.hidden = false;
  if (S.status.running) {
    const send = () => api("/api/peek", { profile: e.data }).catch(() => {});
    send();
    clearInterval(peekRenew);
    peekRenew = setInterval(send, 8000); // the engine drops a preview that isn't renewed
  }
}

function stopPeek() {
  clearTimeout(peekTimer);
  clearInterval(peekRenew);
  peekRenew = null;
  if (!P.peek) return;
  P.peek = null;
  peekCard?.classList.remove("peeking");
  peekCard = null;
  $("#peek-label").hidden = true;
  if (!lightTransition.current) lightTransition("fade"); // a click starts a sweep: keep it
  invalidatePreview();
  if (S.status.running) api("/api/peek", { profile: null }).catch(() => {});
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

// ---------- Share to the community gallery ----------
let shareTags = new Set();

function openShare() {
  $("#sh-author").value = S.profile.author || "";
  $("#sh-desc").value = S.profile.description || "";
  shareTags = new Set((S.profile.tags || []).filter((t) => TAGS.includes(t)));
  if (hasReactive(S.profile)) shareTags.add(S.profile.layers.some((l) => l.effect === "reactive") ? "reactive" : "animated");
  const box = $("#sh-tags");
  box.innerHTML = "";
  for (const t of TAGS.filter((x) => x !== "theme")) {
    const b = h("button", { type: "button", class: shareTags.has(t) ? "on" : "" }, t[0].toUpperCase() + t.slice(1));
    b.addEventListener("click", () => { shareTags.has(t) ? shareTags.delete(t) : shareTags.add(t); b.classList.toggle("on"); });
    box.append(b);
  }
  $("#sh-check").hidden = true;
  $("#sh-copy").hidden = true;
  $("#dlg-share").showModal();
}

async function shareProfile() {
  const data = clone(S.profile);
  data.author = $("#sh-author").value.trim();
  data.description = $("#sh-desc").value.trim();
  data.tags = [...shareTags];
  const note = $("#sh-check");
  try {
    const r = await api("/api/gallery/share", { profile: data });
    note.hidden = false;
    if (r.error) { note.textContent = r.error; return; }
    // keep the details in the profile too, so the next share or save has them
    Object.assign(S.profile, { author: data.author, description: data.description, tags: data.tags });
    commit({ rerender: false });
    if (r.url) {
      window.open(r.url, "_blank", "noopener");
      note.textContent = `GitHub is open with ${r.filename} ready. Sign in, then press "Propose changes" and "Create pull request".`;
    } else {
      $("#sh-copy").hidden = false;
      $("#sh-copy").onclick = async () => { await navigator.clipboard.writeText(r.json).catch(() => {}); toast("Profile copied"); };
      window.open(`https://github.com/HiddenOnLies/KeyGlow-profiles/new/main/profiles?filename=${encodeURIComponent(r.filename)}`, "_blank", "noopener");
      note.textContent = `This profile is too big for a link. GitHub is open to create ${r.filename}: press "Copy profile" and paste it there.`;
    }
  } catch (e) { note.hidden = false; note.textContent = e.message; }
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
  $("#sh-go").addEventListener("click", shareProfile);
  $("#set-update-check").addEventListener("click", async () => { $("#set-update-info").textContent = "Checking…"; await checkUpdate(true); });
  $("#update-skip").addEventListener("click", async () => {
    try { showUpdate(await api("/api/update/skip", { version: S.update?.latest || "" })); } catch (e) { toast(e.message, "err"); }
  });
  $("#set-caps").addEventListener("change", capsInfo);
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
      const hadUpdates = S.settings.gallery_updates !== false;
      S.settings = await api("/api/settings", {
        community_url: $("#set-community").value.trim(),
        fps: Math.max(5, Math.min(60, +$("#set-fps").value || 30)),
        apply_last_on_start: $("#set-last").checked,
        start_with_windows: $("#set-autostart").checked,
        start_openrgb: $("#set-openrgb").checked,
        layout: $("#set-layout").value,
        layout_updates: $("#set-layout-updates").checked,
        gallery_updates: $("#set-gallery-updates").checked,
        update_check: $("#set-update").checked,
        caps_lock: $("#set-caps").value,
        caps_lock_color: $("#set-caps-color").value,
        openrgb_device: $("#set-device").value.trim(),
      });
      pollStatus(); // picks up a layout change
      showUpdate(S.update);
      if (old !== S.settings.community_url) { S.lib.community = null; renderCards(); }
      if (!hadUpdates && S.settings.gallery_updates && !S.settings.community_url) refreshGallery();
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
  if (kind === "model" && base === "local") return `Your own layout for the ${lay.title}, made with the layout editor.`;
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

// ---------- Visual layout editor ----------
// Edits a copy of the current layout on the on-screen keyboard; saving stores it on this PC as
// the exact layout for the connected keyboard (it then wins over bundled and workshop layouts).
const LE = { keys: [], sel: null, history: [], known: [] };
const leSnap = () => JSON.stringify(LE.keys);
const leKey = (id) => LE.keys.find((k) => k.id === id);
const leRound = (v) => Math.round(v * 4) / 4;

async function openLayoutEditor() {
  $("#dlg-settings").close();
  stopPeek();
  setEditing(false);
  const lay = S.meta.layout;
  LE.keys = lay.keys.map((k) => ({ id: k.id, x: k.x, y: k.y, w: k.w || 1, h: k.h || 1 }));
  LE.sel = null;
  LE.history = [leSnap()];
  $("#le-title").value = S.status.device || lay.title || "";
  if (!LE.known.length) LE.known = await api("/api/layout/keys").catch(() => []);
  document.body.classList.add("layout-editing");
  $("#layout-editor").hidden = false;
  leMessage();
  leRender();
}

function closeLayoutEditor() {
  document.body.classList.remove("layout-editing");
  $("#layout-editor").hidden = true;
  LE.sel = null;
  buildKeyboard(); // back to the layout KeyGlow uses
  invalidatePreview();
}

function leMessage(text = "", err = false) {
  const m = $("#le-msg");
  m.textContent = text || "Drag a key to move it; drag its right or bottom edge to resize it. Arrow keys move the selected key, Shift+arrows resize it, Delete removes it.";
  m.classList.toggle("err", err);
}

function leClashes() {
  const out = new Set();
  const e = 1e-6;
  for (let i = 0; i < LE.keys.length; i++) {
    for (let j = i + 1; j < LE.keys.length; j++) {
      const a = LE.keys[i], b = LE.keys[j];
      if (a.x < b.x + b.w - e && b.x < a.x + a.w - e && a.y < b.y + b.h - e && b.y < a.y + a.h - e) { out.add(a.id); out.add(b.id); }
    }
  }
  return out;
}

// Rebuilds the on-screen keyboard from the copy being edited (keeps the live colors by key id)
function leRender() {
  const kb = $("#kb");
  const minX = Math.min(...LE.keys.map((k) => k.x), 0), minY = Math.min(...LE.keys.map((k) => k.y), 0);
  const W = Math.max(...LE.keys.map((k) => k.x + k.w), 1) - minX + 0.5;
  const H = Math.max(...LE.keys.map((k) => k.y + k.h), 1) - minY + 0.5;
  LE.view = { minX, minY, W, H };
  kb.innerHTML = "";
  for (const id of Object.keys(keyEls)) delete keyEls[id];
  kb.style.aspectRatio = `${W} / ${H}`;
  kb.style.setProperty("--u", `${kb.clientWidth / W}px`);
  const clash = leClashes();
  const labels = Object.fromEntries(LE.known.map((k) => [k.id, k.label]));
  for (const k of LE.keys) {
    const el = h("div", {
      class: `key${k.id === LE.sel ? " le-sel" : ""}${clash.has(k.id) ? " le-clash" : ""}`, "data-id": k.id,
      style: `left:${((k.x - minX) / W) * 100}%;top:${((k.y - minY) / H) * 100}%;width:${(k.w / W) * 100}%;height:${(k.h / H) * 100}%`,
    }, h("div", { class: "cap" }, S.meta.layout.labels[k.id] ?? labels[k.id] ?? k.id));
    if (lastColors[k.id]) el.style.setProperty("--c", "#" + lastColors[k.id]);
    keyEls[k.id] = el;
    kb.append(el);
  }
  leProps();
  const present = new Set(LE.keys.map((k) => k.id));
  const add = $("#le-add-key");
  add.innerHTML = "";
  for (const k of LE.known.filter((x) => !present.has(x.id))) add.append(h("option", { value: k.id }, k.label === k.id ? k.id : `${k.label} (${k.id})`));
}

function leProps() {
  const box = $("#le-props");
  box.innerHTML = "";
  const k = leKey(LE.sel);
  if (!k) { box.append(h("span", { class: "muted small" }, "Click a key to select it.")); return; }
  const num = (label, prop, min, max) => {
    const inp = h("input", { type: "number", step: 0.25, min, max, value: k[prop] });
    inp.addEventListener("change", () => {
      const v = parseFloat(inp.value);
      if (!Number.isFinite(v)) return;
      k[prop] = Math.min(max, Math.max(min, leRound(v)));
      leCommit();
    });
    return h("label", {}, label, inp);
  };
  box.append(h("label", {}, "Key", h("input", { value: k.id, readonly: true, title: "To use another key, delete this one and add it" })),
    num("X", "x", 0, 60), num("Y", "y", 0, 20), num("Width", "w", 0.25, 12), num("Height", "h", 0.25, 6),
    h("button", { type: "button", class: "small-btn danger", onclick: () => leDelete() }, "Delete key"));
}

function leCommit() {
  const snap = leSnap();
  if (LE.history[LE.history.length - 1] !== snap) LE.history.push(snap);
  leRender();
}

function leDelete() {
  if (!LE.sel) return;
  LE.keys = LE.keys.filter((k) => k.id !== LE.sel);
  LE.sel = null;
  leCommit();
}

function leUndo() {
  if (LE.history.length < 2) return;
  LE.history.pop();
  LE.keys = JSON.parse(LE.history[LE.history.length - 1]);
  if (!leKey(LE.sel)) LE.sel = null;
  leRender();
}

function leAdd() {
  const id = $("#le-add-key").value;
  if (!id) return;
  // a free spot below the keyboard, so it doesn't overlap anything
  const bottom = Math.max(...LE.keys.map((k) => k.y + k.h), 0);
  LE.keys.push({ id, x: 0, y: leRound(bottom + 0.25), w: 1, h: 1 });
  LE.sel = id;
  leCommit();
  leMessage(`Added ${id} below the keyboard: drag it to its place.`);
}

async function leSave() {
  const clash = leClashes();
  if (clash.size) { leMessage(`Some keys overlap (in red): ${[...clash].slice(0, 6).join(", ")}. Move them apart first.`, true); return; }
  // keep the layout starting at 0,0
  const minX = Math.min(...LE.keys.map((k) => k.x)), minY = Math.min(...LE.keys.map((k) => k.y));
  const keys = LE.keys.map((k) => ({ id: k.id, x: k.x - minX, y: k.y - minY, ...(k.w !== 1 ? { w: k.w } : {}), ...(k.h !== 1 ? { h: k.h } : {}) }));
  try {
    const r = await api("/api/layout/save", { title: $("#le-title").value.trim(), keys });
    if (r.error) { leMessage(r.error, true); return; }
    closeLayoutEditor();
    await reloadLayout();
    S.meta.model_layouts = (await api("/api/meta")).model_layouts;
    toast("Layout saved. KeyGlow uses it for this keyboard from now on.");
  } catch (e) { leMessage(e.message, true); }
}

function leExport() {
  const minX = Math.min(...LE.keys.map((k) => k.x)), minY = Math.min(...LE.keys.map((k) => k.y));
  const lay = S.meta.layout;
  const out = {
    title: $("#le-title").value.trim() || lay.title,
    ...(lay.usb ? { usb: [lay.usb] } : {}),
    ...(S.status.device ? { names: [S.status.device] } : {}),
    keys: LE.keys.map((k) => ({ id: k.id, x: k.x - minX, y: k.y - minY, ...(k.w !== 1 ? { w: k.w } : {}), ...(k.h !== 1 ? { h: k.h } : {}) })),
  };
  const name = (out.title || "keyboard").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  const blob = new Blob([JSON.stringify(out, null, 2) + "\n"], { type: "application/json" });
  const a = h("a", { href: URL.createObjectURL(blob), download: `${name}.json` });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  leMessage("Exported. To share it, add it to the KeyGlow workshop (KeyGlow-layouts on GitHub).");
}

function setupLayoutEditor() {
  const kb = $("#kb");
  let drag = null;
  kb.addEventListener("pointerdown", (e) => {
    if (!document.body.classList.contains("layout-editing")) return;
    const el = e.target.closest(".key");
    if (!el) { LE.sel = null; leRender(); return; }
    const k = leKey(el.dataset.id);
    LE.sel = k.id;
    const r = el.getBoundingClientRect();
    const edge = 0.22; // the last 22% of a key resizes it
    const mode = e.clientX > r.right - r.width * edge ? "w" : e.clientY > r.bottom - r.height * edge ? "h" : "move";
    drag = { id: k.id, mode, sx: e.clientX, sy: e.clientY, x: k.x, y: k.y, w: k.w, h: k.h, u: kb.clientWidth / LE.view.W };
    try { kb.setPointerCapture(e.pointerId); } catch { /* keeps working without capture */ }
    leRender();
    e.preventDefault();
  });
  kb.addEventListener("pointermove", (e) => {
    if (!drag) return;
    const k = leKey(drag.id);
    const dx = (e.clientX - drag.sx) / drag.u, dy = (e.clientY - drag.sy) / drag.u;
    if (drag.mode === "move") { k.x = Math.max(0, leRound(drag.x + dx)); k.y = Math.max(0, leRound(drag.y + dy)); }
    else if (drag.mode === "w") k.w = Math.min(12, Math.max(0.25, leRound(drag.w + dx)));
    else k.h = Math.min(6, Math.max(0.25, leRound(drag.h + dy)));
    const el = keyEls[k.id];
    const v = LE.view;
    el.style.left = `${((k.x - v.minX) / v.W) * 100}%`; el.style.top = `${((k.y - v.minY) / v.H) * 100}%`;
    el.style.width = `${(k.w / v.W) * 100}%`; el.style.height = `${(k.h / v.H) * 100}%`;
  });
  kb.addEventListener("pointerup", () => { if (drag) { drag = null; leCommit(); } });
  window.addEventListener("keydown", (e) => {
    if (!document.body.classList.contains("layout-editing") || e.target.matches?.("input, select, textarea")) return;
    if (e.ctrlKey && e.key.toLowerCase() === "z") { e.preventDefault(); leUndo(); return; }
    const k = leKey(LE.sel);
    if (!k) return;
    const step = { ArrowLeft: [-0.25, 0], ArrowRight: [0.25, 0], ArrowUp: [0, -0.25], ArrowDown: [0, 0.25] }[e.key];
    if (step) {
      e.preventDefault();
      if (e.shiftKey) { k.w = Math.max(0.25, k.w + step[0]); k.h = Math.max(0.25, k.h + step[1]); }
      else { k.x = Math.max(0, k.x + step[0]); k.y = Math.max(0, k.y + step[1]); }
      leCommit();
    } else if (e.key === "Delete") { e.preventDefault(); leDelete(); }
  });
  $("#set-layout-edit").addEventListener("click", openLayoutEditor);
  $("#le-undo").addEventListener("click", leUndo);
  $("#le-cancel").addEventListener("click", closeLayoutEditor);
  $("#le-save").addEventListener("click", leSave);
  $("#le-export").addEventListener("click", leExport);
  $("#le-add").addEventListener("click", leAdd);
}

function fillLayoutSelect() {
  const sel = $("#set-layout");
  const models = S.meta.model_layouts || [];
  const tag = (m) => (m.workshop ? " (workshop" + (m.verified ? ")" : ", untested)") : (m.verified ? "" : " (untested)"));
  sel.innerHTML = "";
  sel.append(
    h("option", { value: "auto" }, "Automatic (as OpenRGB reports it)"),
    h("optgroup", { label: "Keyboard models" }, ...models.map((m) => h("option", { value: m.name }, m.title + tag(m)))),
    h("optgroup", { label: "Standard layouts" }, ...S.meta.layouts.map((l) => h("option", { value: l.name }, l.title))),
  );
  const want = S.settings.layout || "auto";
  sel.value = [...sel.options].some((o) => o.value === want) ? want : "auto";
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
    S.meta.model_layouts = (await api("/api/meta")).model_layouts;
    fillLayoutSelect();
    pollStatus(); // a better layout may have arrived
  } catch (e) { box.textContent = ""; toast(e.message, "err"); }
}

function capsInfo() {
  const mode = $("#set-caps").value;
  const has = S.meta.layout.caps_lock_indicator;
  const box = $("#set-caps-info");
  if (!(S.meta.layout.keys || []).some((k) => k.id === "CAPSLOCK")) {
    box.textContent = "This keyboard has no Caps Lock key.";
  } else if (mode === "off") {
    box.textContent = "The Caps Lock key shows the profile's colors as usual.";
  } else if (mode === "on") {
    box.textContent = "The Caps Lock key lights up in this color while Caps Lock is on.";
  } else if (has === true) {
    box.textContent = "This keyboard has its own Caps Lock indicator, so KeyGlow leaves the key alone.";
  } else if (has === false) {
    box.textContent = "This keyboard has no Caps Lock indicator, so the key lights up in this color while Caps Lock is on.";
  } else {
    box.textContent = "KeyGlow doesn't know if this keyboard has its own indicator, so the key lights up while Caps Lock is on.";
  }
}

function openSettings() {
  fillLayoutSelect();
  // the workshop may have brought new models since the app started
  api("/api/meta").then((m) => { S.meta.model_layouts = m.model_layouts; fillLayoutSelect(); }).catch(() => {});
  $("#set-layout-info").textContent = layoutInfo(S.meta.layout);
  $("#set-layout-updates").checked = S.settings.layout_updates !== false;
  $("#set-gallery-updates").checked = S.settings.gallery_updates !== false;
  $("#set-update").checked = S.settings.update_check !== false;
  showUpdate(S.update);
  $("#set-caps").value = S.settings.caps_lock || "auto";
  $("#set-caps-color").value = S.settings.caps_lock_color || "#ffffff";
  capsInfo();
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
    else if (act === "share") openShare();
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
  // when the keyboard stays unreachable for a few seconds, a banner explains it (without blocking the app)
  offlinePolls = st.connected ? 0 : offlinePolls + 1;
  showConnBanner(st);
  const dev = $("#device");
  dev.classList.toggle("ok", !!st.connected);
  dev.classList.toggle("bad", !st.connected);
  $("#device-text").textContent = st.connected ? st.device : "Keyboard not connected";
  dev.title = st.connected ? "Connected through OpenRGB" : `${st.error || "Open OpenRGB and start its SDK Server."}\nClick to retry.`;
  const pw = $("#power");
  pw.classList.toggle("on", !!st.running);
  document.body.classList.toggle("lights-off", !st.running);
  pw.setAttribute("aria-checked", String(!!st.running));
  $("#power-text").textContent = st.running ? "On" : "Off";
  const pill = $("#game-pill");
  pill.hidden = !st.override;
  if (st.override) {
    pill.textContent = `${st.override.reason} · ${st.override.profile}`;
    pill.title = `Playing ${st.override.reason}: using "${st.override.profile}"`;
  }
}

// The banner explains what's wrong: no keyboard, or another RGB program fighting for it
function showConnBanner(st) {
  const banner = $("#conn-banner");
  const apps = st.conflicts || [];
  let text = "";
  if (!st.connected && offlinePolls >= 3) {
    text = st.devices_seen?.length ? "OpenRGB is running but doesn't see your keyboard."
      : "Keyboard not connected. You're seeing a preview only.";
    if (apps.length) text += ` Open RGB programs that may hold it: ${apps.join(", ")}.`;
  } else if (st.connected && apps.length) {
    text = `${apps.join(", ")} ${apps.length > 1 ? "are" : "is"} open and also ${apps.length > 1 ? "control" : "controls"} this keyboard. Close it if the lights flicker or don't change.`;
  }
  banner.hidden = !text;
  if (text) $("#conn-text").textContent = text;
  $("#conn-help").hidden = !!st.connected;
  $("#conn-rescan").hidden = !!st.connected;
}

async function rescanDevices() {
  try {
    const r = await api("/api/rescan", {});
    if (r.result === "requested") toast("OpenRGB is looking for devices again. This takes a few seconds.");
    else if (r.result === "unsupported") toast("Your OpenRGB can't do this from KeyGlow (it needs OpenRGB 1.0 or newer). In OpenRGB, press Rescan Devices.", "err");
    else toast("Couldn't reach OpenRGB. Is it open?", "err");
    setTimeout(pollStatus, 4000);
  } catch (e) { toast(e.message, "err"); }
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
  const apps = S.status.conflicts || [];
  $("#con-conflicts").textContent = apps.length
    ? `Open right now: ${apps.join(", ")}. If one of them controls your keyboard, close it (also from the tray), then try again.`
    : "NGENUITY, iCUE, Synapse, Armoury Crate… Two programs writing to the keyboard fight each other.";
  const seen = S.status.devices_seen || [];
  $("#con-seen").hidden = !seen.length;
  $("#con-seen").textContent = `OpenRGB sees: ${seen.join(", ")}.`;
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

// ---------- New version notice ----------
function showUpdate(u) {
  S.update = u;
  const pill = $("#update-pill");
  pill.hidden = !(u?.newer && !u.skipped && S.settings.update_check !== false);
  if (!pill.hidden) {
    const link = $("#update-link");
    link.textContent = `KeyGlow ${u.latest} is out`;
    link.href = u.url;
    link.title = `You have ${u.current}. Open the release page to download it.`;
  }
  const info = $("#set-update-info");
  if (info) {
    info.textContent = !u ? "" : u.error && !u.latest ? `You have ${u.current}. Couldn't check: ${u.error}`
      : u.newer ? `You have ${u.current}; ${u.latest} is out.` : `You have ${u.current}, the latest version.`;
  }
}

async function checkUpdate(force = false) {
  try { showUpdate(await api(force ? "/api/update/check" : "/api/update", force ? {} : undefined)); }
  catch { /* offline: no notice */ }
}

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
    const cards = $("#cards");
    cards.classList.remove("swap");
    void cards.offsetWidth; // restart the fade
    cards.classList.add("swap");
    cards.scrollTop = 0;
  }));
  $("#search").addEventListener("input", renderCards);
  $("#btn-library").addEventListener("click", () => toggleLibrary());
  $("#btn-edit").addEventListener("click", () => setEditing(!S.editing));
  $("#btn-edit-done").addEventListener("click", () => setEditing(false));
  $("#conn-help").addEventListener("click", openConnect);
  $("#conn-rescan").addEventListener("click", rescanDevices);
  $("#con-rescan").addEventListener("click", rescanDevices);
  window.addEventListener("blur", stopPeek);
  // the quick start row scrolls sideways with the mouse wheel
  const fx = $("#effects");
  fx.addEventListener("wheel", (e) => {
    if (Math.abs(e.deltaY) <= Math.abs(e.deltaX) || fx.scrollWidth <= fx.clientWidth) return;
    fx.scrollLeft += e.deltaY;
    e.preventDefault();
  }, { passive: false });

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
    if (e.target.matches?.("input, textarea") || document.body.classList.contains("layout-editing")) return;
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
  setupLayoutEditor();
  setupGames();

  await Promise.all([loadLibrary(), pollStatus()]);
  toggleLibrary(store.get("keyglow.libraryOpen", true));
  setEditing(store.get("keyglow.editing", false));
  // a new window shows what the keyboard is playing now, so opening it never changes the lights
  const active = (await api("/api/active").catch(() => ({}))).profile;
  const start = active || S.settings.last_profile || S.lib.presets[0]?.data;
  const all = [...S.lib.presets, ...S.lib.mine];
  loadProfile(start || { name: "My profile", layers: [newLayer("solid")] }, {
    sourceId: all.find((p) => p.data?.name === start?.name)?.id ?? null,
  });
  setInterval(pollStatus, 2000);
  checkUpdate();
  setTimeout(checkUpdate, 20000); // the check at startup runs in the background
  setInterval(tick, 1000 / 40);
}

init().catch((e) => {
  document.body.innerHTML = `<div class="empty" style="padding-top:30vh">KeyGlow couldn't start: ${e.message}</div>`;
});
