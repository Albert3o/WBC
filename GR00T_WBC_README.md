# GR00T Whole Body Control (WBC) — Real Robot Deployment Guide

## Prerequisites

- G1 robot powered on and fully booted (~2 minutes after power on)
- Ethernet cable plugged from PC's built-in ethernet port (`eno1`) into the G1's ethernet port
- USB ethernet adapter (`enx6c1ff7b914d4`) **unplugged** from PC (avoids routing conflicts)

---

## G1 Network Architecture

| IP | Computer | Role |
|---|---|---|
| `192.168.123.161` | RockChip (PC1) | Low-level motor control — runs SONIC firmware. Not accessible to developers. |
| `192.168.123.164` | Jetson Orin (PC2) | High-level development computer — runs G1 Pilot firmware. SSH accessible. |

Your PC must be on the same subnet: `192.168.123.99` (assigned to `eno1`).

---

## One-Time Setup (already done — do not repeat)

These steps have already been completed and do not need to be run again:

```bash
# 1. Assign static IP to eno1
sudo ip addr add 192.168.123.99/24 dev eno1

# 2. Patch the WBC bug (NoneType crash in state_processor.py)
sed -i 's/while result\["name"\]:/while result is not None and result["name"]:/' \
  ~/Isaac-GR00T/external_dependencies/GR00T-WholeBodyControl/gr00t_wbc/control/envs/g1/utils/state_processor.py
```

---

## Every Time — Startup Sequence

### Step 1 — Fix routing (only needed if USB adapter is still plugged in)

If `enx6c1ff7b914d4` is plugged in, traffic to the robot gets routed through it
instead of `eno1`. Remove the bad route:

```bash
sudo ip route del 192.168.123.0/24 dev enx6c1ff7b914d4
```

> **Tip:** If you unplug the USB adapter permanently, you never need this step again.

Verify routing is now correct (should show `dev eno1`):

```bash
ip route get 192.168.123.164
```

Expected output:
```
192.168.123.164 dev eno1 src 192.168.123.99 uid 1000
```

---

### Step 2 — Verify robot is reachable

```bash
ping -I eno1 -c 3 192.168.123.164
```

Expected output: 0% packet loss. If ping fails, check the ethernet cable and
make sure the robot is fully booted.

---

### Step 3 — Activate the Python environment

```bash
cd ~/Isaac-GR00T/external_dependencies/GR00T-WholeBodyControl
source ~/.venv/bin/activate
```

Or use the Isaac-GR00T venv:

```bash
source ~/Isaac-GR00T/.venv/bin/activate
```

---

### Step 4 — Run the WBC script

```bash
python gr00t_wbc/control/main/teleop/run_g1_control_loop.py --interface eno1 --no-with_hands
```

---

## Keyboard Controls (once the script is running)

The tmux session will open with multiple panes. Navigate panes with `Ctrl+B` then arrow keys.

| Key | Action |
|---|---|
| `]` | Start the control system |
| `ENTER` | Switch to Planner Mode (real-time locomotion) |
| `W` / `S` | Move forward / backward |
| `A` / `D` | Steer left / right |
| `Q` / `E` | Turn in place |
| `1` | Slow walk |
| `2` | Walk |
| `3` | Run |
| `N` / `P` | Next / Previous motion set |
| `O` | **Emergency stop — exit immediately** |
| `R` | Instant momentum reset (halt movement) |

> ⚠️ **Safety:** Always keep a finger near `O` (emergency stop) when the robot is moving.

---

## Troubleshooting

**`real: does not match an available interface`**
You passed `--interface real` — use the actual interface name `--interface eno1` instead.

**`TypeError: 'NoneType' object is not subscriptable` on line 29**
The one-time patch was not applied. Run:
```bash
sed -i 's/while result\["name"\]:/while result is not None and result["name"]:/' \
  ~/Isaac-GR00T/external_dependencies/GR00T-WholeBodyControl/gr00t_wbc/control/envs/g1/utils/state_processor.py
```

**`Destination Host Unreachable` when pinging**
Check: (1) ethernet cable is plugged into robot's ethernet port, (2) robot is fully booted,
(3) routing is via `eno1` not `enx6c1ff7b914d4`.

**`Link detected: no` on ethernet adapter**
Cable is not physically connected or robot is off. Check both ends of the cable.

**SSH `permission denied` to `192.168.123.164`**
Default credentials: `username: unitree`, `password: 123`. Password may have been changed — ask your team.

**`] key does nothing in tmux`**
Make sure you are focused on the correct pane (the control loop pane, left side).
Use `Ctrl+B` then `←` to navigate there, then press `]`.
