"""
Wumpus World - Q-learning tabulaire.
Agent avec règles heuristiques simples (brise => pas de puits voisin, etc.).
Interface Pygame : vision spectateur, sauvegarde/chargement Q-table.
"""

import pygame
import sys
from enum import Enum, IntEnum
import random
from collections import deque
import os
import json

# Configuration
CELL_SIZE = 100
GRID_SIZE = 4
WINDOW_SIZE = CELL_SIZE * GRID_SIZE
INFO_PANEL_WIDTH = 400
BOTTOM_BAR_HEIGHT = 56
WINDOW_WIDTH = WINDOW_SIZE + INFO_PANEL_WIDTH
WINDOW_HEIGHT = WINDOW_SIZE + BOTTOM_BAR_HEIGHT

# Couleurs UI
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
GREEN = (0, 200, 0)
RED = (255, 0, 0)
YELLOW = (255, 215, 0)
BLUE = (100, 150, 255)
DARK_GREEN = (0, 120, 0)
ORANGE = (255, 165, 0)
BROWN = (101, 67, 33)

UI_BG_DEEP = (18, 22, 32)
UI_BG_PANEL = (28, 34, 48)
UI_BG_CELL_VIS = (72, 82, 98)
UI_BG_CELL_SAFE = (52, 78, 62)
UI_BG_CELL_UNK = (42, 46, 56)
UI_ACCENT = (94, 156, 255)
UI_ACCENT_DIM = (60, 100, 160)
UI_TEXT = (230, 234, 242)
UI_TEXT_MUTED = (160, 170, 188)
UI_GOLD_UI = (255, 200, 120)
UI_GRID_LINE = (20, 24, 32)
UI_START_RING = (72, 201, 120)

# ─────────────────────────────────────────────
# Sprites (création / chargement)
# ─────────────────────────────────────────────

def create_wumpus_sprite(size=70):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    r = size // 2 - 4
    pygame.draw.ellipse(surf, (180, 20, 20), (cx - r, cy - r + 6, r * 2, r * 2 - 4))
    horn = (120, 10, 10)
    pygame.draw.polygon(surf, horn, [(cx-14, cy-r+6),(cx-24, cy-r-12),(cx-5, cy-r+2)])
    pygame.draw.polygon(surf, horn, [(cx+14, cy-r+6),(cx+24, cy-r-12),(cx+5, cy-r+2)])
    for ex in [cx - 12, cx + 12]:
        pygame.draw.circle(surf, YELLOW, (ex, cy - 8), 8)
        pygame.draw.circle(surf, BLACK, (ex, cy - 8), 3)
    mouth_y = cy + 10
    pygame.draw.rect(surf, (60, 0, 0), (cx-16, mouth_y, 32, 12), border_radius=4)
    for i in range(4):
        pygame.draw.rect(surf, WHITE, (cx-14+i*9, mouth_y, 7, 10), border_radius=2)
    pygame.draw.ellipse(surf, (80, 0, 0), (cx-r, cy-r+6, r*2, r*2-4), 2)
    return surf

