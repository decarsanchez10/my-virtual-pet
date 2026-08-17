# Chirpy 🐣 — Desktop Pet Reminder

A tiny always-on-top pet that sits on your screen and pops up cute
speech-bubble reminders for your OJT time-in/out and schoolwork
deadlines, powered by Groq's **free** LLM API.

## 1. Install Python (if you don't have it)

Download from https://www.python.org/downloads/ and during install,
check **"Add Python to PATH"**.

## 2. Get a free Groq API key

1. Go to https://console.groq.com/keys
2. Sign up (free) and click "Create API Key"
3. Copy the key (starts with `gsk_...`)

## 3. Set up the project

Open **PowerShell** and run:

```powershell
mkdir $HOME\ChirpyPet
cd $HOME\ChirpyPet
```

Copy `pet.py` and `config.json` into that folder (drag and drop them
in File Explorer, or save them there directly).

Install the one dependency:

```powershell
pip install requests
```

## 4. Add your API key

Open `config.json` in Notepad:

```powershell
notepad config.json
```

Replace `PASTE_YOUR_GROQ_API_KEY_HERE` with your real key. Save and close.

## 5. Set your schedule

Still in `config.json`, edit the `daily_reminders` section:

- `"time"` — 24-hour format, e.g. `"08:00"` for 8 AM
- `"days"` — which days it applies (`mon`–`sun`)
- `"message_hint"` — what you want Chirpy to remind you about

For one-off deadlines (like a project due date), edit
`one_time_deadlines`:

- `"datetime"` — format `"YYYY-MM-DD HH:MM"` (24-hour)
- `"remind_before_minutes"` — how many minutes *before* the deadline
  to ping you (e.g. `1440` = 1 day before, `60` = 1 hour before)

You can add as many entries as you want — just copy the `{ }` blocks.

## 6. Run it

```powershell
python pet.py
```

Chirpy should appear in the bottom-right corner of your screen.

- **Double-click** the pet → get a random cute check-in message
- **Right-click** the pet → close it
- **Drag** the pet → move it anywhere on screen

## 7. Make it start automatically every day (optional)

To have Chirpy launch automatically when you log into Windows:

1. Press `Win + R`, type `shell:startup`, hit Enter — this opens your
   Startup folder.
2. In that folder, create a file named `start_chirpy.vbs` with this
   content (Notepad is fine):

   ```vbscript
   Set WshShell = CreateObject("WScript.Shell")
   WshShell.Run "pythonw C:\Users\YOURNAME\ChirpyPet\pet.py", 0
   ```

   (Replace `YOURNAME` with your actual Windows username, and adjust
   the path if you saved the folder elsewhere. Using `pythonw`
   instead of `python` prevents a console window from popping up.)

3. Save it. Now Chirpy launches silently every time you log in.

## Notes

- If Groq's API is unreachable (no internet, key expired, free-tier
  rate limit hit) Chirpy just uses a canned fallback message instead
  of crashing — so it always still reminds you on time.
- Groq's free tier is generous for this use case (a handful of short
  messages a day), so you shouldn't hit any billing surprises.
- All your schedule data stays local in `config.json` — nothing is
  stored anywhere except your machine and the momentary Groq API call.
