"""
Desktop Pet Reminder - Chirpy
------------------------------
A cute always-on-top desktop pet that pops up reminders for your
schedule (OJT time-in/out, schoolwork deadlines, etc) using Groq's
free LLM API to generate the message text.

Run with:  python pet.py
Requires:  pip install requests pystray pillow  (pystray/pillow optional, see below)

Edit config.json to set your own schedule and Groq API key.
Get a free Groq API key at: https://console.groq.com/keys
"""

import json
import os
import sys
import time
import random
import threading
import tkinter as tk
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("Missing dependency. Run: pip install requests")
    sys.exit(1)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")

DAY_MAP = {
    0: "mon", 1: "tue", 2: "wed", 3: "thu",
    4: "fri", 5: "sat", 6: "sun"
}

FALLBACK_MESSAGES = [
    "Hey! Don't forget this one, okay? 🐣",
    "Psst, it's time! You've got this.",
    "Reminder time! Go get it done, then rest.",
    "Beep boop, your schedule says it's time!",
]


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"fired_today": {}, "fired_deadlines": {}, "last_date": ""}


def save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def generate_message(config, hint, label):
    """Call Groq API for a cute custom message. Falls back to canned text on failure."""
    api_key = config.get("groq_api_key", "")
    if not api_key or api_key == "PASTE_YOUR_GROQ_API_KEY_HERE":
        return random.choice(FALLBACK_MESSAGES)

    pet_name = config.get("pet_name", "your pet")
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": config.get("groq_model", "llama-3.1-8b-instant"),
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            f"You are {pet_name}, a tiny cute desktop pet that gives short, "
                            "warm, playful reminder messages to your owner. Max 2 sentences. "
                            "Use at most 1 emoji. No hashtags. Speak casually, like a supportive friend."
                        ),
                    },
                    {"role": "user", "content": f"Reminder topic: {label}. {hint}"},
                ],
                "max_tokens": 60,
                "temperature": 0.9,
            },
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[Groq API failed, using fallback] {e}")
        return random.choice(FALLBACK_MESSAGES)


class PetApp:
    def __init__(self, config):
        self.config = config
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # no window border
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "black")
        self.root.configure(bg="black")

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.pet_size = 90
        self.x = screen_w - self.pet_size - 40
        self.y = screen_h - self.pet_size - 100
        self.root.geometry(f"{self.pet_size}x{self.pet_size}+{self.x}+{self.y}")

        self.label = tk.Label(
            self.root,
            text=config.get("pet_emoji", "🐣"),
            font=("Segoe UI Emoji", 46),
            bg="#fff9eb",
            fg="white",
            highlightbackground="#ffd166",
            highlightthickness=2,
            bd=0,
        )
        self.label.pack(expand=True, fill="both", padx=5, pady=5)

        # Drag to move
        self.label.bind("<ButtonPress-1>", self.start_drag)
        self.label.bind("<B1-Motion>", self.do_drag)
        # Right-click to quit
        self.label.bind("<Button-3>", lambda e: self.root.destroy())
        # Double click for a manual check-in message
        self.label.bind("<Double-Button-1>", lambda e: self.manual_greet())

        self.bubble = None
        self._drag_offset = (0, 0)

        # Background scheduler thread
        self.state = load_state()
        t = threading.Thread(target=self.scheduler_loop, daemon=True)
        t.start()

        # Idle bounce animation
        self.bounce_dir = 1
        self.animate()

    def start_drag(self, event):
        self._drag_offset = (event.x + self.label.winfo_x(), event.y + self.label.winfo_y())

    def do_drag(self, event):
        x = self.root.winfo_pointerx() - self._drag_offset[0]
        y = self.root.winfo_pointery() - self._drag_offset[1]
        self.root.geometry(f"+{x}+{y}")

    def animate(self):
        # tiny idle bounce
        cur_y = self.root.winfo_y()
        self.root.geometry(f"+{self.root.winfo_x()}+{cur_y}")
        self.root.after(2000, self.animate)

    def show_bubble(self, text):
        if self.bubble is not None:
            try:
                self.bubble.destroy()
            except Exception:
                pass

        px, py = self.root.winfo_x(), self.root.winfo_y()
        bubble = tk.Toplevel(self.root)
        bubble.overrideredirect(True)
        bubble.wm_attributes("-topmost", True)
        bubble_w = 260
        bx = px - bubble_w - 10 if px - bubble_w - 10 > 0 else px + self.pet_size + 10
        by = py - 10
        bubble.geometry(f"{bubble_w}x100+{bx}+{by}")
        bubble.configure(bg="#fff7e6")

        frame = tk.Frame(bubble, bg="#fff7e6", highlightbackground="#e0a800", highlightthickness=2)
        frame.pack(fill="both", expand=True)

        lbl = tk.Label(
            frame,
            text=text,
            wraplength=230,
            justify="left",
            bg="#fff7e6",
            fg="#333333",
            font=("Segoe UI", 10),
            padx=10,
            pady=10,
        )
        lbl.pack(fill="both", expand=True)

        self.bubble = bubble
        # auto dismiss after 12 seconds
        bubble.after(12000, lambda: bubble.destroy() if bubble.winfo_exists() else None)

    def manual_greet(self):
        msg = generate_message(self.config, "give me a random cute check-in message", "Manual check-in")
        self.root.after(0, lambda: self.show_bubble(msg))

    def fire_reminder(self, label, hint):
        msg = generate_message(self.config, hint, label)
        self.root.after(0, lambda: self.show_bubble(f"{label}\n\n{msg}"))

    def scheduler_loop(self):
        interval = self.config.get("check_interval_seconds", 30)
        while True:
            try:
                self.check_schedule()
            except Exception as e:
                print(f"[scheduler error] {e}")
            time.sleep(interval)

    def check_schedule(self):
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_hm = now.strftime("%H:%M")
        weekday = DAY_MAP[now.weekday()]

        if self.state.get("last_date") != today_str:
            self.state["fired_today"] = {}
            self.state["last_date"] = today_str
            save_state(self.state)

        # Daily reminders
        for r in self.config.get("daily_reminders", []):
            if weekday not in r.get("days", []):
                continue
            key = f"{r['id']}_{today_str}"
            if self.state["fired_today"].get(key):
                continue
            if current_hm == r["time"]:
                self.fire_reminder(r["label"], r.get("message_hint", ""))
                self.state["fired_today"][key] = True
                save_state(self.state)

        # One-time deadlines with lead-time reminders
        for d in self.config.get("one_time_deadlines", []):
            try:
                due = datetime.strptime(d["datetime"], "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            for lead in d.get("remind_before_minutes", [0]):
                fire_time = due - timedelta(minutes=lead)
                key = f"{d['id']}_{lead}"
                if self.state["fired_deadlines"].get(key):
                    continue
                if now >= fire_time and now < due:
                    label = f"{d['label']} (due {due.strftime('%b %d, %I:%M %p')})"
                    self.fire_reminder(label, d.get("message_hint", ""))
                    self.state["fired_deadlines"][key] = True
                    save_state(self.state)

    def run(self):
        self.root.mainloop()


def main():
    if not os.path.exists(CONFIG_PATH):
        print(f"config.json not found at {CONFIG_PATH}")
        sys.exit(1)
    config = load_config()
    app = PetApp(config)
    print("Chirpy is running! Double-click to greet, right-click to quit.")
    app.run()


if __name__ == "__main__":
    main()
