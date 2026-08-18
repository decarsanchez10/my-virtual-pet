# Spidey 🕷️ — Desktop Spider-Man Reminder

A tiny always-on-top desktop pet that sits on your screen, hangs from the top of your monitor on a web, and pops up custom speech-bubble reminders for your schedule, powered by Groq's **free** LLM API.

---

## Features
*   **Web-Slinging Animations**: Spidey slides down smoothly from the top of the screen when launching and slides back up off-screen when exiting.
*   **Gentle Bobbing**: Spidey gently bobs up and down on his web string while idle to feel alive.
*   **Modern Dark UI Speech Bubbles**: Sleek dark-mode notification cards (`#0f0f12`) with a thin Spider-Man red accent border and modern typography.
*   **Sound Notifications**: Friendly audio chime notifications played asynchronously on reminder events.
*   **AI-Powered Personality**: Integrates with Groq API so Spidey speaks in character like a supportive web-slinging friend!

---

## 1. Setup Instructions

1.  **Install Python**: Download from [python.org](https://www.python.org/downloads/) and ensure you check **"Add Python to PATH"** during installation.
2.  **Get a Free Groq API Key**:
    *   Sign up at the [Groq Console](https://console.groq.com/keys).
    *   Create a free API key (starts with `gsk_...`).

---

## 2. Setup the Project

Install the required dependencies:
```powershell
pip install requests pillow
```

Ensure your files are structured in the same folder:
*   `pet.py` — The core application.
*   `config.json` — The schedule and API key configuration.
*   `spiderman.png` — The character sprite.

---

## 3. Configure Your Schedule

Open `config.json` and customize your settings:

```json
{
  "groq_api_key": "YOUR_GROQ_API_KEY",
  "groq_model": "llama-3.1-8b-instant",
  "pet_emoji": "🕷️",
  "pet_name": "Spider-Man",
  "pet_image": "spiderman.png",
  "check_interval_seconds": 30,
  "daily_reminders": [
    {
      "id": "ojt_time_in",
      "label": "OJT Time In",
      "time": "08:00",
      "days": ["mon", "tue", "wed", "thu", "fri"],
      "message_hint": "remind me to time in, keep it short and in-character"
    }
  ]
}
```

---

## 4. How to Use

Run the pet app from your terminal:
```powershell
python pet.py
```

*   **Double-click Spidey** ➔ Get a manual greeting or check-in message.
*   **Drag Spidey** ➔ Reposition him anywhere along the top of your screen (he will slide up from the new position when closing).
*   **Right-click Spidey** ➔ Safely exit (Spidey will slide up off-screen before closing).
