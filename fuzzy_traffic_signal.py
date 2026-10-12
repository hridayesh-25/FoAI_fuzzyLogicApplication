"""
Intelligent Traffic Signal Control Using Fuzzy Logic — Sequential Signal Demo

Run:
    python fuzzy_traffic_signal.py

Requirements:
    Python 3.x with Tkinter. No pip packages required.

Features:
- Four simulated approaches: North, East, South, West.
- Fuzzy logic calculates a suggested green duration from vehicle count and waiting time.
- Only ONE approach is green at a time; the other three remain red.
- The active signal automatically switches when its countdown reaches zero.
- Every road gets a turn. The next road is selected using a fair, priority-aware
  scheduler: longest-waiting approaches are favored, then larger queues.
- New Traffic generates a fresh scenario. Recalculate restarts the schedule.


All nine fuzzy rules
Your program combines the three density categories with the three waiting-time categories, giving \(3 \times 3 = 9\) rules.
Traffic density -Waiting time	Suggested green time
Low	             Short	        12 seconds
Low	            Medium	        18 seconds
Low	            Long	        28 seconds
Medium	        Short	        22 seconds
Medium	        Medium	        32 seconds
Medium	        Long	        42 seconds
High	        Short	        35 seconds
High	        Medium	        45 seconds
High	        Long	        58 seconds
"""

import tkinter as tk
from tkinter import ttk
import random

GREEN_MIN, GREEN_MAX = 10, 60
TICK_MS = 1000

# ---------------- Fuzzy logic: membership functions ----------------

def triangular(x, a, b, c):
    if x <= a or x >= c:
        return 0.0
    if x == b:
        return 1.0
    if x < b:
        return (x - a) / (b - a) if b != a else 1.0
    return (c - x) / (c - b) if c != b else 1.0

def shoulder_low(x, a, b):
    if x <= a:
        return 1.0
    if x >= b:
        return 0.0
    return (b - x) / (b - a)

def shoulder_high(x, a, b):
    if x <= a:
        return 0.0
    if x >= b:
        return 1.0
    return (x - a) / (b - a)

def fuzzify_density(count):
    # Overlapping sets: low, medium, high
    return {
        "low": shoulder_low(count, 3, 9),
        "medium": triangular(count, 4, 10, 16),
        "high": shoulder_high(count, 12, 19),
    }

def fuzzify_wait(wait):
    return {
        "short": shoulder_low(wait, 15, 45),
        "medium": triangular(wait, 20, 60, 100),
        "long": shoulder_high(wait, 75, 110),
    }

def fuzzy_green_time(vehicle_count, wait_seconds):
    """Evaluate fuzzy rules and return a bounded green duration in seconds."""
    d = fuzzify_density(vehicle_count)
    w = fuzzify_wait(wait_seconds)

    rules = [
        ("low", "short", 12),
        ("low", "medium", 18),
        ("low", "long", 28),
        ("medium", "short", 22),
        ("medium", "medium", 32),
        ("medium", "long", 42),
        ("high", "short", 35),
        ("high", "medium", 45),
        ("high", "long", 58),
    ]

    numerator = denominator = 0.0
    fired = []
    for density_label, wait_label, seconds in rules:
        strength = min(d[density_label], w[wait_label])  # fuzzy AND
        if strength > 0:
            numerator += strength * seconds
            denominator += strength
            fired.append((density_label, wait_label, seconds, strength))

    # Fallback protects edge cases where no rule has nonzero strength.
    result = numerator / denominator if denominator else 20.0
    return max(GREEN_MIN, min(GREEN_MAX, result)), fired, d, w

# ---------------- GUI and sequential signal scheduling ----------------

