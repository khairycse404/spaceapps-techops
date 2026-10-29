// ============================================================================
//  NASA Space Apps Cairo – Tech Ops | Firebase Configuration & Shared Helpers
// ============================================================================

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getDatabase } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-database.js";

export const FIREBASE_DATABASE_URL = "https://spaceapps-cairo-techops-default-rtdb.firebaseio.com";

// Number of workshop rooms (rooms 1..ROOM_COUNT).
export const ROOM_COUNT = 15;

// Optional friendly names / room codes shown next to "Room 01" (e.g. "D142").
export const ROOM_NAMES = {
  1: "D142",
  2: "D145",
  3: "D148",
  4: "D150",
  5: "D154",
  6: "C129",
  7: "C132",
  8: "C134",
  9: "D242",
  10: "D245",
  11: "D248",
  12: "D250",
  13: "D254",
  14: "C232",
  15: "C234",
};

// The 5 Rooms Strike Team members (Karim - Tasbeeh - Omar - Lojine - Khairy)
export const ROOMS_TEAM = [
  { id: "karim",   name: "Karim",   short: "Karim",   en: "Karim" },
  { id: "tasbeeh", name: "Tasbeeh", short: "Tasbeeh", en: "Tasbeeh" },
  { id: "omar",    name: "Omar",    short: "Omar",    en: "Omar" },
  { id: "lojine",  name: "Lojine",  short: "Lojine",  en: "Lojine" },
  { id: "khairy",  name: "Khairy",  short: "Khairy",  en: "Khairy" },
];

// Holder options for equipment: Materials Room + the 5 Team Members
export const EQUIPMENT_HOLDERS = [
  { id: "materials_room", name: "Materials Room", icon: "📦", isPerson: false },
  { id: "karim",          name: "Karim",          icon: "👤", isPerson: true },
  { id: "tasbeeh",        name: "Tasbeeh",        icon: "👤", isPerson: true },
  { id: "omar",           name: "Omar",           icon: "👤", isPerson: true },
  { id: "lojine",         name: "Lojine",         icon: "👤", isPerson: true },
  { id: "khairy",         name: "Khairy",         icon: "👤", isPerson: true },
];

// 4 live status choices for each of the 5 Rooms Team members
export const MEMBER_STATUSES = [
  { id: "STANDBY",  label: "🟢 Standby",     short: "🟢 Standby",  cls: "st-standby" },
  { id: "CHECKING", label: "🔍 Inspecting",  short: "🔍 Checking", cls: "st-checking" },
  { id: "SOS",      label: "🚨 In SOS",      short: "🚨 In SOS",   cls: "st-sos" },
  { id: "HALL",     label: "⏸️ On Break",    short: "⏸️ Break",    cls: "st-hall" },
];

// Backup Material Inventory: 2 Mac Converters + 4 Power Strips
export const EQUIPMENT_ITEMS = [
  { id: "mac_1",   type: "mac",   icon: "💻🔌", title: "Mac Converter #1", sub: "USB-C to HDMI Adapter #1" },
  { id: "mac_2",   type: "mac",   icon: "💻🔌", title: "Mac Converter #2", sub: "USB-C to HDMI Adapter #2" },
  { id: "strip_1", type: "strip", icon: "⚡🔌", title: "Power Strip #1",   sub: "Extension Cord #1" },
  { id: "strip_2", type: "strip", icon: "⚡🔌", title: "Power Strip #2",   sub: "Extension Cord #2" },
  { id: "strip_3", type: "strip", icon: "⚡🔌", title: "Power Strip #3",   sub: "Extension Cord #3" },
  { id: "strip_4", type: "strip", icon: "⚡🔌", title: "Power Strip #4",   sub: "Extension Cord #4" },
];

export const DEFAULT_HOLDERS = {
  mac_1: "materials_room",
  mac_2: "materials_room",
  strip_1: "materials_room",
  strip_2: "materials_room",
  strip_3: "materials_room",
  strip_4: "materials_room",
};

// Database key for a room — MUST match what check_room.py writes (rooms/room_<id>).
export const roomKey = (n) => `room_${n}`;

// ============================================================================
//  ADMIN-EDITABLE CONFIG  (everything below can be changed from admin.html)
//  The arrays/objects exported above are mutated IN PLACE, so every page that
//  imported them automatically sees the new team, materials, names and text.
// ============================================================================
export const THRESHOLDS = { min_mbps: 5, max_ping_ms: 150, min_wifi_percent: 40 };
export const SITE = {
  title_main: "TECH OPS",
  title_accent: "MISSION CONTROL",
  subtitle: "NASA Space Apps Cairo · Bootcamp",
};
export const EQUIPMENT_TYPES = ["mac", "strip", "other"];
export const DEFAULT_ICON_BY_TYPE = { mac: "💻🔌", strip: "⚡🔌", other: "🧰" };

// Factory defaults (snapshot taken before any remote config is applied)
export const FACTORY = {
  team: ROOMS_TEAM.map((m) => ({ id: m.id, name: m.name })),
  equipment: EQUIPMENT_ITEMS.map((i) => ({ ...i })),
  room_count: ROOM_COUNT,
  site: { ...SITE },
  thresholds: { ...THRESHOLDS },
};

