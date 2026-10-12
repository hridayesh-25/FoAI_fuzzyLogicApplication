# INTELLIGENT TRAFFIC SIGNAL CONTROL USING FUZZY LOGIC

### Demo Overview

This Python-based graphical simulation demonstrates an adaptive traffic signal controller for a four-way intersection (North, South, East, and West). It uses simulated vehicle counts and waiting times to calculate a suitable green-light duration for each approach. A scheduler then selects one approach at a time; its signal becomes green while the other three remain red. When the countdown finishes, the controller moves to the next eligible approach, continuing the cycle so every direction gets a turn.

### Core Logic

The fuzzy controller converts numeric inputs into degrees of membership between 0 and 1. Traffic density is categorized as Low, Medium, or High, and waiting time as Short, Medium, or Long. A set of nine IF–THEN rules maps each combination to a candidate green duration.

For an AND condition, the rule strength is the minimum of the two membership values. If multiple rules are active, their suggested durations are combined using a weighted average. The resulting green time is bounded to the configured range and rounded for the countdown timer.

Separately, the scheduler prioritizes approaches using waiting time, with vehicle count used to break ties. Fuzzy logic determines how long a road should be green; the scheduler determines which road goes next.

### How to Run the Demo

1. Install Python 3 on the computer if it is not already installed. Tkinter is included with most standard Windows Python installations.
2. Save the provided Python demo file (for example, `fuzzy_traffic_signal.py`) in a folder.
3. Open Command Prompt or the terminal in that folder.
4. Run `python fuzzy_traffic_signal.py` (or `py fuzzy_traffic_signal.py` on Windows).
5. Click New Traffic to generate a new traffic scenario, then click Run Fuzzy Controller or the equivalent start button to calculate durations and begin the signal cycle.
6. Use Pause/Resume if available, and choose North, South, East, or West in the inspection menu to view its inputs, membership values, active rules, suggested duration, and current signal state.

### What the Demo Shows

The interface displays the four approaches, vehicle queues, signal colors, countdown, and fuzzy-controller details. It makes the decision process inspectable rather than showing only a final signal. Exact counts and durations can vary when new traffic is generated. This is an educational simulation with simulated inputs, not a real-world traffic controller.
