// ============================================================================
//  NASA Space Apps Cairo – Tech Ops | Firebase Configuration & Shared Helpers
// ============================================================================

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getDatabase } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-database.js";

export const FIREBASE_DATABASE_URL = "https://spaceapps-cairo-techops-default-rtdb.firebaseio.com";

// Number of workshop rooms (rooms 1..ROOM_COUNT).
export const ROOM_COUNT = 12;

// Optional friendly names shown next to "Room 05" (leave empty if not needed).
export const ROOM_NAMES = {};

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
