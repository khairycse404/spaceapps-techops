# 🛰️ NASA Space Apps Cairo — Tech Ops Mission Control (Phase 1: 12 Rooms)

Serverless, free, always-on. Static site on **GitHub Pages** + **Firebase Realtime Database**.
No laptop has to stay open: the cloud holds the state.

| File | What it does |
|---|---|
| `index.html` | Mission Control dashboard (9 Tech Ops phones + main-hall monitor) |
| `check.html` | **Mobile Room Inspector** (runs on any phone, tests Wi-Fi & reports Data Show) |
| `sos.html` | Mentor emergency page, opened from the podium QR (`sos.html?room=5`) |
| `qr.html` | Printable A4 QR cards for the 12 podiums |
| `dist/TechOps_RoomInspector.exe` | **Standalone Windows .EXE app** (no Python required, double-click to run!) |
| `check_room.py` | Desktop GUI app source code (Tkinter + requests) |
| `build_exe.bat` | 1-Click script to re-compile the `.exe` |
| `firebase-config.js` | Firebase Realtime Database URL configuration |
| `theme.css` | Shared dark space theme |
| `database.rules.json` | Optional tighter Firebase security rules |

---

## ⏱️ 3-minute setup

### Step 1 — Firebase Realtime Database (≈60 s)
1. Go to <https://console.firebase.google.com> → **Add project** → name it `spaceapps-techops` → disable Google Analytics → **Create**.
2. Left menu **Build → Realtime Database → Create Database**. Pick any location, then choose **Start in test mode** → **Enable**.
3. On the **Data** tab copy the URL at the top, e.g. `https://spaceapps-techops-default-rtdb.firebaseio.com`
   (EU/Asia locations look like `https://…-default-rtdb.europe-west1.firebasedatabase.app` — both work).
4. Open `firebase-config.js` and paste it:
   ```js
   export const FIREBASE_DATABASE_URL = "https://spaceapps-techops-default-rtdb.firebaseio.com";
   ```
5. *(Recommended)* **Rules** tab → paste the contents of `database.rules.json` → **Publish**.
   It keeps test-mode openness for `rooms/` and `sos_log/` only and rejects invalid statuses.
   Test mode itself expires after 30 days, which is plenty for the bootcamp.

> ⚠️ Anyone who knows the URL can write to the database (needed so mentors need no login). Don't post the link publicly; wipe the project after the event.

### Step 2 — Push to GitHub & enable Pages (≈2 min)
```powershell
cd "d:\Nasa Space Apps - Tech Ops"
git init
git add .
git commit -m "Tech Ops Phase 1"
git branch -M main
git remote add origin https://github.com/<username>/spaceapps-techops.git
git push -u origin main
```
(Create the empty repo first at <https://github.com/new>, name `spaceapps-techops`, **Public**.)

Then on GitHub: **Settings → Pages → Build and deployment → Source: “Deploy from a branch” → Branch `main` / `/ (root)` → Save**.
After ~1 minute your site is live at `https://<username>.github.io/spaceapps-techops/`.

### Step 3 — Print the QR codes
Open `https://<username>.github.io/spaceapps-techops/qr.html` → it auto-detects the URL → **Print** (A4, scale 100%) → cut & tape one on each podium.
Scan one with your phone to confirm it opens the right room.

### Step 4 — Room-check laptops
```powershell
pip install requests
python check_room.py
```
First run asks for the Firebase URL and your name (saved to `config.json`, git-ignored). Then type a room number → projector pattern appears on the Data Show → press **G** or **B** → results go to the dashboard.

---

## 👥 How the team uses it

**Dashboard (`index.html`)**
1. Type your name → **Save** (stored in your phone's `localStorage`).
2. Tap **🔊 Enable Audio & Vibration Alerts** once per phone/session (browsers require a tap). Screen stays awake while enabled. The main-hall monitor should do this too.
3. When a room goes red: siren every 4 s until someone taps **🏃‍♂️ Claim Task** (claiming is race-safe: first tap wins). Everyone sees *“⚙️ Name is heading to Room X”*, and the mentor's phone shows *“🏃‍♂️ Name is on the way…”*.
4. After fixing it tap **✅ Mark Resolved** → room returns to READY and the event is stored in `sos_log` (handy for the post-event report). **↩ Release** hands the task back if you can't go.
5. **✍️ Quick Manual Check** marks a room Ready/Warning (or resets it) from a phone.

**Mentor (`sos.html?room=N`)**: tap one of 4 big buttons (optional note first). Multiple issues add up on the same alert.

**`check_room.py` options**
- `python check_room.py --reconfigure` — change URL / name.
- `config.json` extras: `min_mbps` (5), `max_ping_ms` (150), `min_wifi_percent` (40) decide READY vs WARNING; `projector_position` e.g. `"1920,0"` opens the pattern on a second monitor.
- Press **Esc** on the pattern to skip a room without uploading.
- If a room has an open SOS, the script updates metrics but **keeps the SOS status** (never silently clears it).

### Database layout
```
rooms/room_<1..12>:
  status: UNCHECKED | READY | WARNING | SOS
  ping_ms, download_mbps, wifi_signal, datashow ("OK"|"Issue"), checked_by, updated_at, source, note
  sos: { issue, note, created_at, claimed_by, claimed_at }      ← exists only while an SOS is open
sos_log/<push-id>: { room, issue, note, reported_at, claimed_by, resolved_by, resolved_at }
```
Manual test from any terminal:
```powershell
curl.exe -X PATCH "https://<project>-default-rtdb.firebaseio.com/rooms/room_3.json" -d "{\"status\":\"READY\",\"checked_by\":\"test\"}"
```

---

## 🧪 Pre-event checklist (5 min)
- [ ] Dashboard shows **Live** (green pill) and 12 grey cards.
- [ ] `python check_room.py` on a laptop → Room 1 turns green on your phone.
- [ ] Scan QR for room 1 → tap a button → dashboard card flashes red + siren.
- [ ] Tap **Claim Task** → mentor phone says “… is on the way”.
- [ ] **Mark Resolved** → card green, mentor phone says “All fixed”.

## 🛠️ Troubleshooting
| Symptom | Fix |
|---|---|
| Red “Firebase is not configured” banner | Paste the URL in `firebase-config.js` and push again (hard-refresh, `Ctrl+Shift+R`). |
| Page is blank when opening the HTML file directly | ES modules need http(s). Use GitHub Pages or `python -m http.server 8000` locally. |
| `Permission denied` / HTTP 401 | Rules not in test mode (or expired). Re-publish `database.rules.json`. |
| No sound on iPhone vibration | iOS Safari doesn't support `navigator.vibrate`; sound still works after tapping the Enable button. |
| Projector pattern shows on the laptop, not the Data Show | Press `Win+P` → *Duplicate*, or set `projector_position` in `config.json`. |
| Python ping shows `None` | ICMP blocked on that Wi-Fi; the script falls back to a TCP timing test, and flags “no internet” only if both fail. |

## 🚀 Next: Phase 2
Main Orientation Hall tools — Presentation/Data Show control, Stream monitoring, External Mic hand-off management.
