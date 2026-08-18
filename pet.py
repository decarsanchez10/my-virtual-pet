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
    import winsound
except ImportError:
    winsound = None

try:
    import requests
except ImportError:
    print("Missing dependency. Run: pip install requests")
    sys.exit(1)

def play_notification_sound():
    if winsound:
        try:
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
        except Exception as e:
            print(f"[Sound error] {e}")

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
        
        # Transparent key color (fuchsia avoids cutting out black outlines)
        self.trans_color = "#ff00ff"
        self.root.overrideredirect(True)  # no window border
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", self.trans_color)
        self.root.configure(bg=self.trans_color)

        # Look for image path in config or check if default spiderman.png exists
        image_path = config.get("pet_image", "")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if not image_path:
            potential_default = os.path.join(script_dir, "spiderman.png")
            if os.path.exists(potential_default):
                image_path = potential_default
        else:
            if not os.path.isabs(image_path):
                image_path = os.path.join(script_dir, image_path)

        self.pet_image = None
        if image_path and os.path.exists(image_path):
            try:
                self.pet_image = tk.PhotoImage(file=image_path)
            except Exception as e:
                print(f"[Error loading image] {e}")

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        if self.pet_image:
            self.pet_size = self.pet_image.width()
            self.x = screen_w - self.pet_size - 100
            self.y = 0
            self.root.geometry(f"{self.pet_size}x{self.pet_size}+{self.x}+{self.y}")

            self.label = tk.Label(
                self.root,
                image=self.pet_image,
                bg=self.trans_color,
                bd=0,
                highlightthickness=0,
            )
            self.label.pack(expand=True, fill="both")
        else:
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
        self.is_dragging = False

        # Background scheduler thread
        self.state = load_state()
        t = threading.Thread(target=self.scheduler_loop, daemon=True)
        t.start()

        # Idle bobbing/bounce animation
        self.bounce_dir = 1
        self.animate()

    def start_drag(self, event):
        self.is_dragging = True
        self._drag_offset = (event.x, event.y)

    def do_drag(self, event):
        x = self.root.winfo_pointerx() - self._drag_offset[0]
        y = self.root.winfo_pointery() - self._drag_offset[1]
        self.root.geometry(f"+{x}+{y}")
        # When dragging is completed (or during), we want to make sure
        # is_dragging is cleared on release
        self.label.bind("<ButtonRelease-1>", self.stop_drag)

    def stop_drag(self, event):
        self.is_dragging = False

    def animate(self):
        # Gentle bobbing up and down like hanging on a web
        if not self.is_dragging:
            self.bounce_dir = -self.bounce_dir
            cur_x = self.root.winfo_x()
            cur_y = self.root.winfo_y()
            new_y = cur_y + (self.bounce_dir * 4)
            self.root.geometry(f"+{cur_x}+{new_y}")
        self.root.after(1000, self.animate)

    def show_bubble(self, text):
        if self.bubble is not None:
            try:
                self.bubble.destroy()
            except Exception:
                pass

        # Split text into Title and Message if it has double-newlines
        title_text = "🕷️ Spider-Man"
        message_text = text
        if "\n\n" in text:
            parts = text.split("\n\n", 1)
            title_text = f"🕷️ {parts[0]}"
            message_text = parts[1]

        px, py = self.root.winfo_x(), self.root.winfo_y()
        bubble = tk.Toplevel(self.root)
        bubble.overrideredirect(True)
        bubble.wm_attributes("-topmost", True)
        
        bubble_w = 280
        bubble_h = 130
        bx = px - bubble_w - 10 if px - bubble_w - 10 > 0 else px + self.pet_size + 10
        by = max(10, py - 10)
        bubble.geometry(f"{bubble_w}x{bubble_h}+{bx}+{by}")
        bubble.configure(bg="#0f0f12")

        # Force DWM rounded corners on Windows 11
        try:
            from ctypes import windll, byref, sizeof, c_int
            bubble.update()
            hwnd = windll.user32.GetParent(bubble.winfo_id())
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 33, byref(c_int(2)), sizeof(c_int)
            )
        except Exception:
            pass

        # Modern Outer border frame
        frame = tk.Frame(
            bubble,
            bg="#0f0f12",
            highlightbackground="#ef4444",  # Spider-Man Red
            highlightthickness=1,
            bd=0
        )
        frame.pack(fill="both", expand=True)

        # Header Frame (for title)
        header_frame = tk.Frame(frame, bg="#0f0f12")
        header_frame.pack(fill="x", padx=12, pady=(10, 0))

        # Title Label
        title_lbl = tk.Label(
            header_frame,
            text=title_text,
            font=("Segoe UI", 9, "bold"),
            bg="#0f0f12",
            fg="#f87171",  # Light red for modern contrast
            anchor="w"
        )
        title_lbl.pack(side="left", fill="x")

        # Divider line
        divider = tk.Frame(frame, bg="#27272a", height=1)
        divider.pack(fill="x", padx=12, pady=6)

        # Message Label
        lbl = tk.Label(
            frame,
            text=message_text,
            wraplength=250,
            justify="left",
            bg="#0f0f12",
            fg="#e4e4e7",  # Zinc-200 readable text
            font=("Segoe UI", 10),
            anchor="nw"
        )
        lbl.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        self.bubble = bubble
        # auto dismiss after 12 seconds
        bubble.after(12000, lambda: bubble.destroy() if bubble.winfo_exists() else None)

    def manual_greet(self):
        msg = generate_message(self.config, "give me a random cute check-in message", "Manual check-in")
        play_notification_sound()
        self.root.after(0, lambda: self.show_bubble(msg))

    def fire_reminder(self, label, hint):
        msg = generate_message(self.config, hint, label)
        play_notification_sound()
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
