"""
Visualiseur du noyau dynamique / bassins de cristallisation
-----------------------------------------------------------
Version initiale generee pour Topbrutus.

Dependances:
    pip install numpy matplotlib

Lancement:
    python noyau_dynamique_visualiseur.py

Controles:
    ESPACE : pause / reprise
    1..4   : changer de monde structurel
    n      : injecter une impulsion dans l'entree du bassin 1
    c      : effacer les traces
    h      : afficher / cacher l'aide
    a / z  : augmenter / diminuer la vitesse
    s / x  : augmenter / diminuer la coherence
    f / v  : augmenter / diminuer le feedback
    r      : reset complet
    clic   : selectionner un nud d'analyse (SOURCE / B1 / B2 / B3 / SORTIE)

Ce script montre :
- des "autoroutes dynamiques" gauche/droite ;
- des billes qui circulent ;
- 3 bassins de cristallisation ;
- une vue speciale de l'entree/sortie du premier bassin ;
- un changement de "monde structurel" qui modifie l'esthetique
  et la dynamique d'apparition des cristaux.
"""

import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle, Polygon
from matplotlib.collections import LineCollection


# ------------------------------------------------------------
# Outils geometriques
# ------------------------------------------------------------

def polyline_length(points):
    p = np.asarray(points, dtype=float)
    dif = p[1:] - p[:-1]
    seg = np.linalg.norm(dif, axis=1)
    return seg.sum(), seg


def sample_polyline(points, s):
    """
    Retourne la position echantillonnee le long d'une polyligne.
    s dans [0, 1].
    """
    p = np.asarray(points, dtype=float)
    s = float(np.clip(s, 0.0, 1.0))
    total, seg = polyline_length(p)
    if total == 0:
        return p[0].copy()

    dist = s * total
    acc = 0.0
    for i, length in enumerate(seg):
        if acc + length >= dist:
            t = (dist - acc) / max(length, 1e-9)
            return (1.0 - t) * p[i] + t * p[i + 1]
        acc += length
    return p[-1].copy()


def circle_points(cx, cy, r, start_deg, end_deg, n=20):
    ang = np.deg2rad(np.linspace(start_deg, end_deg, n))
    x = cx + r * np.cos(ang)
    y = cy + r * np.sin(ang)
    return np.column_stack([x, y])


def diamond(center, size):
    cx, cy = center
    return np.array([
        [cx, cy + size],
        [cx + size, cy],
        [cx, cy - size],
        [cx - size, cy],
    ])


# ------------------------------------------------------------
# Modele du moteur
# ------------------------------------------------------------