const slug = (s) => String(s ?? "").toLowerCase().replace(/[^a-z0-9_]/g, "");
const clean = (s, max = 60) => String(s ?? "").trim().slice(0, max);
const cleanIcon = (s) => String(s ?? "").replace(/[<>&"'`]/g, "").trim().slice(0, 12);

// Firebase may return a list as an array OR as an object — normalise both.
export function toList(v) {
  if (!v) return [];
  if (Array.isArray(v)) return v.filter(Boolean);
  if (typeof v === "object") return Object.values(v).filter(Boolean);
  return [];
}

export function rebuildHolders() {
  EQUIPMENT_HOLDERS.splice(
    0, EQUIPMENT_HOLDERS.length,
    { id: "materials_room", name: "Materials Room", icon: "📦", isPerson: false },
    ...ROOMS_TEAM.map((m) => ({ id: m.id, name: m.name, icon: "👤", isPerson: true })),
  );
}

let _lastCfgJson = "";
export function applyRemoteConfig(cfg) {
  cfg = cfg && typeof cfg === "object" ? cfg : {};

  // Team members
  const seenT = new Set();
  let team = toList(cfg.team)
    .map((m) => ({ id: slug(m.id), name: clean(m.name, 30) }))
    .filter((m) => m.id && m.name && m.id !== "materials_room" && !seenT.has(m.id) && seenT.add(m.id));
  if (!team.length) team = FACTORY.team;
  ROOMS_TEAM.splice(0, ROOMS_TEAM.length,
    ...team.map((m) => ({ id: m.id, name: m.name, short: m.name, en: m.name })));
  rebuildHolders();

  // Materials / equipment
  const seenE = new Set();
  let eq = toList(cfg.equipment)
    .map((i) => {
      const type = EQUIPMENT_TYPES.includes(i.type) ? i.type : "other";
      return {
        id: slug(i.id), type,
        icon: cleanIcon(i.icon) || DEFAULT_ICON_BY_TYPE[type],
        title: clean(i.title, 40), sub: clean(i.sub, 60),
      };
    })
    .filter((i) => i.id && i.title && !seenE.has(i.id) && seenE.add(i.id));
  // An admin may deliberately delete every item, so only fall back to the
  // factory list when the admin has never customised the materials.
  if (!cfg.equipment_custom && !eq.length) eq = FACTORY.equipment;
  EQUIPMENT_ITEMS.splice(0, EQUIPMENT_ITEMS.length, ...eq);

  // Optional room names (stored as room_1, room_2, ...)
  const parsedNames = {};
  for (const [k, v] of Object.entries(cfg.room_names || {})) {
    const m = /^room_(\d+)$/.exec(k);
    if (m && v) parsedNames[Number(m[1])] = clean(v, 40);
  }
  if (Object.keys(parsedNames).length > 0) {
    for (const k of Object.keys(ROOM_NAMES)) delete ROOM_NAMES[k];
    Object.assign(ROOM_NAMES, parsedNames);
  }

  // Site text + thresholds
  const s = cfg.site || {};
  SITE.title_main = clean(s.title_main, 40) || FACTORY.site.title_main;
  SITE.title_accent = clean(s.title_accent, 40) || FACTORY.site.title_accent;
  SITE.subtitle = clean(s.subtitle, 80) || FACTORY.site.subtitle;
  const t = cfg.thresholds || {};
  for (const k of Object.keys(THRESHOLDS)) {
    const n = Number(t[k]);
    THRESHOLDS[k] = Number.isFinite(n) && n >= 0 ? n : FACTORY.thresholds[k];
  }

  // Remember for instant first paint next time
  try {
    const { admin_pin_hash, ...rest } = cfg;
    const json = JSON.stringify(rest);
    if (json !== _lastCfgJson) { _lastCfgJson = json; localStorage.setItem("techops_cfg_cache", json); }
  } catch { /* ignore */ }

  if (Number(cfg.room_count) >= 1) return Math.round(Number(cfg.room_count));
  return null;
}

// Apply the cached config immediately so pages paint with the right names.
try { applyRemoteConfig(JSON.parse(localStorage.getItem("techops_cfg_cache") || "{}")); } catch { /* ignore */ }

export const CONFIG_OK = !FIREBASE_DATABASE_URL.includes("YOUR-PROJECT-ID");

const app = initializeApp({ databaseURL: FIREBASE_DATABASE_URL });
export const db = getDatabase(app);

// Re-export the SDK helpers so every page uses the exact same pinned version.
export {
  ref, onValue, update, set, push, runTransaction, serverTimestamp,
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-database.js";

// REST helpers so mobile browsers connect instantly even if carrier blocks WebSockets
export async function restGet(path = "") {
  const clean = path.replace(/^\/+|\/+$/g, "");
  const url = `${FIREBASE_DATABASE_URL}/${clean ? clean + ".json" : ".json"}?_t=${Date.now()}`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function restPatch(path, data) {
  const clean = path.replace(/^\/+|\/+$/g, "");
  const url = `${FIREBASE_DATABASE_URL}/${clean ? clean + ".json" : ".json"}`;
  const res = await fetch(url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// PUT replaces the whole node (used for lists such as team / equipment)
export async function restPut(path, data) {
  const clean = path.replace(/^\/+|\/+$/g, "");
  const url = `${FIREBASE_DATABASE_URL}/${clean}.json`;
  const res = await fetch(url, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function restDelete(path) {
  const clean = path.replace(/^\/+|\/+$/g, "");
  const url = `${FIREBASE_DATABASE_URL}/${clean}.json`;
  const res = await fetch(url, { method: "DELETE" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return true;
}

// Shared helpers -------------------------------------------------------------
export function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

export function pad2(n) { return String(n).padStart(2, "0"); }

export const MISSING_CONFIG_MESSAGE =
  "⚠️ Firebase is not configured yet. Open <code>firebase-config.js</code> and paste your " +
  "Realtime Database URL into <code>FIREBASE_DATABASE_URL</code>, then push again.";