def create_gold_sprite(size=60):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    body = pygame.Rect(cx-20, cy-12, 40, 26)
    pygame.draw.rect(surf, (218, 165, 32), body, border_radius=6)
    pygame.draw.rect(surf, (255, 220, 50), body.inflate(-6, -6), border_radius=5)
    pygame.draw.rect(surf, (255, 255, 180), (body.x+5, body.y+4, 14, 6), border_radius=3)
    font = pygame.font.SysFont("Arial", 16, bold=True)
    lbl = font.render("Au", True, (120, 80, 0))
    surf.blit(lbl, (cx - lbl.get_width()//2, cy - lbl.get_height()//2 + 2))
    pygame.draw.rect(surf, (160, 120, 0), body, 2, border_radius=6)
    return surf

def create_pit_sprite(size=80):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    r = size // 2 - 4
    pygame.draw.circle(surf, (70, 70, 70), (cx, cy), r)
    pygame.draw.ellipse(surf, (20, 20, 20), (cx-r+8, cy-r+10, (r-8)*2, (r-10)*2))
    for i in range(5):
        pygame.draw.circle(surf, (10, 10, 10), (cx, cy+i*2), max(2, r-8-i*4))
    pygame.draw.circle(surf, (110, 110, 110), (cx, cy), r, 3)
    pygame.draw.circle(surf, (40, 40, 40), (cx, cy), r-8, 2)
    return surf

def create_arrow_sprite(size=50):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    pygame.draw.rect(surf, BROWN, (4, cy-3, size-18, 6), border_radius=2)
    pygame.draw.polygon(surf, (200, 120, 40), [(size-3, cy),(size-16, cy-10),(size-16, cy+10)])
    pygame.draw.polygon(surf, (180, 180, 180), [(4, cy),(14, cy-8),(14, cy+8)])
    return surf

def create_agent_sprite(size=70):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    s = size // 2 - 6
    pts = [(cx+s, cy), (cx-s, cy-s), (cx-s, cy+s)]
    pygame.draw.polygon(surf, (30, 180, 255), pts)
    pygame.draw.polygon(surf, WHITE, pts, 2)
    pygame.draw.circle(surf, WHITE, (cx+s//2, cy), 5)
    pygame.draw.circle(surf, BLACK, (cx+s//2, cy), 2)
    return surf

def load_image(filename, fallback_fn, size):
    """Charge une image si elle existe, sinon crée un sprite."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.smoothscale(img, (size, size))
        except Exception:
            pass
    return fallback_fn(size)

# Types et actions
class CellType(Enum):
    EMPTY = 0
    PIT = 1
    WUMPUS = 2
    GOLD = 3

class Direction(IntEnum):
    RIGHT = 0
    DOWN = 1
    LEFT = 2
    UP = 3

class Action(Enum):
    FORWARD = "MOVE_FORWARD"
    TURN_LEFT = "TURN_LEFT"
    TURN_RIGHT = "TURN_RIGHT"
    GRAB = "GRAB"
    SHOOT = "SHOOT"
    CLIMB = "CLIMB"

def get_adjacent(x, y):
    """Retourne les cases voisines (dans la grille)."""
    adj = []
    for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
        nx, ny = x+dx, y+dy
        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
            adj.append((nx, ny))
    return adj

# ─────────────────────────────────────────────
# Q-learning
# ─────────────────────────────────────────────

QL_ACTIONS = (Action.FORWARD, Action.TURN_LEFT, Action.TURN_RIGHT, Action.GRAB, Action.SHOOT, Action.CLIMB)

def encode_q_state(world):
    """Tuple (x, y, dir, arrow, gold, wumpus_alive, breeze, stench, glitter) pour la Q-table."""
    a = world.agent
    p = world.get_perceptions(a.x, a.y)
    return (
        a.x, a.y,
        int(a.direction),
        int(a.has_arrow),
        int(a.has_gold),
        int(world.wumpus_alive),
        int(p["breeze"]),
        int(p["stench"]),
        int(p["glitter"]),
    )

class QLearningAgent:
    """Agent Q-learning avec règles heuristiques pour le Wumpus."""

    def __init__(self, alpha=0.5, gamma=0.5, epsilon=0.3):
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.training = True
        self.Q = {}
        self.episode_index = 0
        self.reset_episode()

    def reset_episode(self):
        """Réinitialise l'état de l'agent pour une nouvelle partie."""
        self.x = 0
        self.y = 0
        self.direction = Direction.RIGHT
        self.has_arrow = True
        self.has_gold = False
        self.is_alive = True
        self.climbed_out = False
        self.visited = {(0, 0)}
        self.safe_cells = {(0, 0)}
        self.perceptions = {}
        self.valid_wumpus = set()
        self.wumpus_dead = False
        self.action_plan = deque()
        self.score = 0
        self.status = "Q-learning"
        self.no_pit_near = set()
        self.no_wumpus_here = set()

    def current_pos(self):
        return (self.x, self.y)

    def update_kb(self, x, y, percepts):
        """Met à jour la mémoire de l'agent : cases visitées, déductions sur puits et Wumpus."""
        self.visited.add((x, y))
        self.perceptions[(x, y)] = percepts
        self.safe_cells.add((x, y))
        if not percepts["breeze"]:
            for nx, ny in get_adjacent(x, y):
                self.no_pit_near.add((nx, ny))
        if not percepts["stench"]:
            for nx, ny in get_adjacent(x, y):
                self.no_wumpus_here.add((nx, ny))

    def deduce_safe_cells(self):
        """Après la mort du Wumpus, toutes les cases deviennent sans danger puant."""
        self.no_wumpus_here = set()

    def q_value(self, state, action):
        return self.Q.get((state, action), 0.0)

    def _forward_cell(self):
        """Retourne la case devant l'agent, ou None si en dehors."""
        dx = dy = 0
        if self.direction == Direction.RIGHT:
            dx = 1
        elif self.direction == Direction.LEFT:
            dx = -1
        elif self.direction == Direction.DOWN:
            dy = 1
        elif self.direction == Direction.UP:
            dy = -1
        nx, ny = self.x + dx, self.y + dy
        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
            return (nx, ny)
        return None

    def legal_actions(self, world):
        """Liste des actions autorisées : évite d'avancer vers une case potentiellement dangereuse non visitée."""
        cur = world.get_perceptions(self.x, self.y)
        legal = []
        for a in QL_ACTIONS:
            if a == Action.FORWARD:
                t = self._forward_cell()
                if t is None:
                    continue
                nx, ny = t
                if (nx, ny) not in self.visited:
                    if cur["breeze"] and (nx, ny) not in self.no_pit_near:
                        continue
                    if world.wumpus_alive and cur["stench"] and (nx, ny) not in self.no_wumpus_here:
                        continue
                legal.append(a)
            else:
                legal.append(a)
        return legal if legal else list(QL_ACTIONS)

    def best_action(self, state, legal):
        best_a, best_q = legal[0], -1e18
        for a in legal:
            q = self.q_value(state, a)
            if q > best_q:
                best_q, best_a = q, a
        return best_a

    def choose_action(self, world):
        """Choisit une action : réflexes (or, sortie) puis ε-greedy."""
        p = world.get_perceptions(self.x, self.y)
        if p.get("glitter") and not self.has_gold:
            return Action.GRAB
        if (self.x, self.y) == (0, 0) and self.has_gold:
            return Action.CLIMB

        legal = self.legal_actions(world)
        state = encode_q_state(world)
        if self.training and random.random() < self.epsilon:
            return random.choice(legal)
        return self.best_action(state, legal)

    def learn(self, state, action, reward, next_state, done):
        """Met à jour la Q-valeur selon la formule Q-learning."""
        q_sa = self.q_value(state, action) #Récupération de l’ancienne valeur Q
        max_next = 0.0 if done else max(self.q_value(next_state, ap) for ap in QL_ACTIONS)
        self.Q[(state, action)] = q_sa + self.alpha * (reward + self.gamma * max_next - q_sa)

    def q_table_size(self):
        return len({k[0] for k in self.Q})

    def save(self, path):
        rows = [{"s": list(st), "a": ac.name, "v": float(v)} for (st, ac), v in self.Q.items()]
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"Q": rows}, f)

    def load(self, path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.Q = {}
        for item in data.get("Q", []):
            st = tuple(item["s"])
            ac = Action[item["a"]]
            self.Q[(st, ac)] = float(item["v"])

# ─────────────────────────────────────────────
# Monde (environnement)
# ─────────────────────────────────────────────

class World:
    def __init__(self, agent=None):
        self.grid = [[CellType.EMPTY]*GRID_SIZE for _ in range(GRID_SIZE)]
        self.wumpus_alive = True
        self.game_over = False
        self.message = ""
        self.agent = agent if agent else QLearningAgent()
        if agent:
            self.agent.reset_episode()
        self.wumpus_pos = None
        self.gold_pos = None
        self.pits = []
        self._place_elements()
        self.agent.update_kb(0, 0, self.get_perceptions(0, 0))

    def _place_elements(self):
        """Place aléatoirement Wumpus, or et 3 puits (case (0,0) exclue)."""
        positions = [(x,y) for x in range(GRID_SIZE) for y in range(GRID_SIZE) if (x,y) != (0,0)]
        random.shuffle(positions)
        self.wumpus_pos = positions.pop()
        self.grid[self.wumpus_pos[1]][self.wumpus_pos[0]] = CellType.WUMPUS
        self.gold_pos = positions.pop()
        self.grid[self.gold_pos[1]][self.gold_pos[0]] = CellType.GOLD
        self.pits = []
        for _ in range(3):
            pos = positions.pop()
            self.pits.append(pos)
            self.grid[pos[1]][pos[0]] = CellType.PIT

    def get_perceptions(self, x, y):
        """Retourne breeze, stench, glitter pour une case donnée."""
        p = {'breeze': False, 'stench': False, 'glitter': False}
        for nx, ny in get_adjacent(x, y):
            if self.grid[ny][nx] == CellType.PIT:
                p['breeze'] = True
            if self.grid[ny][nx] == CellType.WUMPUS and self.wumpus_alive:
                p['stench'] = True
        if self.grid[y][x] == CellType.GOLD and not self.agent.has_gold:
            p['glitter'] = True
        return p

    def execute_action(self, action):
        """Exécute l'action et retourne la récompense (Safe +10, Pit -10, W -10000, G +1000, NonValid 0)."""
        if self.game_over or action is None:
            return 0.0

        reward = 0.0

        if action == Action.TURN_LEFT:
            self.agent.direction = Direction((self.agent.direction.value - 1) % 4)
            self.message = "Tourne à gauche."
            reward = 10.0

        elif action == Action.TURN_RIGHT:
            self.agent.direction = Direction((self.agent.direction.value + 1) % 4)
            self.message = "Tourne à droite."
            reward = 10.0

        elif action == Action.FORWARD:
            dx = dy = 0
            if self.agent.direction == Direction.RIGHT:
                dx = 1
            elif self.agent.direction == Direction.DOWN:
                dy = 1
            elif self.agent.direction == Direction.LEFT:
                dx = -1
            elif self.agent.direction == Direction.UP:
                dy = -1
            nx, ny = self.agent.x + dx, self.agent.y + dy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                self.agent.x, self.agent.y = nx, ny
                self.message = "Avance."
                cell = self.grid[ny][nx]
                if cell == CellType.PIT:
                    self.agent.is_alive = False
                    self.game_over = True
                    self.message = "GAME OVER — tombé dans un puits !"
                    reward = -10.0
                elif cell == CellType.WUMPUS and self.wumpus_alive:
                    self.agent.is_alive = False
                    self.game_over = True
                    self.message = "GAME OVER — dévoré par le Wumpus !"
                    reward = -10000.0
                else:
                    percepts = self.get_perceptions(nx, ny)
                    self.agent.update_kb(nx, ny, percepts)
                    reward = 10.0
            else:
                self.message = "Mur !"
                reward = 0.0

        elif action == Action.GRAB:
            if (self.agent.x, self.agent.y) == self.gold_pos and not self.agent.has_gold:
                self.agent.has_gold = True
                self.message = "L'or est à moi !"
                reward = 1000.0
            else:
                self.message = "Rien à ramasser."
                reward = 0.0

        elif action == Action.SHOOT:
            if self.agent.has_arrow:
                self.agent.has_arrow = False
                dx = dy = 0
                if self.agent.direction == Direction.RIGHT:
                    dx = 1
                elif self.agent.direction == Direction.DOWN:
                    dy = 1
                elif self.agent.direction == Direction.LEFT:
                    dx = -1
                elif self.agent.direction == Direction.UP:
                    dy = -1
                ax, ay = self.agent.x, self.agent.y
                killed = False
                while 0 <= ax + dx < GRID_SIZE and 0 <= ay + dy < GRID_SIZE:
                    ax += dx
                    ay += dy
                    if (ax, ay) == self.wumpus_pos and self.wumpus_alive:
                        self.wumpus_alive = False
                        self.agent.wumpus_dead = True
                        killed = True
                        break
                if killed:
                    self.message = "AAAARGH ! Wumpus tué !"
                    # Mise à jour des perceptions stockées pour les cases visitées
                    for (vx, vy) in list(self.agent.visited):
                        if (vx, vy) in self.agent.perceptions:
                            self.agent.perceptions[(vx, vy)]['stench'] = False
                    self.agent.deduce_safe_cells()
                    reward = 10.0
                else:
                    self.message = "Raté !"
                    reward = 10.0
            else:
                self.message = "Plus de flèche."
                reward = 0.0

        elif action == Action.CLIMB:
            if self.agent.x == 0 and self.agent.y == 0:
                self.game_over = True
                self.agent.climbed_out = True
                if self.agent.has_gold:
                    self.message = "VICTOIRE ! Sorti avec l'or !"
                else:
                    self.message = "Sorti sans l'or."
                reward = 10.0
            else:
                self.message = "Sortie uniquement en (0,0)."
                reward = 0.0

        self.agent.score += reward
        return reward

def train_q_learning_episodes(n_episodes, agent=None, max_steps=220):
    """Entraîne l'agent sur n_episodes parties sans affichage."""
    agent = agent or QLearningAgent()
    agent.training = True
    returns = []
    for _ in range(n_episodes):
        if pygame.get_init():
            pygame.event.pump()
        world = World(agent=agent)
        ep_ret = 0.0
        for _step in range(max_steps):
            if world.game_over or not world.agent.is_alive:
                break
            s = encode_q_state(world)
            a = agent.choose_action(world)
            r = world.execute_action(a)
            s2 = encode_q_state(world)
            done = world.game_over or (not world.agent.is_alive)
            agent.learn(s, a, r, s2, done)
            ep_ret += r
        returns.append(ep_ret)
        agent.episode_index += 1
    return agent, returns

QTABLE_DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qtable_wumpus.json")

# ─────────────────────────────────────────────
# Interface Pygame
# ─────────────────────────────────────────────

def _load_ui_fonts():
    for name in ("Segoe UI", "Calibri", "Arial", "DejaVu Sans"):
        try:
            title = pygame.font.SysFont(name, 26, bold=True)
            body = pygame.font.SysFont(name, 19)
            small = pygame.font.SysFont(name, 16)
            return title, body, small
        except Exception:
            continue
    return (pygame.font.Font(None, 28), pygame.font.Font(None, 22), pygame.font.Font(None, 18))

class Game:
    """Gère l'affichage et la boucle de jeu."""

    def __init__(self):
        pygame.init()
        try:
            pygame.display.set_icon(create_agent_sprite(32))
        except Exception:
            pass
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Wumpus World — Q-learning")
        self.clock = pygame.time.Clock()
        self.font_title, self.font, self.small_font = _load_ui_fonts()
        self.q_agent = QLearningAgent()
        self.world = World(agent=self.q_agent)
        self.auto_play = True
        self.auto_delay = 300
        self._load_sprites()

    def _load_sprites(self):
        S = CELL_SIZE - 20
        self.img_wumpus = load_image("wumpus.png", create_wumpus_sprite, S)
        self.img_gold = load_image("gold.png", create_gold_sprite, S - 10)
        self.img_pit = load_image("pit.png", create_pit_sprite, S + 10)
        self.img_arrow = load_image("arrow.png", create_arrow_sprite, 36)
        self.img_agent = load_image("agent.png", create_agent_sprite, S)

    def _blit_center(self, img, cx, cy):
        self.screen.blit(img, (cx - img.get_width()//2, cy - img.get_height()//2))

    def _cell_center(self, x, y):
        return x * CELL_SIZE + CELL_SIZE//2, y * CELL_SIZE + CELL_SIZE//2

    def _wrap_text(self, text, font, max_width):
        if not text:
            return [""]
        words = text.split()
        lines, current = [], []
        for w in words:
            trial = " ".join(current + [w])
            if font.render(trial, True, (0,0,0)).get_width() <= max_width:
                current.append(w)
            else:
                if current:
                    lines.append(" ".join(current))
                current = [w]
        if current:
            lines.append(" ".join(current))
        return lines if lines else [text]

    def _perception_badge(self, label, text_color):
        surf = self.small_font.render(label, True, text_color)
        pad_x, pad_y = 5, 3
        w, h = surf.get_width() + pad_x*2, surf.get_height() + pad_y*2
        box = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(box, (12,16,28,210), box.get_rect(), border_radius=6)
        pygame.draw.rect(box, (*text_color[:3],90), box.get_rect(), 1, border_radius=6)
        box.blit(surf, (pad_x, pad_y))
        return box

    def draw_grid(self):
        agent = self.world.agent
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                cx, cy = self._cell_center(x, y)
                cell_type = self.world.grid[y][x]
                visited = (x,y) in agent.visited

                if visited:
                    bg = UI_BG_CELL_VIS
                elif (x,y) in agent.safe_cells:
                    bg = UI_BG_CELL_SAFE
                else:
                    bg = UI_BG_CELL_UNK
                pygame.draw.rect(self.screen, bg, rect)

                if not visited and (x+y)%2 == 1:
                    shade = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                    shade.fill((0,0,0,18))
                    self.screen.blit(shade, rect.topleft)

                if cell_type == CellType.PIT:
                    self._blit_center(self.img_pit, cx, cy)
                if cell_type == CellType.WUMPUS:
                    self._blit_center(self.img_wumpus, cx, cy)
                    if not self.world.wumpus_alive:
                        sz = 24
                        pygame.draw.line(self.screen, RED, (cx-sz, cy-sz), (cx+sz, cy+sz), 5)
                        pygame.draw.line(self.screen, RED, (cx+sz, cy-sz), (cx-sz, cy+sz), 5)
                if cell_type == CellType.GOLD and not agent.has_gold:
                    self._blit_center(self.img_gold, cx, cy)

                if visited:
                    perceptions = self.world.get_perceptions(x, y)
                    bx, by = x * CELL_SIZE + 6, y * CELL_SIZE + 6
                    if perceptions["breeze"]:
                        b = self._perception_badge("Brise", (150,205,255))
                        self.screen.blit(b, (bx, by))
                        by += b.get_height() + 3
                    if perceptions["stench"]:
                        b = self._perception_badge("Puant", (140,230,160))
                        self.screen.blit(b, (bx, by))

                if not visited and (x,y) in agent.valid_wumpus:
                    wtag = self._perception_badge("?W", ORANGE)
                    self.screen.blit(wtag, (x*CELL_SIZE + CELL_SIZE - wtag.get_width() - 6, y*CELL_SIZE + 6))

                coord = self.small_font.render(f"{x},{y}", True, UI_TEXT_MUTED)
                self.screen.blit(coord, (x*CELL_SIZE + CELL_SIZE - coord.get_width() - 4, y*CELL_SIZE + CELL_SIZE - coord.get_height() - 2))

                if (x,y) == (0,0):
                    pygame.draw.rect(self.screen, UI_START_RING, rect, 4, border_radius=2)
                else:
                    pygame.draw.rect(self.screen, UI_GRID_LINE, rect, 1)

                if (x,y) == (agent.x, agent.y) and agent.is_alive:
                    glow = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                    pygame.draw.rect(glow, (*UI_ACCENT[:3], 35), glow.get_rect(), border_radius=4)
                    self.screen.blit(glow, rect.topleft)
                    self._blit_center(self.img_agent, cx, cy)
                    if agent.has_arrow:
                        ax = x*CELL_SIZE + CELL_SIZE - 38
                        ay = y*CELL_SIZE + CELL_SIZE - 26
                        self.screen.blit(self.img_arrow, (ax, ay))

    def draw_info_panel(self):
        agent = self.world.agent
        panel = pygame.Rect(WINDOW_SIZE, 0, INFO_PANEL_WIDTH, WINDOW_SIZE)
        pygame.draw.rect(self.screen, UI_BG_PANEL, panel)
        pygame.draw.rect(self.screen, UI_ACCENT_DIM, (WINDOW_SIZE, 0, 3, WINDOW_SIZE))
        pygame.draw.line(self.screen, UI_GRID_LINE, (WINDOW_SIZE, 48), (WINDOW_WIDTH, 48))

        px = WINDOW_SIZE + 18
        yo = 12
        text_w = INFO_PANEL_WIDTH - 36

        def subhead(label):
            nonlocal yo
            t = self.font.render(label, True, UI_GOLD_UI)
            self.screen.blit(t, (px, yo))
            yo += t.get_height() + 4
            pygame.draw.line(self.screen, UI_ACCENT_DIM, (px, yo), (WINDOW_WIDTH - 18, yo), 1)
            yo += 8

        def line(s, color=UI_TEXT, font=None):
            nonlocal yo
            f = font or self.font
            self.screen.blit(f.render(s, True, color), (px, yo))
            yo += f.get_height() + 5

        def muted(s):
            line(s, UI_TEXT_MUTED, self.small_font)

        head = self.font_title.render("Mission", True, UI_TEXT)
        self.screen.blit(head, (px, yo))
        yo += head.get_height() + 10

        line("Agent : Q-learning + règles Wumpus", UI_ACCENT)
        muted(f"États appris : {agent.q_table_size()}   ε = {agent.epsilon:.2f}   exploration : {'oui' if agent.training else 'non'}")
        muted("Brise ⇒ puits voisins ; Puant ⇒ Wumpus voisin.")
        muted("Avance interdite vers inconnu si danger potentiel.")
        yo += 4

        subhead("État & inventaire")
        line(f"Position ({agent.x},{agent.y})   ·   {agent.direction.name}")
        line(f"Score {agent.score}")
        line(f"Flèche {'oui' if agent.has_arrow else 'non'}      Or {'ramassé' if agent.has_gold else 'non'}")
        muted(f"Cases visitées : {len(agent.visited)} / {GRID_SIZE*GRID_SIZE}")
        yo += 4

        subhead("Statut")
        for wline in self._wrap_text(agent.status, self.small_font, text_w)[:3]:
            line(wline, UI_TEXT_MUTED, self.small_font)
        yo += 2

        subhead("Dernier événement")
        for wline in self._wrap_text(self.world.message, self.small_font, text_w)[:3]:
            line(wline, UI_TEXT_MUTED, self.small_font)
        yo += 2

        subhead("Contrôles")
        muted("Espace   pas manuel    P   auto/manuel")
        muted("+ / -    vitesse auto   R   nouvelle partie")
        muted("J        exploration on/off")
        muted("T        entraîner Q (150 épisodes)")
        muted("F6 / F7  sauver / charger qtable")

    def draw_bottom_bar(self):
        bar = pygame.Rect(0, WINDOW_SIZE, WINDOW_WIDTH, BOTTOM_BAR_HEIGHT)
        pygame.draw.rect(self.screen, (22,26,36), bar)
        pygame.draw.line(self.screen, UI_ACCENT_DIM, (0, WINDOW_SIZE), (WINDOW_WIDTH, WINDOW_SIZE), 2)

        mode = "AUTO" if self.auto_play else "MANUEL"
        left = self.font.render(f"Vitesse {self.auto_delay} ms/pas  ·  {mode}", True, UI_GOLD_UI)
        self.screen.blit(left, (16, WINDOW_SIZE + (BOTTOM_BAR_HEIGHT - left.get_height())//2))

        legends = [(self.img_wumpus, "Wumpus"), (self.img_gold, "Or"), (self.img_pit, "Puits"), (self.img_arrow, "Flèche")]
        total_w = sum(92 for _ in legends)
        ox = max(WINDOW_SIZE//2, WINDOW_WIDTH - total_w - 24)
        cy = WINDOW_SIZE + BOTTOM_BAR_HEIGHT//2
        for img, label in legends:
            thumb = pygame.transform.smoothscale(img, (28,28))
            self.screen.blit(thumb, (ox, cy - thumb.get_height()//2))
            t = self.small_font.render(label, True, UI_TEXT_MUTED)
            self.screen.blit(t, (ox + 32, cy - t.get_height()//2))
            ox += 92

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not self.auto_play:
                    if not self.world.game_over:
                        self._step_agent()
                elif event.key == pygame.K_p:
                    self.auto_play = not self.auto_play
                elif event.key == pygame.K_r:
                    self.world = World(agent=self.q_agent)
                    self.auto_play = True
                elif event.key == pygame.K_t:
                    self.q_agent.training = True
                    train_q_learning_episodes(150, self.q_agent, max_steps=200)
                    self.world = World(agent=self.q_agent)
                    self.auto_play = True
                elif event.key == pygame.K_F6:
                    try:
                        self.q_agent.save(QTABLE_DEFAULT_PATH)
                        self.world.message = f"Q-table sauvegardée ({self.q_agent.q_table_size()} états)."
                    except OSError as e:
                        self.world.message = f"Sauvegarde échouée : {e}"
                elif event.key == pygame.K_j:
                    self.q_agent.training = not self.q_agent.training
                elif event.key == pygame.K_F7:
                    try:
                        self.q_agent.load(QTABLE_DEFAULT_PATH)
                        self.world = World(agent=self.q_agent)
                        self.world.message = "Q-table chargée."
                    except FileNotFoundError:
                        self.world.message = "Fichier qtable_wumpus.json introuvable."
                    except (OSError, json.JSONDecodeError, KeyError, TypeError) as e:
                        self.world.message = f"Chargement échoué : {e}"
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    self.auto_delay = max(50, self.auto_delay - 50)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    self.auto_delay = min(2000, self.auto_delay + 50)
        return True

    def _step_agent(self):
        """Effectue une étape d'apprentissage (choix action, mise à jour Q)."""
        w = self.world
        if w.game_over:
            return
        s = encode_q_state(w)
        a = w.agent.choose_action(w)
        r = w.execute_action(a)
        s2 = encode_q_state(w)
        done = w.game_over or (not w.agent.is_alive)
        w.agent.learn(s, a, r, s2, done)
        w.agent.status = "Q-learning" + (" (exploration)" if w.agent.training else " (greedy)")

    def run(self):
        """Boucle principale du jeu."""
        timer = 0
        running = True
        while running:
            dt = self.clock.tick(60)
            running = self.handle_events()

            if self.auto_play and not self.world.game_over:
                timer += dt
                if timer >= self.auto_delay:
                    timer = 0
                    self._step_agent()

            self.screen.fill(UI_BG_DEEP)
            self.draw_grid()
            self.draw_info_panel()
            self.draw_bottom_bar()

            if self.world.game_over:
                overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE), pygame.SRCALPHA)
                overlay.fill((8,10,18,200))
                self.screen.blit(overlay, (0,0))
                box_w = min(WINDOW_SIZE - 40, 540)
                msg_lines = self._wrap_text(self.world.message, self.small_font, box_w - 32)
                box_h = min(108 + len(msg_lines)*(self.small_font.get_height()+4), WINDOW_SIZE - 40)
                bx = (WINDOW_SIZE - box_w)//2
                by = (WINDOW_SIZE - box_h)//2
                card = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
                pygame.draw.rect(card, (32,40,58,250), card.get_rect(), border_radius=12)
                pygame.draw.rect(card, UI_ACCENT_DIM, card.get_rect(), 2, border_radius=12)
                self.screen.blit(card, (bx, by))
                title = self.font_title.render("Fin de partie", True, UI_GOLD_UI)
                self.screen.blit(title, (bx + (box_w - title.get_width())//2, by + 14))
                my = by + 48
                for ln in msg_lines[:4]:
                    row = self.small_font.render(ln, True, UI_TEXT)
                    self.screen.blit(row, (bx + (box_w - row.get_width())//2, my))
                    my += row.get_height() + 4
                hint = self.small_font.render("[R] Nouvelle partie", True, UI_TEXT_MUTED)
                self.screen.blit(hint, (bx + (box_w - hint.get_width())//2, by + box_h - 28))

            pygame.display.flip()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()