class DynamicCrystalEngine:
    def __init__(self):
        self.dt = 0.035
        self.time = 0.0
        self.speed = 1.0
        self.coherence = 0.55
        self.feedback = 0.25
        self.world_index = 0
        self.worlds = [
            ("MONDE 1  HELIX", "#69c8ff", "#ffba52", "#e0f6ff"),
            ("MONDE 2  TORUS", "#59f2d7", "#ff78cc", "#f5f7ff"),
            ("MONDE 3  GRID", "#84ff6c", "#ffd15a", "#f8ffef"),
            ("MONDE 4  OBSIDIAN", "#8fa8ff", "#ff8a73", "#fdf3f2"),
        ]
        self.paused = False
        self.show_help = True

        self.node_names = ["SOURCE", "B1", "B2", "B3", "SORTIE"]
        self.node_y = np.array([0.0, 2.0, 4.2, 6.4, 8.8], dtype=float)
        self.node_pos = {name: np.array([0.0, y]) for name, y in zip(self.node_names, self.node_y)}
        self.selected_node = "B1"

        # Ports speciaux du premier bassin
        self.b1_in = np.array([-3.1, self.node_y[1]])
        self.b1_out = np.array([3.1, self.node_y[1]])
        self.injection_port = np.array([-4.3, self.node_y[1] + 0.6])
        self.interception_port = np.array([4.3, self.node_y[1] - 0.6])

        # Historique des series
        self.max_hist = 320
        self.hist_t = []
        self.hist_inflow = []
        self.hist_outflow = []
        self.hist_crystal = []
        self.hist_coherence = []
        self.node_hist = {name: [] for name in self.node_names}

        # Billes / flux
        self.left_particles = np.linspace(0.0, 1.0, 18, endpoint=False)
        self.right_particles = np.linspace(0.1, 1.1, 18, endpoint=False) % 1.0
        self.center_pulses = np.linspace(0.0, 1.0, 15, endpoint=False)

        self.inject_pulse = 0.0
        self.crystals = []

        # Traces
        self.traces_enabled = True
        self.trace_points = []

        self._rebuild_paths()

    # ------------------------
    # Geometrie des autoroutes
    # ------------------------
    def _world_shape(self):
        """
        Parametres structurels selon le monde.
        amplitude laterale, rayon des roues, courbure.
        """
        if self.world_index == 0:   # helix
            return 1.9, 0.95, 0.35
        if self.world_index == 1:   # torus
            return 2.35, 1.12, 0.52
        if self.world_index == 2:   # grid
            return 1.45, 0.82, 0.20
        return 2.05, 1.00, 0.48    # obsidian

    def _rebuild_paths(self):
        amp, radius, curvature = self._world_shape()
        y = self.node_y

        # Autoroute gauche : montee laterale avec passage par chaque centre
        left = [(-0.35, y[0])]
        right = [(0.35, y[0])]

        for level in [1, 2, 3]:
            yy = y[level]
            # roue gauche
            left.extend(circle_points(-amp, yy, radius, 255, -75, n=26).tolist())
            left.append((0.0, yy))

            # roue droite
            right.extend(circle_points(amp, yy, radius, -75, 255, n=26).tolist())
            right.append((0.0, yy))

            # segment vers l'etage suivant / sortie
            y_next = y[level + 1]
            mid_y = yy + (y_next - yy) * 0.55
            if level < 3:
                left.append((-amp * (1.0 - curvature), mid_y))
                right.append((amp * (1.0 - curvature), mid_y))
            else:
                left.append((-0.3, mid_y))
                right.append((0.3, mid_y))

        left.append((0.0, y[-1]))
        right.append((0.0, y[-1]))

        self.left_path = np.array(left, dtype=float)
        self.right_path = np.array(right, dtype=float)

        # Retour externe (sortie -> source)
        self.outer_left = np.array([
            [-3.9, y[-1] - 0.2],
            [-5.1, 7.1],
            [-5.6, 4.6],
            [-5.1, 2.0],
            [-4.0, y[0] + 0.15],
        ])
        self.outer_right = np.array([
            [3.9, y[-1] - 0.2],
            [5.1, 7.1],
            [5.6, 4.6],
            [5.1, 2.0],
            [4.0, y[0] + 0.15],
        ])

        # Axe central
        self.center_path = np.column_stack([np.zeros(100), np.linspace(y[0], y[-1], 100)])

    # ------------------------
    # Monde / couleurs
    # ------------------------
    @property
    def world_name(self):
        return self.worlds[self.world_index][0]

    @property
    def colors(self):
        _, c_left, c_right, c_center = self.worlds[self.world_index]
        return c_left, c_right, c_center

    def switch_world(self, idx):
        self.world_index = int(idx) % len(self.worlds)
        self._rebuild_paths()
        # Changer aussi legerement la coherence pour montrer un nouvel etat
        self.coherence = np.clip(0.45 + 0.12 * self.world_index, 0.1, 0.95)

    # ------------------------
    # Dynamique interne
    # ------------------------
    def node_signal(self, name):
        t = self.time
        y_idx = self.node_names.index(name)
        phase = 0.55 * y_idx
        base = 0.45 + 0.30 * math.sin(2.0 * t + phase)
        mod = 0.18 * math.sin(5.0 * t - 0.7 * phase)
        sync = 0.20 * self.coherence
        return max(0.0, base + mod + sync)

    def step(self):
        if self.paused:
            return

        self.time += self.dt * self.speed

        # Progression des billes
        delta = 0.007 + 0.012 * self.speed
        self.left_particles = (self.left_particles + delta * (0.8 + 0.5 * self.coherence)) % 1.0
        self.right_particles = (self.right_particles + delta * (0.85 + 0.4 * self.feedback)) % 1.0
        self.center_pulses = (self.center_pulses + delta * 1.55) % 1.0

        # Signaux bassin 1 : entree / sortie
        inflow = (
            0.95
            + 0.55 * math.sin(2.3 * self.time)
            + 0.28 * math.sin(6.2 * self.time + 1.2)
            + self.inject_pulse
        )
        inflow *= (0.80 + 0.40 * self.coherence)

        crystal_index = max(0.0, inflow * (0.45 + self.coherence) * (1.0 + 0.5 * self.feedback))
        outflow = (
            0.62 * inflow
            + 0.26 * crystal_index
            + 0.18 * math.sin(2.3 * self.time - 0.9)
        )
        outflow = max(0.0, outflow)

        # Decroissance de l'impulsion injectee
        self.inject_pulse *= 0.92

        # Historique
        self.hist_t.append(self.time)
        self.hist_inflow.append(inflow)
        self.hist_outflow.append(outflow)
        self.hist_crystal.append(crystal_index)
        self.hist_coherence.append(self.coherence)
        for name in self.node_names:
            self.node_hist[name].append(self.node_signal(name))

        if len(self.hist_t) > self.max_hist:
            self.hist_t.pop(0)
            self.hist_inflow.pop(0)
            self.hist_outflow.pop(0)
            self.hist_crystal.pop(0)
            self.hist_coherence.pop(0)
            for name in self.node_names:
                self.node_hist[name].pop(0)

        # Apparition de nouveaux cristaux
        spawn_gate = crystal_index > 1.35 and (len(self.hist_t) % 4 == 0)
        if spawn_gate:
            size = 0.10 + 0.08 * min(1.0, crystal_index / 2.8)
            drift = 0.04 + 0.015 * self.world_index
            self.crystals.append({
                "x": self.b1_out[0] + 0.2,
                "y": self.b1_out[1] + 0.15 * math.sin(self.time * 2.0),
                "vx": drift + 0.02 * self.coherence,
                "vy": 0.02 * math.sin(self.time * 1.7),
                "size": size,
                "age": 0,
                "ttl": 85 + 25 * self.world_index
            })

        alive = []
        for c in self.crystals:
            c["x"] += c["vx"]
            c["y"] += c["vy"]
            c["age"] += 1
            if c["age"] < c["ttl"] and c["x"] < 6.0:
                alive.append(c)
        self.crystals = alive

        # Traces
        if self.traces_enabled:
            selected_pos = self.node_pos[self.selected_node]
            signal = self.node_signal(self.selected_node)
            self.trace_points.append((selected_pos[0], selected_pos[1], signal))
            if len(self.trace_points) > 240:
                self.trace_points.pop(0)

    def inject(self):
        self.inject_pulse += 1.15

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.coherence = 0.55
        self.feedback = 0.25
        self.left_particles = np.linspace(0.0, 1.0, 18, endpoint=False)
        self.right_particles = np.linspace(0.1, 1.1, 18, endpoint=False) % 1.0
        self.center_pulses = np.linspace(0.0, 1.0, 15, endpoint=False)
        self.inject_pulse = 0.0
        self.crystals = []
        self.trace_points = []
        self.hist_t.clear()
        self.hist_inflow.clear()
        self.hist_outflow.clear()
        self.hist_crystal.clear()
        self.hist_coherence.clear()
        for name in self.node_names:
            self.node_hist[name].clear()

    def clear_traces(self):
        self.trace_points = []


