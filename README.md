# Mini-Project: Wumpus World implementation using Q‑learning

**USTHB — M1 SII — S2 | Agents Technology | 2025-2026**

---

## Overview

This project implements the classic **Wumpus World** (4×4 grid) with a **Q‑learning** agent.  
The agent learns to survive, collect gold, and return to the start cell by interacting with the environment.

- **Rewards**:  
  Safe move = +10 / Pit = –10 / Wumpus = –10000 / Gold = +1000 / Invalid = 0

- **Perceptions**: breeze (pit nearby), stench (Wumpus nearby), glitter (gold on cell)

- **Q‑learning hyperparameters**: α = 0.5, γ = 0.5, ε = 0.3 (exploration rate)

## How to run

```bash
pip install pygame
python wumpus_qlearning.py
