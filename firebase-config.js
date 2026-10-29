// ============================================================================
//  NASA Space Apps Cairo – Tech Ops | Firebase configuration
//  >>> The ONLY thing you must edit is FIREBASE_DATABASE_URL below. <<<
//
//  Firebase Console → Build → Realtime Database → copy the URL at the top of
//  the "Data" tab. It looks like one of:
//     https://my-project-default-rtdb.firebaseio.com
//     https://my-project-default-rtdb.europe-west1.firebasedatabase.app
//  (no trailing slash, no ".json")
// ============================================================================

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getDatabase } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-database.js";

export const FIREBASE_DATABASE_URL = "https://spaceapps-cairo-techops-default-rtdb.firebaseio.com";

// Number of workshop rooms (rooms 1..ROOM_COUNT).
export const ROOM_COUNT = 12;

// Optional friendly names shown next to "Room 05" (leave empty if not needed).
// Example: { 5: "Data Science", 9: "Rocketry" }
export const ROOM_NAMES = {};

// The 5 Rooms Strike Team members (كريم . تسبيح . عمر . خيري . لجين)
export const ROOMS_TEAM = [
  { id: "karim",   name: "كريم · Karim",    short: "كريم",   en: "Karim" },
  { id: "tasbeeh", name: "تسبيح · Tasbeeh", short: "تسبيح",  en: "Tasbeeh" },
  { id: "omar",    name: "عمر · Omar",      short: "عمر",    en: "Omar" },
  { id: "khairy",  name: "خيري · Khairy",   short: "خيري",   en: "Khairy" },
  { id: "logain",  name: "لجين · Logain",   short: "لجين",   en: "Logain" },
];

// 4 live status choices for each of the 5 Rooms Team members
export const MEMBER_STATUSES = [
  { id: "STANDBY",  label: "🟢 متاح · Standby",    short: "🟢 متاح",    cls: "st-standby" },
  { id: "CHECKING", label: "🔍 بيفحص · Checking",  short: "🔍 بيفحص",   cls: "st-checking" },
  { id: "SOS",      label: "🚨 طوارئ · In SOS",    short: "🚨 طوارئ",   cls: "st-sos" },
  { id: "HALL",     label: "⏸️ القاعة الرئيسية / Break", short: "⏸️ استراحة", cls: "st-hall" },
];

// Backup Material Inventory: 2 Mac Converters + 4 Power Strips (المشتركات)
export const EQUIPMENT_ITEMS = [
  { id: "mac_1",   type: "mac",   icon: "💻🔌", title: "Mac Converter #1", ar: "كونڤرتر ماك ١" },
  { id: "mac_2",   type: "mac",   icon: "💻🔌", title: "Mac Converter #2", ar: "كونڤرتر ماك ٢" },
  { id: "strip_1", type: "strip", icon: "⚡🔌", title: "Power Strip #1",   ar: "مشترك كهرباء ١" },
  { id: "strip_2", type: "strip", icon: "⚡🔌", title: "Power Strip #2",   ar: "مشترك كهرباء ٢" },
  { id: "strip_3", type: "strip", icon: "⚡🔌", title: "Power Strip #3",   ar: "مشترك كهرباء ٣" },
  { id: "strip_4", type: "strip", icon: "⚡🔌", title: "Power Strip #4",   ar: "مشترك كهرباء ٤" },
];

// Database key for a room — MUST match what check_room.py writes (rooms/room_<id>).
export const roomKey = (n) => `room_${n}`;

export const CONFIG_OK = !FIREBASE_DATABASE_URL.includes("YOUR-PROJECT-ID");

const app = initializeApp({ databaseURL: FIREBASE_DATABASE_URL });
export const db = getDatabase(app);

// Re-export the SDK helpers so every page uses the exact same pinned version.
export {
  ref, onValue, update, set, push, runTransaction, serverTimestamp,
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-database.js";

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