# ------------------------------------------------------------
# Vue / Visualisation
# ------------------------------------------------------------

class EngineVisualizer:
    def __init__(self, engine: DynamicCrystalEngine):
        self.engine = engine
        self.fig = plt.figure(figsize=(16, 10), facecolor="#071018")
        gs = GridSpec(2, 3, figure=self.fig, width_ratios=[2.2, 1.05, 1.25], height_ratios=[1.0, 1.0], wspace=0.18, hspace=0.18)

        self.ax_main = self.fig.add_subplot(gs[:, 0])
        self.ax_b1 = self.fig.add_subplot(gs[0, 1])
        self.ax_probe = self.fig.add_subplot(gs[1, 1])
        self.ax_info = self.fig.add_subplot(gs[:, 2])

        self._setup_axes()
        self._connect_events()

        self.anim = FuncAnimation(self.fig, self._update, interval=35, blit=False)

    def _setup_axes(self):
        bg = "#071018"
        for ax in [self.ax_main, self.ax_b1, self.ax_probe, self.ax_info]:
            ax.set_facecolor(bg)

        # Main
        self.ax_main.set_xlim(-6.2, 6.2)
        self.ax_main.set_ylim(-0.8, 9.8)
        self.ax_main.set_xticks([])
        self.ax_main.set_yticks([])
        self.ax_main.set_title("MOTEUR VISUALISABLE  Noyau dynamique / autoroutes de cristallisation", color="white", fontsize=14, pad=12)

        # B1 dashboard
        self.ax_b1.set_title("BASSIN 1  Entree / sortie / cristallisation", color="white", fontsize=12, pad=10)
        self.ax_b1.set_xlim(0, 1)
        self.ax_b1.set_ylim(0, 1)
        self.ax_b1.set_xticks([])
        self.ax_b1.set_yticks([])

        # Probe
        self.ax_probe.set_title("SONDE D'ANALYSE  point selectionne", color="white", fontsize=12, pad=10)

        # Info
        self.ax_info.set_xlim(0, 1)
        self.ax_info.set_ylim(0, 1)
        self.ax_info.set_xticks([])
        self.ax_info.set_yticks([])
        self.ax_info.set_title("PILOTAGE / LEGENDE", color="white", fontsize=12, pad=10)

    def _connect_events(self):
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)
        self.fig.canvas.mpl_connect("button_press_event", self._on_click)

    def _on_key(self, event):
        e = self.engine
        key = (event.key or "").lower()
        if key == " ":
            e.paused = not e.paused
        elif key in ("1", "2", "3", "4"):
            e.switch_world(int(key) - 1)
        elif key == "n":
            e.inject()
        elif key == "c":
            e.clear_traces()
        elif key == "h":
            e.show_help = not e.show_help
        elif key == "a":
            e.speed = min(3.0, e.speed + 0.1)
        elif key == "z":
            e.speed = max(0.2, e.speed - 0.1)
        elif key == "s":
            e.coherence = min(0.98, e.coherence + 0.03)
        elif key == "x":
            e.coherence = max(0.05, e.coherence - 0.03)
        elif key == "f":
            e.feedback = min(1.2, e.feedback + 0.03)
        elif key == "v":
            e.feedback = max(0.0, e.feedback - 0.03)
        elif key == "r":
            e.reset()

    def _on_click(self, event):
        if event.inaxes != self.ax_main or event.xdata is None or event.ydata is None:
            return
        click = np.array([event.xdata, event.ydata], dtype=float)
        e = self.engine
        best_name = None
        best_dist = 1e9
        for name, pos in e.node_pos.items():
            d = np.linalg.norm(click - pos)
            if d < best_dist:
                best_dist = d
                best_name = name
        if best_name is not None and best_dist < 1.2:
            e.selected_node = best_name

    # ------------------------
    # Dessin principal
    # ------------------------
    def _draw_main(self):
        ax = self.ax_main
        ax.clear()
        ax.set_facecolor("#071018")
        ax.set_xlim(-6.2, 6.2)
        ax.set_ylim(-0.8, 9.8)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title("MOTEUR VISUALISABLE  Noyau dynamique / autoroutes de cristallisation", color="white", fontsize=14, pad=12)

        e = self.engine
        c_left, c_right, c_center = e.colors

        # Halo du monde
        ax.text(0.02, 0.98, e.world_name, transform=ax.transAxes, ha="left", va="top", color="#d7e5ff", fontsize=11, weight="bold")
        ax.text(0.98, 0.98, "clic sur un nud = analyse", transform=ax.transAxes, ha="right", va="top", color="#9bb6d7", fontsize=10)

        # Autoroutes / lignes de fond
        ax.plot(e.left_path[:, 0], e.left_path[:, 1], color=c_left, lw=3.2, alpha=0.8)
        ax.plot(e.right_path[:, 0], e.right_path[:, 1], color=c_right, lw=3.2, alpha=0.8)
        ax.plot(e.center_path[:, 0], e.center_path[:, 1], color=c_center, lw=4.0, alpha=0.55)
        ax.plot(e.outer_left[:, 0], e.outer_left[:, 1], color="#8bbcff", lw=1.6, alpha=0.45, ls="--")
        ax.plot(e.outer_right[:, 0], e.outer_right[:, 1], color="#ffcf88", lw=1.6, alpha=0.45, ls="--")

        # Fleches du retour
        for pts, col in [(e.outer_left, "#8bbcff"), (e.outer_right, "#ffcf88")]:
            for frac in [0.22, 0.52, 0.82]:
                p1 = sample_polyline(pts, max(0.0, frac - 0.03))
                p2 = sample_polyline(pts, min(1.0, frac + 0.03))
                ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=16, color=col, lw=0))

        # Nuds
        for name, pos in e.node_pos.items():
            y = pos[1]
            radius = 0.22 if name != "SORTIE" else 0.28
            glow = Circle(pos, radius * 2.2, fc="none", ec="#a8dcff", lw=1.0, alpha=0.18)
            node = Circle(pos, radius, fc="#0e2438", ec="white", lw=1.8)
            ax.add_patch(glow)
            ax.add_patch(node)
            signal = e.node_signal(name)
            inner = Circle(pos, radius * (0.35 + 0.35 * min(1.0, signal / 1.4)), fc="#dff9ff", ec="none", alpha=0.92)
            ax.add_patch(inner)
            if name == e.selected_node:
                ring = Circle(pos, radius * 1.75, fc="none", ec="#ffe780", lw=2.2, alpha=0.95)
                ax.add_patch(ring)
            ax.text(pos[0], y + 0.38, name, color="white", fontsize=10, ha="center", va="bottom", weight="bold")

        # Connexions horizontales des bassins
        for yy in e.node_y[1:4]:
            ax.hlines(yy, -0.55, 0.55, color="#e6f7ff", lw=2.4, alpha=0.6)

        # Ports speciaux bassin 1
        ax.scatter(*e.b1_in, s=90, c="#7dff8d", marker="o", edgecolors="white", zorder=5)
        ax.scatter(*e.b1_out, s=90, c="#ff7bd0", marker="o", edgecolors="white", zorder=5)
        ax.scatter(*e.injection_port, s=120, c="#95d9ff", marker="^", edgecolors="white", zorder=5)
        ax.scatter(*e.interception_port, s=120, c="#ffd982", marker="v", edgecolors="white", zorder=5)
        ax.plot([e.b1_in[0], 0.0], [e.b1_in[1], e.node_y[1]], color="#7dff8d", lw=2.4, alpha=0.7)
        ax.plot([0.0, e.b1_out[0]], [e.node_y[1], e.b1_out[1]], color="#ff7bd0", lw=2.4, alpha=0.7)
        ax.plot([e.injection_port[0], e.b1_in[0]], [e.injection_port[1], e.b1_in[1]], color="#95d9ff", lw=1.5, alpha=0.75, ls="--")
        ax.plot([e.b1_out[0], e.interception_port[0]], [e.b1_out[1], e.interception_port[1]], color="#ffd982", lw=1.5, alpha=0.75, ls="--")
        ax.text(e.b1_in[0], e.b1_in[1] + 0.35, "ENTREE BASSIN 1", color="#b8ffc2", fontsize=9, ha="center")
        ax.text(e.b1_out[0], e.b1_out[1] + 0.35, "SORTIE BASSIN 1", color="#ffb8ef", fontsize=9, ha="center")
        ax.text(e.injection_port[0] - 0.15, e.injection_port[1] + 0.25, "INJECTION", color="#b9e7ff", fontsize=8, ha="center")
        ax.text(e.interception_port[0] + 0.15, e.interception_port[1] - 0.35, "INTERCEPTION", color="#ffe5ae", fontsize=8, ha="center")

        # Billes sur les autoroutes
        left_pts = np.array([sample_polyline(e.left_path, s) for s in e.left_particles])
        right_pts = np.array([sample_polyline(e.right_path, s) for s in e.right_particles])
        center_pts = np.array([sample_polyline(e.center_path, s) for s in e.center_pulses])

        ax.scatter(left_pts[:, 0], left_pts[:, 1], s=34, c=c_left, edgecolors="white", linewidths=0.6, zorder=10)
        ax.scatter(right_pts[:, 0], right_pts[:, 1], s=34, c=c_right, edgecolors="white", linewidths=0.6, zorder=10)
        ax.scatter(center_pts[:, 0], center_pts[:, 1], s=20, c=c_center, edgecolors="none", alpha=0.75, zorder=9)

        # Petits cercles / "roues"
        amp, radius, curvature = e._world_shape()
        for yy in e.node_y[1:4]:
            ax.add_patch(Circle((-amp, yy), radius, fc="none", ec=c_left, lw=1.2, alpha=0.35))
            ax.add_patch(Circle((amp, yy), radius, fc="none", ec=c_right, lw=1.2, alpha=0.35))

        # Cristaux emis
        crystal_color = "#c9fff4" if e.world_index in (0, 2) else "#ffe0ff"
        for c in e.crystals:
            age_ratio = 1.0 - c["age"] / max(c["ttl"], 1)
            poly = diamond((c["x"], c["y"]), c["size"] * (0.55 + 0.45 * age_ratio))
            patch = Polygon(poly, closed=True, fc=crystal_color, ec="white", lw=0.9, alpha=0.25 + 0.7 * age_ratio)
            ax.add_patch(patch)

        # Traces
        if e.trace_points:
            tp = np.array(e.trace_points)
            sizes = 10 + 30 * np.clip(tp[:, 2], 0, 1.8) / 1.8
            ax.scatter(tp[:, 0], tp[:, 1], s=sizes, c="#ffe780", alpha=0.12, edgecolors="none", zorder=2)

        # Legendes structurelles
        ax.text(-5.35, 8.8, "retour externe", color="#8bbcff", fontsize=10, rotation=90, va="top")
        ax.text(5.35, 8.8, "retour externe", color="#ffcf88", fontsize=10, rotation=270, va="top")
        ax.text(0.0, -0.35, "SOURCE", color="#dff9ff", fontsize=12, ha="center", weight="bold")
        ax.text(0.0, 9.25, "SORTIE / EMERGENCE", color="#ffffff", fontsize=12, ha="center", weight="bold")

        # Aide
        if e.show_help:
            help_box = (
                "Commandes\n"
                "espace = pause | 1..4 = mondes | n = injection\n"
                "a/z = vitesse | s/x = coherence | f/v = feedback\n"
                "c = effacer traces | r = reset | h = aide"
            )
            ax.text(0.02, 0.02, help_box, transform=ax.transAxes, ha="left", va="bottom",
                    fontsize=9, color="#dbe8ff",
                    bbox=dict(boxstyle="round,pad=0.35", fc="#0d1c2b", ec="#27445f", alpha=0.85))

    # ------------------------
    # Dashboard bassin 1
    # ------------------------
    def _draw_b1_panel(self):
        ax = self.ax_b1
        ax.clear()
        ax.set_facecolor("#071018")
        ax.set_title("BASSIN 1  Entree / sortie / cristallisation", color="white", fontsize=12, pad=10)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])

        e = self.engine
        c_left, c_right, c_center = e.colors

        # Mini schema
        ax.text(0.12, 0.90, "entree", color="#7dff8d", fontsize=10, ha="center")
        ax.text(0.88, 0.90, "sortie", color="#ff7bd0", fontsize=10, ha="center")
        ax.plot([0.14, 0.42], [0.62, 0.62], color="#7dff8d", lw=4)
        ax.plot([0.58, 0.86], [0.62, 0.62], color="#ff7bd0", lw=4)
        ax.add_patch(Circle((0.50, 0.62), 0.09, fc="#0e2438", ec="white", lw=1.5))
        ax.add_patch(Circle((0.50, 0.62), 0.04 + 0.04 * min(1.0, (e.hist_crystal[-1] if e.hist_crystal else 0.0)/2.0),
                            fc="#dff9ff", ec="none"))
        ax.text(0.50, 0.49, "bassin 1", color="white", fontsize=10, ha="center")

        # Autoroutes miniatures
        ax.plot([0.15, 0.26, 0.38, 0.50], [0.76, 0.86, 0.74, 0.62], color=c_left, lw=2.2, alpha=0.9)
        ax.plot([0.50, 0.62, 0.74, 0.85], [0.62, 0.74, 0.86, 0.76], color=c_right, lw=2.2, alpha=0.9)
        ax.scatter([0.15, 0.50, 0.85], [0.76, 0.62, 0.76], s=[40, 55, 40], c=[c_left, c_center, c_right], edgecolors="white", linewidths=0.7)

        # Barres numeriques
        inflow = e.hist_inflow[-1] if e.hist_inflow else 0.0
        outflow = e.hist_outflow[-1] if e.hist_outflow else 0.0
        crystal = e.hist_crystal[-1] if e.hist_crystal else 0.0

        values = [("inflow", inflow, "#7dff8d"), ("outflow", outflow, "#ff7bd0"), ("crystal", crystal, "#ffe780")]
        y0 = 0.34
        for i, (label, value, color) in enumerate(values):
            yy = y0 - 0.10 * i
            ax.text(0.08, yy, label, color="white", fontsize=9, ha="left", va="center")
            ax.add_patch(Rectangle((0.28, yy - 0.025), 0.58, 0.05, fc="#102233", ec="#27445f", lw=0.8))
            fill = min(1.0, value / 2.4)
            ax.add_patch(Rectangle((0.28, yy - 0.025), 0.58 * fill, 0.05, fc=color, ec="none", alpha=0.95))
            ax.text(0.89, yy, f"{value:0.2f}", color=color, fontsize=9, ha="left", va="center")

        # Mini historique
        if len(e.hist_t) > 10:
            xs = np.linspace(0.08, 0.92, len(e.hist_t))
            def norm(arr, low=0.06, high=0.18):
                arr = np.asarray(arr)
                if arr.ptp() < 1e-9:
                    return np.full_like(arr, low + 0.5*(high-low), dtype=float)
                return low + (arr - arr.min()) / arr.ptp() * (high - low)

            yin = norm(e.hist_inflow, 0.05, 0.20)
            yout = norm(e.hist_outflow, 0.05, 0.20)
            ax.plot(xs, yin, color="#7dff8d", lw=1.5)
            ax.plot(xs, yout, color="#ff7bd0", lw=1.5)
            ax.text(0.08, 0.225, "historique court", color="#8faecc", fontsize=8, ha="left")

    # ------------------------
    # Panneau sonde
    # ------------------------
    def _draw_probe_panel(self):
        ax = self.ax_probe
        ax.clear()
        ax.set_facecolor("#071018")
        ax.set_title("SONDE D'ANALYSE  point selectionne", color="white", fontsize=12, pad=10)

        e = self.engine
        name = e.selected_node
        hist = e.node_hist[name]
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#37506c")
        ax.spines["bottom"].set_color("#37506c")
        ax.tick_params(colors="#bcd0e8", labelsize=9)

        if len(hist) > 3:
            x = np.arange(len(hist))
            ax.plot(x, hist, color="#ffe780", lw=2.0, label=f"signal {name}")
            ax.plot(x, e.hist_coherence, color="#80c6ff", lw=1.2, alpha=0.8, label="coherence")
            ax.fill_between(x, 0, hist, color="#ffe780", alpha=0.15)
            ax.set_xlim(0, max(40, len(hist)-1))
            ax.set_ylim(0, max(1.7, np.max(hist) + 0.2))
            ax.grid(color="#18324b", alpha=0.35, ls="--")
            ax.legend(loc="upper left", facecolor="#0d1c2b", edgecolor="#27445f", labelcolor="white")
        else:
            ax.text(0.5, 0.5, "attente de donnees...", color="#9bb6d7", ha="center", va="center", transform=ax.transAxes)

        ax.set_xlabel("echantillons", color="#dfefff")
        ax.set_ylabel("amplitude relative", color="#dfefff")
        ax.text(0.99, 0.96, f"point = {name}", transform=ax.transAxes, ha="right", va="top",
                color="#ffffff", fontsize=10,
                bbox=dict(boxstyle="round,pad=0.25", fc="#102233", ec="#27445f", alpha=0.9))

    # ------------------------
    # Panneau d'infos
    # ------------------------
    def _draw_info_panel(self):
        ax = self.ax_info
        ax.clear()
        ax.set_facecolor("#071018")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title("PILOTAGE / LEGENDE", color="white", fontsize=12, pad=10)

        e = self.engine
        inflow = e.hist_inflow[-1] if e.hist_inflow else 0.0
        outflow = e.hist_outflow[-1] if e.hist_outflow else 0.0
        crystal = e.hist_crystal[-1] if e.hist_crystal else 0.0
        c_left, c_right, c_center = e.colors

        lines = [
            ("temps", f"{e.time:0.2f}"),
            ("vitesse", f"{e.speed:0.2f}"),
            ("coherence", f"{e.coherence:0.2f}"),
            ("feedback", f"{e.feedback:0.2f}"),
            ("monde", e.world_name),
            ("sonde", e.selected_node),
            ("cristaux actifs", str(len(e.crystals))),
            ("B1 inflow", f"{inflow:0.2f}"),
            ("B1 outflow", f"{outflow:0.2f}"),
            ("B1 crystal", f"{crystal:0.2f}"),
        ]

        y = 0.93
        for label, val in lines:
            ax.text(0.05, y, label, color="#90aecd", fontsize=10, ha="left", va="center")
            ax.text(0.95, y, val, color="white", fontsize=10, ha="right", va="center")
            y -= 0.055

        # Legende visuelle
        y -= 0.02
        ax.text(0.05, y, "LEGENDE", color="#ffffff", fontsize=11, weight="bold", ha="left")
        y -= 0.06
        legend = [
            (c_left, "courant gauche / voie A"),
            (c_right, "courant droit / voie B"),
            (c_center, "axe central / synchronisation"),
            ("#7dff8d", "entree du bassin 1"),
            ("#ff7bd0", "sortie du bassin 1"),
            ("#95d9ff", "port d'injection"),
            ("#ffd982", "port d'interception"),
            ("#ffe780", "trace / activite de sonde"),
        ]
        for color, text in legend:
            ax.scatter([0.07], [y], s=70, c=color, edgecolors="white", linewidths=0.6)
            ax.text(0.12, y, text, color="white", fontsize=9, ha="left", va="center")
            y -= 0.05

        y -= 0.02
        desc = (
            "Idee generale\n"
            " Les billes montrent les flux sur les autoroutes.\n"
            " Les nuds centraux sont les points de passage obligatoires.\n"
            " Le premier bassin est detaille a part pour voir\n"
            "  entrees, sorties, injections et cristaux emergents.\n"
            " Le changement de monde structurel modifie la geometrie,\n"
            "  les couleurs et le style d'apparition des cristaux.\n"
            " On peut analyser un point different en cliquant un nud."
        )
        ax.text(0.05, y, desc, color="#d9e8ff", fontsize=9, ha="left", va="top",
                bbox=dict(boxstyle="round,pad=0.35", fc="#0d1c2b", ec="#27445f", alpha=0.85))

    def _update(self, frame):
        self.engine.step()
        self._draw_main()
        self._draw_b1_panel()
        self._draw_probe_panel()
        self._draw_info_panel()
        return []

    def show(self):
        plt.show()


def main():
    engine = DynamicCrystalEngine()
    viz = EngineVisualizer(engine)
    viz.show()


if __name__ == "__main__":
    main()

[executed on device: Topbrutus (e13fd46c-c560-41e2-9c1c-bd2561c44abb)]