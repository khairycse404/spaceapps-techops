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