class TrafficDemo:
    def __init__(self, root):
        self.root = root
        root.title("Fuzzy Logic Traffic Signal Controller — Sequential Mode")
        root.geometry("1120x800")
        root.minsize(900, 700)

        self.roads = ["North", "East", "South", "West"]
        self.counts = {}
        self.waits = {}
        self.results = {}
        self.green_seconds = {}
        self.current_road = None
        self.remaining = 0
        self.timer_running = False
        self.elapsed = 0
        self.last_served = []
        self.selected = tk.StringVar(value="North")

        header = ttk.Frame(root, padding=12)
        header.pack(fill="x")
        ttk.Label(header, text="Intelligent Traffic Signal Control Using Fuzzy Logic",
                  font=("Arial", 16, "bold")).pack(anchor="w")
        ttk.Label(header, text="One green signal at a time • adaptive duration • fair rotation",
                  font=("Arial", 10)).pack(anchor="w", pady=(4, 0))

        controls = ttk.Frame(root, padding=(12, 4))
        controls.pack(fill="x")
        ttk.Button(controls, text="New Traffic", command=self.new_traffic).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Calculate & Start", command=self.calculate_and_start).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Pause", command=self.pause).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Resume", command=self.resume).pack(side="left", padx=(0, 12))
        ttk.Label(controls, text="Inspect approach:").pack(side="left")
        combo = ttk.Combobox(controls, textvariable=self.selected, values=self.roads,
                             state="readonly", width=10)
        combo.pack(side="left", padx=6)
        combo.bind("<<ComboboxSelected>>", lambda _e: self.update_details())

        self.canvas = tk.Canvas(root, bg="#e8ecef", highlightthickness=0, height=440)
        self.canvas.pack(fill="both", expand=True, padx=12, pady=8)

        bottom = ttk.Frame(root, padding=12)
        bottom.pack(fill="x")
        self.status = ttk.Label(bottom, text="Click Calculate & Start to calculate timings and start the signal cycle.",
                                font=("Arial", 10), wraplength=1050)
        self.status.pack(anchor="w")
        self.priority_label = ttk.Label(bottom, text="", font=("Arial", 10), wraplength=1050)
        self.priority_label.pack(anchor="w", pady=(4, 0))
        self.details = ttk.Label(bottom, text="", font=("Consolas", 9), justify="left", wraplength=1050)
        self.details.pack(anchor="w", pady=(8, 0))

        self.new_traffic()

    def new_traffic(self):
        self.timer_running = False
        self.current_road = None
        self.remaining = 0
        self.elapsed = 0
        self.last_served = []
        self.results = {}
        self.green_seconds = {}
        for road in self.roads:
            self.counts[road] = random.randint(0, 20)
            self.waits[road] = random.randint(0, 120)
        self.status.config(text="New traffic generated. Click Calculate & Start to run the fuzzy controller.")
        self.priority_label.config(text="")
        self.draw()
        self.update_details()

    def calculate_and_start(self):
        self.timer_running = False
        self.results = {}
        self.green_seconds = {}
        for road in self.roads:
            secs, fired, d, w = fuzzy_green_time(self.counts[road], self.waits[road])
            self.results[road] = (secs, fired, d, w)
            self.green_seconds[road] = max(1, round(secs))
        self.last_served = []
        self.elapsed = 0
        self.current_road = self.choose_next_road()
        self.remaining = self.green_seconds[self.current_road]
        self.timer_running = True
        self.update_priority()
        self.draw()
        self.update_details()
        self.tick()

    def choose_next_road(self):
        # Fairness rule: roads not served in this cycle get priority first.
        # Among them, choose greatest waiting time; then vehicle count.
        candidates = [r for r in self.roads if r not in self.last_served]
        if not candidates:
            self.last_served = []
            candidates = self.roads[:]
        return max(candidates, key=lambda r: (self.waits[r], self.counts[r]))

    def update_priority(self):
        ranked = sorted(self.roads, key=lambda r: (self.waits[r], self.counts[r]), reverse=True)
        order = " → ".join(f"{r} ({self.green_seconds[r]}s)" for r in ranked)
        self.priority_label.config(text="Initial wait/queue priority (durations shown): " + order)

    def tick(self):
        if not self.timer_running:
            return
        self.draw()
        self.update_details()
        if self.remaining <= 0:
            self.last_served.append(self.current_road)
            self.current_road = self.choose_next_road()
            self.remaining = self.green_seconds[self.current_road]
            self.status.config(text=f"Signal switched: {self.current_road} is GREEN for {self.remaining} seconds. All other approaches are RED.")
            self.draw()
            self.update_details()
        else:
            self.status.config(text=f"ACTIVE SIGNAL: {self.current_road} is GREEN • {self.remaining} seconds remaining. All other approaches are RED.")
        self.remaining -= 1
        self.root.after(TICK_MS, self.tick)

    def pause(self):
        self.timer_running = False
        self.status.config(text="Signal cycle paused. Click Resume to continue.")
        self.draw()

    def resume(self):
        if not self.results:
            self.calculate_and_start()
            return
        if not self.timer_running:
            self.timer_running = True
            self.status.config(text="Signal cycle resumed.")
            self.tick()

    def update_details(self):
        road = self.selected.get()
        if road not in self.counts:
            return
        d = fuzzify_density(self.counts[road])
        w = fuzzify_wait(self.waits[road])
        if road in self.results:
            secs, fired, _, _ = self.results[road]
            active = ", ".join(f"{a}/{b}→{g}s [{strength:.2f}]" for a,b,g,strength in fired)
            result = f"Suggested green: {secs:.1f}s; rounded timer: {self.green_seconds[road]}s\nRules: {active or 'fallback duration used'}"
        else:
            result = "Suggested green: not calculated yet"
        signal = "GREEN" if road == self.current_road and self.timer_running else "RED"
        remaining = f"; remaining={self.remaining}s" if signal == "GREEN" else ""
        self.details.config(text=(
            f"{road}: vehicles={self.counts[road]}, waiting={self.waits[road]}s, signal={signal}{remaining}\n"
            f"Density membership: low={d['low']:.2f}, medium={d['medium']:.2f}, high={d['high']:.2f}\n"
            f"Waiting membership: short={w['short']:.2f}, medium={w['medium']:.2f}, long={w['long']:.2f}\n"
            f"{result}"
        ))

    def draw(self):
        c = self.canvas
        c.delete("all")
        c.update_idletasks()
        width, height = max(c.winfo_width(), 700), max(c.winfo_height(), 440)
        cx, cy, road_w = width / 2, height / 2, 150
        c.create_rectangle(cx-road_w/2, 0, cx+road_w/2, height, fill="#454b54", outline="")
        c.create_rectangle(0, cy-road_w/2, width, cy+road_w/2, fill="#454b54", outline="")
        for yy in range(0, int(height), 30):
            c.create_line(cx, yy, cx, yy+14, fill="white", width=2)
        for xx in range(0, int(width), 30):
            c.create_line(xx, cy, xx+14, cy, fill="white", width=2)

        positions = {
            "North": (cx, cy-road_w/2-70),
            "South": (cx, cy+road_w/2+65),
            "West": (cx-road_w/2-100, cy),
            "East": (cx+road_w/2+100, cy),
        }
        for road in self.roads:
            px, py = positions[road]
            count, wait = self.counts[road], self.waits[road]
            c.create_text(px, py-35, text=f"{road}: {count} vehicles", font=("Arial", 10, "bold"), fill="#17202a")
            c.create_text(px, py-17, text=f"Wait: {wait}s", font=("Arial", 9), fill="#17202a")

            # Draw up to 10 car icons, for visual clarity.
            for i in range(min(count, 10)):
                if road in ("North", "South"):
                    vx = cx - 44 + (i % 2) * 26
                    vy = (cy-road_w/2-27-(i//2)*17) if road == "North" else (cy+road_w/2+7+(i//2)*17)
                else:
                    vx = (cx-road_w/2-27-(i//2)*26) if road == "West" else (cx+road_w/2+7+(i//2)*26)
                    vy = cy - 40 + (i % 2) * 26
                c.create_rectangle(vx-8, vy-5, vx+8, vy+5, fill="#4c9be8", outline="#173f5f")

            is_green = road == self.current_road and self.timer_running
            color = "#20a464" if is_green else "#c94b4b"
            label = f"GREEN\n{max(0,self.remaining)}s" if is_green else "RED"
            c.create_oval(px-23, py+5, px+23, py+51, fill=color, outline="white", width=2)
            c.create_text(px, py+28, text=label, fill="white", font=("Arial", 8, "bold"), justify="center")

        c.create_text(cx, cy, text="INTERSECTION", fill="white", font=("Arial", 10, "bold"))

if __name__ == "__main__":
    root = tk.Tk()
    app = TrafficDemo(root)
    root.mainloop()
