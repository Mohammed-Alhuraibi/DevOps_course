#!/usr/bin/env python3
"""Draw the twelve slides of the "Introduction to Kubernetes" lesson.

    kubernetes/images/slides/k8s-00-what-we-build.svg ... k8s-11-compose-to-kubernetes.svg

Same palette, type, logos and slide frame as the containers lesson: the drawing kit is
docs/images/src/svgkit.py, and a few slide helpers (monospace text, the shipping box, badges)
come from docs/images/src/build_slides.py. Real names only: every object name, image tag,
port and limit below comes from kubernetes/manifests/. Standard library only:

    python3 kubernetes/images/src/build_k8s_slides.py
"""

import argparse
import math
import os
import sys

K8S_SRC = os.path.dirname(os.path.abspath(__file__))              # kubernetes/images/src
REPO = os.path.dirname(os.path.dirname(os.path.dirname(K8S_SRC)))
KIT = os.path.join(REPO, "docs", "images", "src")
sys.path.insert(0, KIT)
from svgkit import *  # noqa: E402,F401,F403  shared tokens, helpers, icons and logos
import build_slides as cs  # noqa: E402  slide helpers of the containers lesson

OUT_DIR = os.path.join(os.path.dirname(K8S_SRC), "slides")   # K8S_SRC, because svgkit's star import brings its own HERE
TOTAL = 12
X0, X1 = 80, 1520
GEN = "kubernetes/images/src/build_k8s_slides.py"


# ---------------------------------------------------------------------------
# Frame and Kubernetes vocabulary
# ---------------------------------------------------------------------------
def frame(n, title, subtitle):
    """Title, subtitle and footer (lesson name, progress, N / 12); n counts from 1."""
    out = [text(X0, 112, title, 52, 800, INK, spacing=-0.8),
           text(X0, 158, subtitle, 24, 400, CAP)]
    check_fit("title", title, 52, 800, X1 - X0)
    check_fit("subtitle", subtitle, 24, 400, X1 - X0)
    out.append(logo("kubernetes", X0, 836, 28))
    out.append(text(X0 + 38, 857, "Kubernetes", 18, 700, TEXT))
    seg, gap = 22, 5
    total = TOTAL * seg + (TOTAL - 1) * gap
    sx = X1 - 74 - total
    for i in range(TOTAL):
        col = ACCENT if i + 1 == n else (FAINT if i + 1 < n else HAIR)
        out.append(rect(sx + i * (seg + gap), 848, seg, 6, 3, fill=col))
    out.append(text(X1, 858, f"{n} / {TOTAL}", 20, 800, INK, "end"))
    return "".join(out)


def pod(x, y, w, h, slug=None, name="", sub=None, hl=False, faded=False, size=18):
    """A pod is a pea pod: a capsule around its container (the pea)."""
    r = h / 2
    out = []
    if hl:
        out.append(rect(x - 6, y - 6, w + 12, h + 12, r + 6, fill=ACCENT_HALO))
    out.append(rect(x, y, w, h, r, fill=WHITE, stroke=ACCENT if hl else LINE, stroke_width=2.5 if hl else 1.8,
                    filter=None if faded else "url(#shadow)"))
    pr = r - 6
    out.append(circle(x + r, y + r, pr, fill=SOFT))
    if slug:
        out.append(logo(slug, x + r - pr * 0.62, y + r - pr * 0.62, pr * 1.24))
    tx = x + 2 * r + 4
    if sub:
        out.append(text(tx, y + r - 3, name, size, 700, INK))
        out.append(text(tx, y + r + 18, sub, 16, 400, CAP))
    else:
        out.append(text(tx, y + r + size * 0.36, name, size, 700, INK))
    check_fit("pod " + name, name, size, 700, w - (tx - x) - r * 0.6)
    return group(out, 0.38 if faded else None)


def obj(x, y, w, kind, name, hl=False, icon=None, h=60):
    """A Kubernetes object card: its kind (small, grey) over its name (bold)."""
    out = []
    if hl:
        out.append(rect(x - 6, y - 6, w + 12, h + 12, R_CHIP + 6, fill=ACCENT_HALO))
    out.append(rect(x, y, w, h, R_CHIP, fill=WHITE, stroke=ACCENT if hl else LINE, stroke_width=2.5 if hl else 1.5,
                    filter="url(#shadow)"))
    tx = x + 16
    if icon:
        out.append(icon(x + 14, y + (h - 30) / 2, 30))
        tx = x + 56
    out.append(text(tx, y + 24, kind, 16, 600, CAP))
    out.append(text(tx, y + 48, name, 19, 800, INK))
    check_fit("obj " + name, name, 19, 800, w - (tx - x) - 10)
    return "".join(out)


def k8s_ic(x, y, s):
    return logo("kubernetes", x, y, s)


def control_plane(x, y, w, h, parts=("API server", "scheduler", "controller manager", "etcd"), sub="run by Google · replicated in 3 zones"):
    out = [rect(x, y, w, h, 14, fill=INK),
           logo("kubernetes", x + 18, y + (h - 30) / 2, 30, color=WHITE),
           text(x + 60, y + h / 2 - 3, "Control plane", 21, 800, WHITE),
           text(x + 60, y + h / 2 + 20, sub, 16.5, 400, "#D1D5DB")]
    cx = x + w - 16
    for p in reversed(parts):
        cw = text_width(p, 16.5, 600) + 24
        cx -= cw
        out.append(rect(cx, y + (h - 32) / 2, cw, 32, 8, fill="#374151"))
        out.append(text(cx + cw / 2, y + h / 2 + 6, p, 16.5, 600, WHITE, "middle"))
        cx -= 8
    return "".join(out)


def node_card(x, y, w, h, title="node", cap="e2-medium", stopped=False):
    out = [card(x, y, w, h, "normal", r=14),
           cs.ic_server(x + 14, y + 14, 24, 26, INK if not stopped else FAINT),
           text(x + 48, y + 34, title, 19, 800, INK if not stopped else FAINT),
           text(x + 48 + text_width(title, 19, 800) + 8, y + 34, cap, 16.5, 400, CAP if not stopped else FAINT)]
    return "".join(out)


def browser_card(x, y, w, h, url="k8s.gulfheight.com", cap=None):
    out = [card(x, y, w, h, "normal", r=12)]
    for i in range(3):
        out.append(circle(x + 18 + i * 14, y + 17, 4.5, fill=LINE))
    out.append(rect(x + 12, y + 32, w - 24, 34, R_CHIP, fill=SOFT))
    out.append(ic_lock(x + 22, y + 39, 18, INK, SOFT))
    out.append(text(x + 46, y + 55, url, 17, 600, INK))
    check_fit("url", url, 17, 600, w - 24 - 42)
    if cap:
        out.append(text(x + w / 2, y + h - 16, cap, 17, 600, TEXT, "middle"))
        check_fit("browser cap", cap, 17, 600, w - 16)
    return "".join(out)


def lb_card(x, y, w, h, title="Google Cloud load balancer", cap="one static IP · bugsquash-ip", hl=False):
    out = []
    if hl:
        out.append(rect(x - 6, y - 6, w + 12, h + 12, R_CARD + 6, fill=ACCENT_HALO))
    out.append(card(x, y, w, h, "new" if hl else "normal"))
    out.append(logo("googlecloud", x + 16, y + (h - 34) / 2, 34))
    out.append(text(x + 62, y + h / 2 - 4, title, 20, 800, INK))
    out.append(text(x + 62, y + h / 2 + 20, cap, 17, 400, CAP))
    check_fit("lb", title, 20, 800, w - 72)
    return "".join(out)


def kubectl_chip(x, y, cmd, size=19, hl=True):
    w = cs.mono_w(cmd, size) + 28
    out = rect(x, y, w, 38, 10, fill=INK) + cs.mono(x + 14, y + 26, cmd, size, WHITE if not hl else "#FBCFE8", weight=700)
    return out, w


def rail(x0, x1, y, color=LINE, wdt=8):
    return rect(x0, y - wdt / 2, x1 - x0, wdt, wdt / 2, fill=color)


def stem(x, y0, y1, color=LINE, wdt=5):
    return rect(x - wdt / 2, y0, wdt, y1 - y0, 0, fill=color)


def curve_arrow(cx, cy, r, a0, a1, color=ACCENT, wdt=4):
    """An arc from angle a0 to a1 (degrees, counter-clockwise, 0 = right) with a head at a1."""
    def pt(a):
        rad = math.radians(a)
        return cx + r * math.cos(rad), cy - r * math.sin(rad)
    (sx, sy), (ex, ey) = pt(a0), pt(a1 - 6 if a1 > a0 else a1 + 6)
    large = 1 if abs(a1 - a0) > 180 else 0
    sweep = 0 if a1 > a0 else 1
    out = [path(f"M{f(round(sx, 2))} {f(round(sy, 2))} A{r} {r} 0 {large} {sweep} {f(round(ex, 2))} {f(round(ey, 2))}",
                fill="none", stroke=color, stroke_width=wdt, stroke_linecap="round")]
    tx, ty = pt(a1)
    bx, by = pt(a1 - 0.5 if a1 > a0 else a1 + 0.5)
    dx, dy = tx - bx, ty - by
    n = (dx * dx + dy * dy) ** 0.5 or 1
    ux, uy = dx / n, dy / n
    L, half = 16, 9
    hx, hy = tx - ux * L, ty - uy * L
    out.append(path(f"M{f(round(tx, 2))} {f(round(ty, 2))} L{f(round(hx - uy * half, 2))} {f(round(hy + ux * half, 2))} "
                    f"L{f(round(hx + uy * half, 2))} {f(round(hy - ux * half, 2))}Z", fill=color))
    return "".join(out)


def ic_chef(x, y, s, color):
    k = s / 24.0
    return (circle(x + 7 * k, y + 9 * k, 5 * k, fill=color) + circle(x + 12 * k, y + 6.5 * k, 6 * k, fill=color)
            + circle(x + 17 * k, y + 9 * k, 5 * k, fill=color) + rect(x + 6 * k, y + 9 * k, 12 * k, 10 * k, 1.5 * k, fill=color)
            + rect(x + 6 * k, y + 20 * k, 12 * k, 3.2 * k, 1.2 * k, fill=color))


def ic_clipboard(x, y, s, color):
    k = s / 24.0
    out = [rect(x + 4 * k, y + 3 * k, 16 * k, 20 * k, 2.5 * k, fill=color),
           rect(x + 8 * k, y + 1 * k, 8 * k, 5 * k, 2 * k, fill=color, stroke=WHITE, stroke_width=1.4 * k)]
    for i in range(3):
        out.append(rect(x + 7.5 * k, y + (10 + i * 4) * k, 9 * k, 1.8 * k, 0.9 * k, fill=WHITE))
    return "".join(out)


def ic_phone(x, y, s, color):
    k = s / 24.0
    return path(f"M{f(x + 6.6 * k)} {f(y + 2 * k)} L{f(x + 9.6 * k)} {f(y + 6.8 * k)} L{f(x + 7.6 * k)} {f(y + 9.2 * k)} "
                f"Q{f(x + 10 * k)} {f(y + 14 * k)} {f(x + 14.8 * k)} {f(y + 16.4 * k)} L{f(x + 17.2 * k)} {f(y + 14.4 * k)} "
                f"L{f(x + 22 * k)} {f(y + 17.4 * k)} L{f(x + 20.6 * k)} {f(y + 21 * k)} Q{f(x + 19 * k)} {f(y + 23 * k)} {f(x + 15 * k)} {f(y + 22 * k)} "
                f"Q{f(x + 6 * k)} {f(y + 19 * k)} {f(x + 2.4 * k)} {f(y + 9 * k)} Q{f(x + 1.6 * k)} {f(y + 5 * k)} {f(x + 3.4 * k)} {f(y + 3.4 * k)}Z",
                fill=color)


def ic_ticket(x, y, w, h, color):
    r = h * 0.16
    return (path(f"M{f(x)} {f(y + 6)} Q{f(x)} {f(y)} {f(x + 6)} {f(y)} H{f(x + w - 6)} Q{f(x + w)} {f(y)} {f(x + w)} {f(y + 6)} "
                 f"V{f(y + h / 2 - r)} A{f(r)} {f(r)} 0 0 0 {f(x + w)} {f(y + h / 2 + r)} V{f(y + h - 6)} Q{f(x + w)} {f(y + h)} {f(x + w - 6)} {f(y + h)} "
                 f"H{f(x + 6)} Q{f(x)} {f(y + h)} {f(x)} {f(y + h - 6)} V{f(y + h / 2 + r)} A{f(r)} {f(r)} 0 0 0 {f(x)} {f(y + h / 2 - r)}Z", fill=color)
            + line(x + w * 0.26, y + 8, x + w * 0.26, y + h - 8, stroke=WHITE, stroke_width=2, opacity=0.6))


def ic_hanger(x, y, s, color):
    k = s / 24.0
    return path(f"M{f(x + 12 * k)} {f(y + 8 * k)} V{f(y + 6 * k)} Q{f(x + 12 * k)} {f(y + 2 * k)} {f(x + 15 * k)} {f(y + 2.5 * k)} "
                f"M{f(x + 12 * k)} {f(y + 8 * k)} L{f(x + 2 * k)} {f(y + 17 * k)} Q{f(x + 1 * k)} {f(y + 19 * k)} {f(x + 3 * k)} {f(y + 19 * k)} "
                f"H{f(x + 21 * k)} Q{f(x + 23 * k)} {f(y + 19 * k)} {f(x + 22 * k)} {f(y + 17 * k)}Z",
                fill="none", stroke=color, stroke_width=2.2 * k, stroke_linejoin="round", stroke_linecap="round")


def disk(x, y, w, h, color=INK):
    """A Google Persistent Disk: a cylinder with the Google Cloud logo."""
    ry = h * 0.14
    return (path(f"M{f(x)} {f(y + ry)} V{f(y + h - ry)} A{f(w / 2)} {f(ry)} 0 0 0 {f(x + w)} {f(y + h - ry)} V{f(y + ry)}", fill=color)
            + f'<ellipse {attrs(cx=x + w / 2, cy=y + ry, rx=w / 2, ry=ry, fill="#374151", stroke=WHITE, stroke_width=2)}/>'
            + circle(x + w / 2, y + h * 0.58, min(w, h) * 0.22, fill=WHITE)
            + logo("googlecloud", x + w / 2 - min(w, h) * 0.15, y + h * 0.58 - min(w, h) * 0.15, min(w, h) * 0.3))


def thermostat(cx, cy, r, value="21°"):
    out = [circle(cx, cy, r, fill=WHITE, stroke=INK, stroke_width=6),
           curve_arrow(cx, cy, r - 18, 225, -20, ACCENT, 8),
           text(cx, cy + 16, value, round(r * 0.55), 800, INK, "middle")]
    return "".join(out)


def note(x, y, w, h, title, body, icon="warn"):
    out = [card(x, y, w, h, "normal")]
    if icon == "warn":
        out.append(ic_warn(x + 22, y + h / 2 - 17, 34, INK))
    out.append(text(x + 74, y + h / 2 - 6, title, 21, 800, INK))
    out.append(text(x + 74, y + h / 2 + 22, body, 18.5, 400, CAP))
    check_fit("note", body, 18.5, 400, w - 84)
    check_fit("note title", title, 21, 800, w - 84)
    return "".join(out)


# ---------------------------------------------------------------------------
# 00 What we'll build
# ---------------------------------------------------------------------------
ZONES = ["a", "b", "c"]


def zones_row(x0, x1, y, h, fill_zone=None, stopped=None):
    """Three zone columns, each with one node. Returns (svg, [(node_x, node_y, node_w)])."""
    gap = 24
    zw = (x1 - x0 - 2 * gap) / 3
    out, nodes = [], []
    for i, z in enumerate(ZONES):
        zx = x0 + i * (zw + gap)
        out.append(rect(zx, y, zw, h, R_CARD, fill=WASH, stroke=HAIR, stroke_width=1.5))
        out.append(text(zx + 16, y + 28, f"zone {z}", 19, 800, TEXT))
        out.append(text(zx + 16 + text_width(f"zone {z}", 19, 800) + 8, y + 28, f"europe-central2-{z}", 16.5, 400, CAP))
        nodes.append((zx + 14, y + 44, zw - 28))
    return "".join(out), nodes


def slide_00():
    out = [frame(1, "What we\u2019ll build",
                 "Bug Squash Arena on Google Kubernetes Engine: one address, three zones, copies everywhere.")]
    # who comes in, from where
    out.append(browser_card(X0, 200, 300, 84))
    out.append(arrow([(X0 + 300, 242), (436, 242)], "normal"))
    out.append(label(408, 230, "HTTPS", "normal", size=17))
    out.append(lb_card(440, 200, 460, 84, cap="static IP bugsquash-ip \u00b7 made by the Ingress"))
    lap_x = 1160
    out.append(card(lap_x, 200, X1 - lap_x, 84, "normal"))
    out.append(cs.ic_laptop(lap_x + 18, 220, 54, INK))
    out.append(text(lap_x + 90, 232, "your laptop", 20, 800, INK))
    chip_svg, _ = kubectl_chip(lap_x + 90, 240, "kubectl apply -f", 17)
    out.append(chip_svg)
    # the cluster
    cx0, cy0, cy1 = X0, 316, 800
    out.append(rect(cx0, cy0, X1 - cx0, cy1 - cy0, R_CARD + 4, fill=WHITE, stroke=FAINT, stroke_width=2.5))
    out.append(logo("kubernetes", cx0 + 20, cy0 + 12, 30))
    out.append(text(cx0 + 60, cy0 + 36, "GKE regional cluster", 22, 800, INK))
    out.append(text(cx0 + 60 + text_width("GKE regional cluster", 22, 800) + 10, cy0 + 36, "europe-central2", 17, 400, CAP))
    # traffic enters through the Ingress, left of the control plane
    ex = 552
    out.append(arrow([(ex, 284), (ex, 446)], "normal"))
    out.append(text(ex - 16, 386, "Ingress bugsquash", 18, 800, INK, "end"))
    out.append(text(ex - 16, 410, "/api \u2192 backend \u00b7 / \u2192 frontend", 16.5, 400, CAP, "end"))
    out.append(control_plane(ex + 32, 360, X1 - 24 - ex - 32, 60, parts=("API server", "scheduler", "controllers", "etcd")))
    out.append(arrow([(1340, 284), (1340, 358)], "normal"))
    out.append(label(1354, 308, "kubectl", "normal", "start", size=17))
    # services rail, then the zones
    ry = 452
    out.append(rail(cx0 + 24, X1 - 24, ry))
    out.append(text(cx0 + 24, ry - 12, "Services: frontend \u00b7 backend \u00b7 postgres", 16.5, 600, CAP))
    zs, nodes = zones_row(cx0 + 24, X1 - 24, 472, 264)
    out.append(zs)
    for i, (nx, ny, nw) in enumerate(nodes):
        out.append(stem(nx + nw * 0.8, ry, ny))
        out.append(node_card(nx, ny, nw, 206, "node", "e2-medium"))
        pw = (nw - 16 * 2 - 12) / 2
        out.append(pod(nx + 16, ny + 52, pw, 56, "vite", "frontend"))
        out.append(pod(nx + 16 + pw + 12, ny + 52, pw, 56, "nodedotjs", "backend"))
        if i == 0:
            out.append(pod(nx + 16, ny + 124, pw, 56, "postgresql", "postgres"))
            out.append(disk(nx + 16 + pw + 24, ny + 118, 46, 64))
            out.append(text(nx + 16 + pw + 82, ny + 146, "postgres-", 16.5, 600, TEXT))
            out.append(text(nx + 16 + pw + 82, ny + 166, "data 5Gi", 16.5, 600, TEXT))
    # cluster-wide settings and storage
    sy = 748
    out.append(text(cx0 + 24, sy + 24, "Also in the cluster:", 17, 700, CAP))
    x = cx0 + 24 + text_width("Also in the cluster: ", 17, 700) + 6
    for kind, name in (("ConfigMap", "bugsquash-config"), ("Secret", "bugsquash-secrets"),
                       ("PersistentVolumeClaim", "postgres-data")):
        w = text_width(kind + " " + name, 17, 700) + 52
        out.append(rect(x, sy, w, 34, R_CHIP, fill=SOFT))
        if kind == "ConfigMap":
            out.append(cs.ic_doc(x + 12, sy + 6, 16, 22, CAP, 2))
        elif kind == "Secret":
            out.append(ic_lock(x + 10, sy + 6, 20, CAP, SOFT))
        else:
            out.append(ic_ticket(x + 8, sy + 9, 26, 16, CAP))
        out.append(text(x + 40, sy + 23, kind, 17, 400, CAP))
        out.append(text(x + 40 + text_width(kind + " ", 17, 400), sy + 23, name, 17, 700, INK))
        x += w + 12
    if x > X1 - 24:
        FIT_PROBLEMS.append("cluster chips too wide")
    return out, ("What we'll build: visitors reach k8s.gulfheight.com through a Google Cloud load balancer with the static IP "
                 "bugsquash-ip, made by the Ingress bugsquash; inside a GKE regional cluster in europe-central2 the Services lead "
                 "to three zones a, b and c, each with one e2-medium node running a frontend and a backend pod, and zone a also runs "
                 "postgres with its 5Gi disk; a control plane run by Google, replicated in 3 zones, takes kubectl commands from your "
                 "laptop; the ConfigMap bugsquash-config, the Secret bugsquash-secrets and the claim postgres-data live in the cluster too.")


# ---------------------------------------------------------------------------
# 01 Why Kubernetes?
# ---------------------------------------------------------------------------
def slide_01():
    out = [frame(2, "Why Kubernetes?",
                 "On one VM you are the safety net. On a cluster you declare what you want and Kubernetes keeps it true.")]
    # left: one VM
    out.append(text(X0, 236, "Docker Compose on one VM", 26, 800, INK))
    srv, (vx, vy, vw, vh) = cs.server_frame(X0, 260, 300, 236, "one VM")
    out.append(srv)
    for k, (slug, nm) in enumerate((("nginx", "proxy"), ("vite", "frontend"), ("nodedotjs", "backend"), ("postgresql", "db"))):
        yy = vy + 4 + k * 42
        out.append(rect(vx + 4, yy, vw - 8, 36, 8, fill=SOFT))
        out.append(logo(slug, vx + 14, yy + 6, 24))
        out.append(text(vx + 48, yy + 24, nm, 18, 700, INK))
    rows_bad = [("VM dies:", "the site dies"), ("More visitors:", "resize by hand"), ("New version:", "by hand, brief downtime")]
    for k, (a, b) in enumerate(rows_bad):
        y = 300 + k * 70
        out.append(cs.bad_badge(X0 + 352, y, 18))
        out.append(text(X0 + 384, y - 4, a, 20, 800, INK))
        out.append(text(X0 + 384, y + 22, b, 19, 400, CAP))
    out.append(line(800, 214, 800, 540, stroke=HAIR, stroke_width=2))
    # right: a cluster
    rx = 840
    out.append(text(rx, 236, "A Kubernetes cluster", 26, 800, INK))
    for k in range(3):
        nx = rx + k * 112
        out.append(card(nx, 262, 100, 108, "normal", r=12))
        out.append(cs.ic_server(nx + 12, 274, 20, 22, INK))
        out.append(text(nx + 38, 291, "node", 16.5, 700, INK))
        out.append(pod(nx + 10, 310, 80, 44, "vite", ""))
    out.append(text(rx, 410, "3 machines, pods spread over them", 18, 400, CAP))
    rows_ok = [("Heals:", "a pod dies, a new one starts"), ("Scales:", "3 → 5 copies with one line"),
               ("Updates, no downtime:", "one pod at a time")]
    for k, (a, b) in enumerate(rows_ok):
        y = 300 + k * 70
        out.append(cs.ok_badge(rx + 372, y, 18))
        out.append(text(rx + 404, y - 4, a, 20, 800, INK))
        out.append(text(rx + 404, y + 22, b, 19, 400, CAP))
        check_fit("ok row", b, 19, 400, X1 - rx - 404)
    # the thermostat band
    by = 568
    out.append(rect(X0, by, X1 - X0, 224, R_CARD, fill=WASH))
    out.append(thermostat(X0 + 132, by + 112, 82))
    out.append(text(X0 + 260, by + 76, "Like a thermostat", 28, 800, INK))
    out.append(text(X0 + 260, by + 116, "You set 21 °C. It heats or cools until the room is 21 °C, and keeps it there.", 21, 400, TEXT))
    out.append(text(X0 + 260, by + 160, "You write", 21, 400, TEXT))
    cw = text_width("You write ", 21, 400)
    out.append(rect(X0 + 260 + cw, by + 134, cs.mono_w("replicas: 3", 21) + 20, 36, 8, fill=INK))
    out.append(cs.mono(X0 + 270 + cw, by + 160, "replicas: 3", 21, WHITE, weight=700))
    out.append(text(X0 + 260 + cw + cs.mono_w("replicas: 3", 21) + 32, by + 160, "and Kubernetes keeps 3 copies running, whatever happens.", 21, 400, TEXT))
    return out, ("Why Kubernetes: with Docker Compose on one VM, the site dies with the VM and scaling and updates are manual; "
                 "a Kubernetes cluster spreads pods over several machines and heals, scales and updates them. Like a thermostat "
                 "set to 21 degrees, you write replicas: 3 and Kubernetes keeps 3 copies running.")


# ---------------------------------------------------------------------------
# 02 The cluster: brain and workers
# ---------------------------------------------------------------------------
def slide_02():
    out = [frame(3, "The cluster: brain and workers",
                 "The control plane decides, the worker nodes do the work: a restaurant’s manager and its cooks.")]
    # laptop
    out.append(card(X0, 300, 220, 140, "normal"))
    out.append(cs.ic_laptop(X0 + 80, 318, 60, INK))
    out.append(text(X0 + 110, 386, "your laptop", 19, 800, INK, "middle"))
    chip_svg, _ = kubectl_chip(X0 + 46, 398, "kubectl", 17)
    out.append(chip_svg)
    # control plane: the manager
    px, py, pw, ph = 360, 212, X1 - 360, 268
    out.append(rect(px, py, pw, ph, R_CARD, fill=INK))
    out.append(ic_clipboard(px + 22, py + 18, 32, WHITE))
    out.append(text(px + 66, py + 44, "Control plane", 26, 800, WHITE))
    out.append(text(px + 66 + text_width("Control plane", 26, 800) + 12, py + 44, "the manager", 22, 400, "#D1D5DB"))
    out.append(logo("googlecloud", px + pw - 268, py + 20, 28))
    out.append(text(px + pw - 232, py + 42, "on GKE: run by Google", 19, 700, WHITE))
    comps = [("API server", "the front desk: every", "request goes through it"),
             ("scheduler", "picks a node for", "every new pod"),
             ("controller manager", "keeps reality equal", "to the plan"),
             ("etcd", "the notebook: the", "whole cluster's state")]
    cw = (pw - 24 * 2 - 16 * 3) / 4
    for k, (t, c1, c2) in enumerate(comps):
        x = px + 24 + k * (cw + 16)
        out.append(rect(x, py + 76, cw, 168, 12, fill="#1F2937", stroke="#374151", stroke_width=1.5))
        if k == 0:
            out.append(rect(x - 5, py + 71, cw + 10, 178, 16, fill="none", stroke=ACCENT, stroke_width=3))
        out.append(text(x + 18, py + 116, t, 22, 800, WHITE))
        out.append(text(x + 18, py + 158, c1, 18, 400, "#D1D5DB"))
        out.append(text(x + 18, py + 184, c2, 18, 400, "#D1D5DB"))
        check_fit("comp", c1, 18, 400, cw - 28)
        check_fit("comp", c2, 18, 400, cw - 28)
    out.append(arrow([(X0 + 220, 370), (px + 20, 370)], "new"))
    # workers: the cooks
    wy, wh = 540, 252
    gap = 24
    ww = (X1 - X0 - 2 * gap) / 3
    for k in range(3):
        x = X0 + k * (ww + gap)
        out.append(card(x, wy, ww, wh, "normal"))
        out.append(ic_chef(x + 18, wy + 14, 30, INK))
        out.append(text(x + 58, wy + 38, f"worker node {k + 1}", 21, 800, INK))
        out.append(text(x + 58 + text_width(f"worker node {k + 1}", 21, 800) + 8, wy + 38, "a cook", 18, 400, CAP))
        for j, (t, c) in enumerate((("kubelet", "follows the manager's orders"), ("containerd", "runs the containers"),
                                    ("kube-proxy", "routes Service traffic"))):
            yy = wy + 60 + j * 44
            out.append(rect(x + 16, yy, ww - 32, 36, 8, fill=SOFT))
            out.append(text(x + 30, yy + 24, t, 17.5, 800, INK))
            out.append(text(x + 30 + 124, yy + 24, c, 17, 400, CAP))
            check_fit("worker", c, 17, 400, ww - 32 - 138)
        out.append(pod(x + 16, wy + 194, (ww - 44) / 2, 46, "vite", "pod"))
        out.append(pod(x + 28 + (ww - 44) / 2, wy + 194, (ww - 44) / 2, 46, "nodedotjs", "pod"))
        ax = max(x + ww / 2, px + 60)
        out.append(arrow([(ax, py + ph), (ax, wy - 2)], "normal"))
    out.append(label(px + 74, 516, "orders", "normal", "start", size=17))
    return out, ("The cluster: the control plane is the manager (API server, scheduler, controller manager and etcd; on GKE "
                 "Google runs it) and kubectl on your laptop talks only to the API server; three worker nodes are the cooks, "
                 "each with kubelet, containerd and kube-proxy, running the pods.")


# ---------------------------------------------------------------------------
# 03 Pods
# ---------------------------------------------------------------------------
POD_YAML = [("apiVersion: v1", 0), ("kind: Pod", 0), ("metadata:", 1), ("  name: hello-frontend", 1),
            ("  labels: { app: hello }", 1), ("spec:", 2), ("  containers:", 2), ("  - name: frontend", 2),
            ("    image: …/bugsquash-frontend:sha-0902b98", 2), ("    ports: [{ containerPort: 8080 }]", 2)]


def slide_03():
    out = [frame(4, "Pods",
                 "The smallest thing Kubernetes runs: one or more containers that share an IP address.")]
    # the pea pod
    px, py, pw, ph = X0 + 10, 236, 700, 236
    out.append(rect(px - 8, py - 8, pw + 16, ph + 16, ph / 2 + 8, fill=ACCENT_HALO))
    out.append(rect(px, py, pw, ph, ph / 2, fill=WHITE, stroke=ACCENT, stroke_width=4))
    peas = [(px + 150, True), (px + 380, False)]
    for cxp, main in peas:
        out.append(circle(cxp, py + ph / 2, 92, fill=SOFT if main else WASH, stroke=LINE if main else HAIR, stroke_width=2))
        if main:
            out.append(cs.box(cxp - 62, py + ph / 2 - 36, 124, 72))
            out.append(rect(cxp - 46, py + ph / 2 - 20, 92, 40, 8, fill=WHITE))
            out.append(logo("vite", cxp - 14, py + ph / 2 - 14, 28))
        else:
            out.append(text(cxp, py + ph / 2 - 4, "+ helper", 19, 700, FAINT, "middle"))
            out.append(text(cxp, py + ph / 2 + 22, "(optional)", 17, 400, FAINT, "middle"))
    ipx = px + pw - 196
    out.append(rect(ipx, py + ph / 2 - 26, 150, 52, 26, fill=INK))
    out.append(text(ipx + 75, py + ph / 2 - 3, "its own IP", 16.5, 700, WHITE, "middle"))
    out.append(cs.mono(ipx + 30, py + ph / 2 + 18, "10.8.1.12", 16, "#FBCFE8"))
    out.append(text(px + 150, py + ph + 44, "a container", 20, 700, TEXT, "middle"))
    out.append(text(px + 150, py + ph + 70, "(the pea)", 18, 400, CAP, "middle"))
    out.append(text(px + pw / 2 + 120, py + ph + 44, "the pod (the shell around it)", 20, 700, ACCENT_TEXT, "middle"))
    # the file
    fx, fy, fw = 880, 220, X1 - 880
    out.append(card(fx, fy, fw, 404, "normal"))
    out.append(cs.ic_doc(fx + 22, fy + 18, 26, 32, INK, 2))
    out.append(text(fx + 60, fy + 42, "01-pod.yaml", 21, 800, INK))
    groups = {0: ("WHAT", "it is"), 1: ("NAME", "and labels"), 2: ("WANT", "the spec")}
    starts = {}
    for i, (ln, g) in enumerate(POD_YAML):
        y = fy + 88 + i * 31
        out.append(cs.mono(fx + 24, y, ln, 17, INK if not ln.startswith(" ") else TEXT, weight=700 if not ln.startswith(" ") else 400))
        starts.setdefault(g, [y, y])
        starts[g][1] = y
        if cs.mono_w(ln, 17) > fw - 150:
            FIT_PROBLEMS.append("pod yaml line too long: " + ln)
    for g, (a, b) in starts.items():
        bx = fx + fw - 104
        out.append(rect(bx, a - 18, 5, b - a + 26, 2.5, fill=ACCENT))
        out.append(text(bx + 14, (a + b) / 2 - 2, groups[g][0], 17, 800, ACCENT_TEXT))
        out.append(text(bx + 14, (a + b) / 2 + 18, groups[g][1], 15.5, 400, CAP))
    # mortal
    my = 676
    out.append(rect(X0, my, X1 - X0, 116, R_CARD, fill=WASH))
    out.append(pod(X0 + 24, my + 30, 250, 56, "vite", "hello-frontend"))
    chip_svg, w = kubectl_chip(X0 + 316, my + 39, "kubectl delete pod hello-frontend", 18)
    out.append(chip_svg)
    out.append(arrow([(X0 + 280, my + 58), (X0 + 312, my + 58)], "normal"))
    gx = X0 + 316 + w + 40
    out.append(arrow([(gx - 36, my + 58), (gx - 4, my + 58)], "normal"))
    out.append(cs.ic_trash(gx, my + 40, 36, GREY))
    out.append(text(gx + 52, my + 52, "Gone for good.", 22, 800, INK))
    out.append(text(gx + 52, my + 82, "A lone pod is never brought back: that is the next slide's job.", 18.5, 400, CAP))
    return out, ("Pods: a pod is the shell around one or more containers, like a pea pod around its peas, and it has its own IP "
                 "address; 01-pod.yaml shows the four parts of every Kubernetes file (apiVersion and kind = what, metadata = name "
                 "and labels, spec = what you want); kubectl delete pod hello-frontend removes it for good.")


# ---------------------------------------------------------------------------
# 04 Deployments
# ---------------------------------------------------------------------------
def slide_04():
    out = [frame(5, "Deployments",
                 "You declare 3 copies. A controller compares that with reality and fixes every difference.")]
    lx = X0
    out.append(obj(lx + 220, 214, 380, "Deployment", "frontend · replicas: 3", hl=True, icon=k8s_ic))
    out.append(arrow([(lx + 410, 280), (lx + 410, 318)], "normal"))
    out.append(obj(lx + 220, 320, 380, "ReplicaSet (made by the Deployment)", "frontend-7c9d5", icon=k8s_ic))
    pods_y = 452
    xs = [lx, lx + 214, lx + 428, lx + 642]
    for k, x in enumerate(xs):
        if k == 3:
            continue
        out.append(arrow([(lx + 410, 386), (lx + 410, 412), (x + 96, 412), (x + 96, pods_y - 4)], "normal"))
    out.append(pod(xs[0], pods_y, 192, 58, "vite", "frontend", "running"))
    out.append(pod(xs[1], pods_y, 192, 58, "vite", "frontend", "crashed", faded=True))
    out.append(cs.bad_badge(xs[1] + 182, pods_y + 4, 15))
    out.append(pod(xs[2], pods_y, 192, 58, "vite", "frontend", "running"))
    out.append(pod(xs[3], pods_y, 192, 58, "vite", "frontend", "new copy", hl=True))
    out.append(arrow([(xs[1] + 96, pods_y + 70), (xs[1] + 96, pods_y + 96), (xs[3] + 96, pods_y + 96), (xs[3] + 96, pods_y + 66)], "new"))
    out.append(label((xs[1] + xs[3]) / 2 + 96, pods_y + 124, "the controller starts a replacement", "new", size=18))
    # scale
    sy = 660
    out.append(rect(X0, sy, 860, 132, R_CARD, fill=WASH))
    chip_svg, w = kubectl_chip(X0 + 24, sy + 18, "kubectl scale deployment frontend --replicas=5", 18)
    out.append(chip_svg)
    for k in range(5):
        out.append(pod(X0 + 24 + k * 164, sy + 72, 150, 44, "vite", "copy", hl=k >= 3))
    # the control loop
    cx, cy, r = 1210, 470, 168
    out.append(text(cx, 236, "The control loop", 26, 800, INK, "middle"))
    out.append(curve_arrow(cx, cy, r, 50, -40, ACCENT, 5))
    out.append(curve_arrow(cx, cy, r, 230, 140, ACCENT, 5))
    for (yy, t1, t2) in ((cy - r - 2, "Desired", "3 copies (your YAML)"), (cy + r + 2, "Actual", "2 running (one crashed)")):
        out.append(rect(cx - 150, yy - 38, 300, 76, 14, fill=WHITE, stroke=LINE, stroke_width=1.5, filter="url(#shadow)"))
        out.append(text(cx, yy - 6, t1, 22, 800, INK, "middle"))
        out.append(text(cx, yy + 22, t2, 18, 400, CAP, "middle"))
    out.append(text(cx + r + 16, cy + 6, "compare", 19, 700, ACCENT_TEXT))
    out.append(text(cx - r - 16, cy - 10, "fix: start", 19, 700, ACCENT_TEXT, "end"))
    out.append(text(cx - r - 16, cy + 14, "1 pod", 19, 700, ACCENT_TEXT, "end"))
    out.append(text(cx, cy - 4, "every few", 18, 400, CAP, "middle"))
    out.append(text(cx, cy + 20, "seconds", 18, 400, CAP, "middle"))
    return out, ("Deployments: the Deployment frontend declares replicas: 3 and owns a ReplicaSet that owns the pods; when a pod "
                 "crashes the controller starts a new copy, because it compares the desired state (3) with the actual state (2) "
                 "every few seconds; kubectl scale deployment frontend --replicas=5 changes the goal to 5.")


# ---------------------------------------------------------------------------
# 05 Services
# ---------------------------------------------------------------------------
def slide_05():
    out = [frame(6, "Services",
                 "One stable name in front of changing pods. It finds them by label and spreads the calls.")]
    # callers
    out.append(text(X0, 238, "Callers", 22, 800, INK))
    callers = [("the Ingress", "for /api"), ("any pod", "http://backend:3000")]
    for k, (a, b) in enumerate(callers):
        y = 264 + k * 104
        out.append(card(X0, y, 300, 84, "normal"))
        out.append(text(X0 + 20, y + 36, a, 21, 800, INK))
        out.append(text(X0 + 20, y + 64, b, 18, 400, CAP))
        out.append(arrow([(X0 + 300, y + 42), (476, 372)], "normal"))
    # the service
    sx, sy, sw, sh = 480, 290, 380, 164
    out.append(rect(sx - 8, sy - 8, sw + 16, sh + 16, R_CARD + 8, fill=ACCENT_HALO))
    out.append(card(sx, sy, sw, sh, "new"))
    out.append(ic_phone(sx + 22, sy + 22, 40, ACCENT))
    out.append(text(sx + 78, sy + 40, "Service", 17, 600, CAP))
    out.append(text(sx + 78, sy + 68, "backend", 28, 800, INK))
    out.append(rect(sx + 22, sy + 96, sw - 44, 48, R_CHIP, fill=SOFT))
    out.append(cs.mono(sx + 38, sy + 127, "selector: app=backend", 18, INK, weight=700))
    # the pods behind it
    px = 1040
    pods = [("10.8.0.14", False, False), ("10.8.2.7 \u00b7 gone", True, False), ("10.8.2.15 \u00b7 new", False, True), ("10.8.1.9", False, False)]
    ys = [220, 330, 330, 440]
    for k, ((ip, gone, new), y) in enumerate(zip(pods, ys)):
        x = px if k != 2 else px + 240
        out.append(pod(x, y, 220, 64, "nodedotjs", "backend", ip, hl=new, faded=gone))
        out.append(group([cs.ic_tag(x + 188, y - 10, 22, CAP)], 0.38 if gone else None))
    out.append(arrow([(px + 220, 362), (px + 236, 362)], "new"))
    for y, tx in ((252, px), (362, px + 240), (472, px)):
        out.append(arrow([(sx + sw, sy + sh / 2), (tx - 4, y)], "new"))
    out.append(text(px + 250, 424, "replaced: new IP,", 18, 700, ACCENT_TEXT))
    out.append(text(px + 250, 448, "same Service name", 18, 400, CAP))
    out.append(text(px, 540, "pods labelled app=backend", 18, 700, TEXT))
    # the metaphor + DNS
    my = 608
    out.append(rect(X0, my, X1 - X0, 184, R_CARD, fill=WASH))
    out.append(ic_phone(X0 + 30, my + 40, 52, INK))
    out.append(text(X0 + 104, my + 64, "Like a company phone number", 26, 800, INK))
    out.append(text(X0 + 104, my + 100, "You call one number and any free agent answers. Agents can change; the number never does.", 21, 400, TEXT))
    out.append(text(X0 + 104, my + 146, "Inside the cluster, DNS turns the name", 20, 400, TEXT))
    w1 = text_width("Inside the cluster, DNS turns the name ", 20, 400)
    out.append(cs.mono(X0 + 104 + w1, my + 146, "backend", 20, INK, weight=700))
    w2 = cs.mono_w("backend ", 20)
    out.append(text(X0 + 104 + w1 + w2, my + 146, "into the Service's fixed IP: no pod IP is ever typed by hand.", 20, 400, TEXT))
    return out, ("Services: callers (the Ingress for /api, or any pod at http://backend:3000) reach the Service backend, which "
                 "selects every ready pod labelled app=backend and spreads the calls; when a pod is replaced it gets a new IP but "
                 "the name stays, like a company phone number that rings any free agent.")


# ---------------------------------------------------------------------------
# 06 ConfigMaps and Secrets
# ---------------------------------------------------------------------------
def slide_06():
    out = [frame(7, "ConfigMaps and Secrets",
                 "The same image everywhere. The settings come from outside, as environment variables.")]
    # .env.prod of the Docker stages
    ex, ey, ew, eh = X0, 236, 330, 360
    out.append(card(ex, ey, ew, eh, "normal"))
    out.append(cs.ic_doc(ex + 20, ey + 18, 26, 32, INK, 2))
    out.append(text(ex + 58, ey + 42, ".env.prod", 22, 800, INK))
    out.append(text(ex + 20, ey + 76, "from the Docker stages", 17, 400, CAP))
    lines = ["NODE_ENV=production", "PGHOST=…", "PGUSER=bugsquash", "TRUST_PROXY=2",
             "POSTGRES_PASSWORD=•••", "JWT_SECRET=•••"]
    for i, ln in enumerate(lines):
        y = ey + 120 + i * 38
        out.append(cs.mono(ex + 20, y, ln, 17, INK if i < 4 else ACCENT_TEXT, weight=400 if i < 4 else 700))
    # split into two objects
    cx = 500
    out.append(arrow([(ex + ew, ey + 140), (cx - 4, 300)], "normal"))
    out.append(arrow([(ex + ew, ey + 300), (cx - 4, 548)], "normal"))
    out.append(card(cx, 214, 400, 236, "normal"))
    out.append(cs.ic_doc(cx + 20, 230, 24, 30, INK, 2))
    out.append(text(cx + 56, 240, "ConfigMap", 16.5, 600, CAP))
    out.append(text(cx + 56, 264, "bugsquash-config", 21, 800, INK))
    keys = ["NODE_ENV", "COOKIE_SECURE", "TRUST_PROXY", "POSTGRES_DB", "PGHOST  PGPORT", "PGUSER  PGDATABASE"]
    for i, k in enumerate(keys):
        out.append(cs.mono(cx + 24, 302 + i * 25, k, 16.5, TEXT))
    out.append(text(cx + 400 - 18, 302, "plain", 16.5, 600, CAP, "end"))
    out.append(text(cx + 400 - 18, 324, "settings", 16.5, 600, CAP, "end"))
    sy = 478
    out.append(rect(cx - 8, sy - 8, 416, 156, R_CARD + 8, fill=ACCENT_HALO))
    out.append(card(cx, sy, 400, 140, "new"))
    out.append(ic_lock(cx + 20, sy + 16, 26, ACCENT, WHITE))
    out.append(text(cx + 56, sy + 26, "Secret", 16.5, 600, CAP))
    out.append(text(cx + 56, sy + 50, "bugsquash-secrets", 21, 800, INK))
    out.append(cs.mono(cx + 24, sy + 88, "POSTGRES_PASSWORD  •••", 16.5, INK, weight=700))
    out.append(cs.mono(cx + 24, sy + 116, "JWT_SECRET         •••", 16.5, INK, weight=700))
    # into the pod
    bx, by, bw, bh = 1020, 300, X1 - 1020, 270
    out.append(card(bx, by, bw, bh, "normal"))
    out.append(pod(bx + 20, by + 20, 260, 60, "nodedotjs", "backend pod", "image unchanged"))
    envs = [("envFrom: the ConfigMap", "every key, as env vars"), ("PGPASSWORD", "← the Secret"), ("JWT_SECRET", "← the Secret")]
    for i, (a, b) in enumerate(envs):
        y = by + 122 + i * 46
        out.append(rect(bx + 20, y - 26, bw - 40, 38, 8, fill=SOFT))
        out.append(cs.mono(bx + 32, y, a, 16.5, INK, weight=700))
        out.append(text(bx + bw - 32, y, b, 16.5, 400, CAP, "end"))
    out.append(arrow([(cx + 400, 332), (bx - 4, 392)], "normal"))
    out.append(arrow([(cx + 400, sy + 70), (bx - 4, 480)], "new"))
    out.append(label(958, 330, "env vars", "normal", size=17))
    # the warning
    out.append(note(X0, 676, X1 - X0, 112, "A Secret is base64, not encryption",
                    "Anyone allowed to read it can decode it: echo c2VjcmV0 | base64 -d prints “secret”. So: never in Git, and few readers."))
    return out, ("ConfigMaps and Secrets: the .env.prod file of the Docker stages splits into the ConfigMap bugsquash-config "
                 "(NODE_ENV, COOKIE_SECURE, TRUST_PROXY, POSTGRES_DB, PGHOST, PGPORT, PGUSER, PGDATABASE) and the Secret "
                 "bugsquash-secrets (POSTGRES_PASSWORD, JWT_SECRET); both reach the unchanged backend image as environment "
                 "variables. Secrets are only base64 encoded, not encrypted.")


# ---------------------------------------------------------------------------
# 07 Storage
# ---------------------------------------------------------------------------
def slide_07():
    out = [frame(8, "Storage",
                 "The pod shows a ticket and gets its disk. Delete the pod: the disk stays, and the new pod gets it back.")]
    old, new = (X0, 226, 300, 92), (X0 + 560, 226, 300, 92)
    out.append(pod(old[0], old[1], old[2], old[3], "postgresql", "postgres", "deleted", faded=True, size=21))
    out.append(group([cs.ic_trash(old[0] + old[2] - 52, old[1] + 30, 30, GREY)], 0.6))
    out.append(pod(new[0], new[1], new[2], new[3], "postgresql", "postgres", "the new pod", size=21))
    out.append(arrow([(old[0] + old[2] + 16, 272), (new[0] - 16, 272)], "normal"))
    out.append(label((old[0] + old[2] + new[0]) / 2, 258, "replaced", "normal", size=19))
    # the ticket both pods show
    tx, ty, tw, th = X0 + 250, 420, 360, 112
    for (x, y, w, h), alive in ((old, False), (new, True)):
        cxp = x + w / 2
        col = INK if alive else FAINT
        out.append(group([path(f"M{cxp} {y + h} V{ty - 40} Q{cxp} {ty - 22} {cxp + (20 if cxp < tx + tw / 2 else -20)} {ty - 22} "
                               f"H{tx + tw / 2 + (-40 if cxp < tx + tw / 2 else 40)} Q{tx + tw / 2 + (-20 if cxp < tx + tw / 2 else 20)} {ty - 22} "
                               f"{tx + tw / 2 + (-20 if cxp < tx + tw / 2 else 20)} {ty - 4}",
                               fill="none", stroke=col, stroke_width=4, stroke_linecap="round", stroke_linejoin="round"),
                          circle(cxp, y + h, 6, fill=col)], None if alive else 0.7))
    out.append(ic_ticket(tx, ty, tw, th, ACCENT))
    out.append(text(tx + tw * 0.26 + 20, ty + 40, "PersistentVolumeClaim", 17, 600, "#FCE7F3"))
    out.append(text(tx + tw * 0.26 + 20, ty + 72, "postgres-data", 25, 800, WHITE))
    out.append(text(tx + tw * 0.26 + 20, ty + 96, "5 GiB · ReadWriteOnce", 16.5, 400, "#FCE7F3"))
    out.append(text(tx + tw * 0.13, ty + th / 2 + 9, "5Gi", 22, 800, WHITE, "middle"))
    # the disk it is bound to
    out.append(arrow([(tx + tw / 2, ty + th + 4), (tx + tw / 2, 600)], "normal"))
    out.append(label(tx + tw / 2 + 14, ty + th + 44, "bound to", "normal", "start", size=18))
    out.append(disk(tx + tw / 2 - 70, 604, 140, 176))
    out.append(text(tx + tw / 2 + 92, 676, "PersistentVolume", 17, 600, CAP))
    out.append(text(tx + tw / 2 + 92, 704, "a Google Persistent Disk", 21, 800, INK))
    out.append(text(tx + tw / 2 + 92, 732, "it lives outside every pod", 18, 400, CAP))
    # the cloakroom
    rx = 1060
    out.append(line(1010, 220, 1010, 790, stroke=HAIR, stroke_width=2))
    out.append(text(rx, 248, "Like a cloakroom", 26, 800, INK))
    rows = [(lambda x, y: ic_ticket(x, y + 6, 48, 30, ACCENT), "The claim is the ticket", "“I need a 5 GiB disk”"),
            (lambda x, y: ic_hanger(x + 4, y, 42, INK), "The volume is the coat", "a real disk Google keeps for you"),
            (lambda x, y: logo("postgresql", x + 6, y, 40), "Any pod with the ticket", "gets the same coat back")]
    for k, (ic, a, b) in enumerate(rows):
        y = 290 + k * 120
        out.append(card(rx, y, X1 - rx, 100, "normal"))
        out.append(ic(rx + 20, y + 30))
        out.append(text(rx + 92, y + 44, a, 21, 800, INK))
        out.append(text(rx + 92, y + 74, b, 18.5, 400, CAP))
        check_fit("cloak", b, 18.5, 400, X1 - rx - 104)
    out.append(text(rx, 682, "ReadWriteOnce: one node writes at a time,", 18, 400, CAP))
    out.append(text(rx, 708, "so the database runs as 1 pod (Recreate).", 18, 400, CAP))
    return out, ("Storage: the postgres pod shows the PersistentVolumeClaim postgres-data (5 GiB, ReadWriteOnce), which is bound "
                 "to a PersistentVolume, a Google Persistent Disk; when the pod is deleted the disk stays and the new pod gets the "
                 "same disk, like a cloakroom ticket for your coat.")


# ---------------------------------------------------------------------------
# 08 Ingress
# ---------------------------------------------------------------------------
def slide_08():
    out = [frame(9, "Ingress",
                 "One static IP on a Google load balancer, routing by path: the job nginx did in the Docker stages.")]
    out.append(browser_card(X0, 300, 290, 130, cap="game runs here · calls /api"))
    # the door
    gx, gy, gw, gh = 450, 232, 380, 268
    out.append(rect(gx - 8, gy - 8, gw + 16, gh + 16, R_CARD + 8, fill=ACCENT_HALO))
    out.append(card(gx, gy, gw, gh, "new"))
    out.append(logo("googlecloud", gx + 20, gy + 20, 36))
    out.append(text(gx + 68, gy + 40, "Google Cloud", 21, 800, INK))
    out.append(text(gx + 68, gy + 64, "load balancer", 21, 800, INK))
    out.append(rect(gx + 20, gy + 88, gw - 40, 46, R_CHIP, fill=SOFT))
    out.append(text(gx + 36, gy + 118, "static IP", 18, 400, CAP))
    out.append(cs.mono(gx + 36 + text_width("static IP ", 18, 400), gy + 118, "bugsquash-ip", 18, INK, weight=700))
    out.append(ic_door(gx + 26, gy + 156, 30, 46, INK))
    out.append(text(gx + 72, gy + 176, "the one public door", 20, 800, INK))
    out.append(text(gx + 72, gy + 200, "made from the Ingress bugsquash", 17, 400, CAP))
    out.append(logo("kubernetes", gx + 22, gy + 222, 26))
    out.append(text(gx + 56, gy + 241, "HTTPS: ManagedCertificate", 17, 700, TEXT))
    out.append(arrow([(X0 + 290, 365), (gx - 4, 365)], "normal"))
    out.append(label((X0 + 290 + gx) / 2, 352, "HTTPS", "normal", size=17))
    # two routes
    routes = [(266, "/api", "API calls from the browser", "backend", "backend:3000", "nodedotjs"),
              (440, "/", "the HTML, CSS and JS files", "frontend", "frontend:8080", "vite")]
    svc_x = 1060
    for y, path_, what, name, svc, slug in routes:
        out.append(arrow([(gx + gw, y + 36), (svc_x - 4, y + 36)], "new"))
        out.append(label((gx + gw + svc_x) / 2, y + 22, path_, "new", size=22))
        out.append(text((gx + gw + svc_x) / 2, y + 66, what, 17, 400, CAP, "middle"))
        out.append(obj(svc_x, y + 6, 210, "Service", svc, icon=k8s_ic))
        for k in range(3):
            out.append(pod(svc_x + 236 + k * 76, y + 14, 68, 44, slug, ""))
        out.append(text(svc_x + 236, y + 84, f"3 {name} pods", 17, 600, TEXT))
    # same job as before
    by = 600
    out.append(rect(X0, by, X1 - X0, 188, R_CARD, fill=WASH))
    out.append(text(X0 + 32, by + 46, "The same job you already know", 24, 800, INK))
    halves = [(X0 + 32, "nginx", "Docker stages", "the nginx proxy on :80 and :443", "certbot renews the certificate"),
              (820, "kubernetes", "Kubernetes on GKE", "an Ingress → a Google load balancer", "Google issues and renews it")]
    for x, slug, t, a, b in halves:
        out.append(logo(slug, x, by + 76, 40))
        out.append(text(x + 56, by + 96, t, 21, 800, INK))
        out.append(text(x + 56, by + 126, a, 19, 400, TEXT))
        out.append(text(x + 56, by + 154, b, 19, 400, CAP))
    return out, ("Ingress: the browser at k8s.gulfheight.com reaches a Google Cloud load balancer with the static IP bugsquash-ip, "
                 "created from the Ingress bugsquash, the one public door; /api, the API calls from the game in the browser, goes "
                 "to the Service backend:3000 and / (the files) to the Service frontend:8080; it does the job of the nginx proxy of "
                 "the Docker stages, and Google issues the HTTPS certificate.")


# ---------------------------------------------------------------------------
# 09 Rolling updates
# ---------------------------------------------------------------------------
def slide_09():
    out = [frame(10, "Rolling updates",
                 "New pods replace old ones one at a time, so visitors never notice the update.")]
    cols = [("start", "3 \u00d7 v1"), ("one swapped", "a v2 is ready, then a v1 stops"), ("two swapped", "the same again"),
            ("done", "3 \u00d7 v2")]
    states = [["v1", "v1", "v1"], ["v2", "v1", "v1"], ["v2", "v2", "v1"], ["v2", "v2", "v2"]]
    gap = 48
    cw = (X1 - X0 - 3 * gap) / 4
    for k, ((t, c), st) in enumerate(zip(cols, states)):
        x = X0 + k * (cw + gap)
        out.append(rect(x, 214, cw, 344, R_CARD, fill=WASH))
        out.append(text(x + 20, 248, f"{k + 1}. {t}", 21, 800, INK))
        out.append(text(x + 20, 274, c, 17, 400, CAP))
        for j, v in enumerate(st):
            out.append(pod(x + 20, 296 + j * 82, cw - 40, 64, "vite", "frontend", v + (" · sha-0902b98" if v == "v1" else " · sha-dcb0790"),
                           hl=v == "v2"))
        if k < 3:
            out.append(arrow([(x + cw + 6, 386), (x + cw + gap - 6, 386)], "normal"))
    # traffic keeps flowing
    ty = 600
    out.append(rail(X0, X1, ty, ACCENT, 8))
    for k in range(4):
        x = X0 + k * (cw + gap) + cw / 2
        out.append(stem(x, 558, ty - 4, LINE))
        out.append(cs.ok_badge(x, ty, 16))
    out.append(text(X0, ty + 44, "Traffic never stops: the Service only sends visitors to pods that are ready.", 20, 700, INK))
    out.append(text(X0, ty + 74, "The game's footer shows which commit is live, so you can watch it change.", 19, 400, CAP))
    # the two commands
    cy = 712
    a, aw = kubectl_chip(X0, cy, "kubectl set image deployment/frontend frontend=…:sha-dcb0790", 18)
    out.append(a)
    out.append(text(X0 + aw + 14, cy + 26, "update", 19, 700, TEXT))
    b, bw = kubectl_chip(X0 + aw + 110, cy, "kubectl rollout undo deployment/frontend", 18)
    out.append(b)
    out.append(text(X0 + aw + 110 + bw + 14, cy + 26, "v1 is back", 19, 700, TEXT))
    if X0 + aw + 110 + bw + 14 + text_width("v1 is back", 19, 700) > X1:
        FIT_PROBLEMS.append("rollout commands too wide")
    return out, ("Rolling updates: three v1 frontend pods (sha-0902b98) are replaced one at a time by v2 pods; a new pod must be "
                 "ready before an old one stops, so traffic keeps flowing; kubectl set image starts the update and kubectl rollout "
                 "undo deployment/frontend brings v1 back.")


# ---------------------------------------------------------------------------
# 10 High availability
# ---------------------------------------------------------------------------
def slide_10():
    out = [frame(11, "High availability",
                 "Copies live in 3 zones. Stop a node and the rest keep serving while Kubernetes moves its pods.")]
    out.append(lb_card(X0, 212, 520, 76, title="Google load balancer",
                       cap="sends visitors only to ready pods"))
    out.append(control_plane(X0 + 560, 212, X1 - X0 - 560, 76, parts=(),
                             sub="replicated by Google in all 3 zones: it survives a zone too"))
    zs, nodes = zones_row(X0, X1, 312, 380)
    out.append(zs)
    for i, (nx, ny, nw) in enumerate(nodes):
        stopped = i == 1
        out.append(group([node_card(nx, ny, nw, 320, "node", "stopped by the instructor" if stopped else "e2-medium", stopped)],
                         0.55 if stopped else None))
        pw = (nw - 44) / 2
        out.append(pod(nx + 16, ny + 56, pw, 56, "vite", "frontend", faded=stopped))
        out.append(pod(nx + 28 + pw, ny + 56, pw, 56, "nodedotjs", "backend", faded=stopped))
        if stopped:
            out.append(cs.bad_badge(nx + nw - 30, ny + 26, 20))
            out.append(text(nx + nw / 2, ny + 172, "its 2 pods are", 19, 700, GREY, "middle"))
            out.append(text(nx + nw / 2, ny + 198, "re-created elsewhere", 19, 700, GREY, "middle"))
            out.append(text(nx + nw / 2, ny + 224, "after about 30 s", 19, 700, ACCENT_TEXT, "middle"))
        else:
            out.append(pod(nx + 16 if i == 0 else nx + 28 + pw, ny + 130, pw, 56, "vite" if i == 0 else "nodedotjs",
                           "frontend" if i == 0 else "backend", "moved here", hl=True))
            if i == 0:
                out.append(pod(nx + 16, ny + 204, pw, 56, "postgresql", "postgres"))
                out.append(disk(nx + 28 + pw + 8, ny + 196, 46, 64))
                out.append(text(nx + 28 + pw + 66, ny + 224, "its disk", 17, 600, TEXT))
                out.append(text(nx + 28 + pw + 66, ny + 246, "zone a only", 16.5, 400, CAP))
    a = nodes[1]
    out.append(arrow([(a[0] + 20, a[1] + 150), (nodes[0][0] + nodes[0][2] - 8, a[1] + 150)], "new"))
    out.append(arrow([(a[0] + a[2] - 20, a[1] + 150), (nodes[2][0] + 8, a[1] + 150)], "new"))
    out.append(note(X0, 712, X1 - X0, 80, "Honest weak spot: one Postgres pod, one disk in zone a",
                    "Lose zone a and the API waits for it. Production uses Cloud SQL or a replicated database."))
    return out, ("High availability: pods are spread over zones a, b and c; when the instructor stops the node in zone b, the "
                 "load balancer keeps sending visitors to the ready pods in zones a and c, and after about 30 seconds Kubernetes "
                 "re-creates the two lost pods there; the control plane is replicated by Google; the weak spot is the single "
                 "Postgres pod with its disk in zone a.")


# ---------------------------------------------------------------------------
# 11 From Compose to Kubernetes
# ---------------------------------------------------------------------------
MAPPING = [("services: backend", "Deployment + Service"), ("proxy: (nginx) + ports:", "Service + Ingress"),
           ("volumes: pgdata", "PersistentVolumeClaim"), (".env.prod", "ConfigMap + Secret"),
           ("healthcheck:", "readiness + liveness probes"), ("restart: unless-stopped", "a self-healing Deployment"),
           ("deploy.resources.limits", "resources: requests + limits"), ("docker compose up -d", "kubectl apply -f manifests/")]


def slide_11():
    out = [frame(12, "From Compose to Kubernetes",
                 "Everything you know from docker-compose.prod.yml already has a Kubernetes name.")]
    lx, lw, rx, rw = X0, 600, 900, X1 - 900
    out.append(logo("docker", lx, 206, 34))
    out.append(text(lx + 46, 232, "docker-compose.prod.yml", 22, 800, INK))
    out.append(logo("kubernetes", rx, 206, 34))
    out.append(text(rx + 46, 232, "Kubernetes (kubernetes/manifests/)", 22, 800, INK))
    rh, gap = 54, 10
    for k, (a, b) in enumerate(MAPPING):
        y = 262 + k * (rh + gap)
        out.append(rect(lx, y, lw, rh, R_CHIP, fill=SOFT))
        out.append(cs.mono(lx + 20, y + 35, a, 19, INK, weight=700))
        if cs.mono_w(a, 19) > lw - 30:
            FIT_PROBLEMS.append("compose side too long: " + a)
        out.append(arrow([(lx + lw + 16, y + rh / 2), (rx - 16, y + rh / 2)], "new" if k == len(MAPPING) - 1 else "normal"))
        last = k == len(MAPPING) - 1
        out.append(rect(rx, y, rw, rh, R_CHIP, fill=ACCENT if last else WHITE, stroke=None if last else LINE, stroke_width=1.5))
        if b.startswith("kubectl"):
            out.append(cs.mono(rx + 20, y + 35, b, 19, WHITE, weight=700))
        else:
            out.append(text(rx + 20, y + 35, b, 21, 800, INK))
            check_fit("k8s side", b, 21, 800, rw - 30)
    return out, ("From Compose to Kubernetes: a Compose service becomes a Deployment plus a Service, ports and the nginx proxy "
                 "become a Service plus an Ingress, volumes become a PersistentVolumeClaim, .env.prod becomes a ConfigMap plus a "
                 "Secret, healthcheck becomes readiness and liveness probes, restart: unless-stopped becomes a self-healing "
                 "Deployment, deploy.resources.limits becomes resources requests and limits, and docker compose up -d becomes "
                 "kubectl apply -f.")


# ---------------------------------------------------------------------------
SLIDES = [
    ("k8s-00-what-we-build", "What we'll build", slide_00),
    ("k8s-01-why-kubernetes", "Why Kubernetes?", slide_01),
    ("k8s-02-brain-and-workers", "The cluster: brain and workers", slide_02),
    ("k8s-03-pods", "Pods", slide_03),
    ("k8s-04-deployments", "Deployments", slide_04),
    ("k8s-05-services", "Services", slide_05),
    ("k8s-06-configmaps-and-secrets", "ConfigMaps and Secrets", slide_06),
    ("k8s-07-storage", "Storage", slide_07),
    ("k8s-08-ingress", "Ingress", slide_08),
    ("k8s-09-rolling-updates", "Rolling updates", slide_09),
    ("k8s-10-high-availability", "High availability", slide_10),
    ("k8s-11-compose-to-kubernetes", "From Compose to Kubernetes", slide_11),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=OUT_DIR, help="output folder (default: kubernetes/images/slides)")
    args = ap.parse_args()
    load_logos()
    os.makedirs(args.out, exist_ok=True)
    status = 0
    for i, (name, title, fn) in enumerate(SLIDES):
        FIT_PROBLEMS.clear()
        body, desc = fn()
        svg = document(f"Introduction to Kubernetes, slide {i + 1} of {TOTAL}: {title}", desc, body, "build_k8s_slides.py")
        svg = svg.replace("docs/images/src/build_k8s_slides.py", GEN)
        target = os.path.join(args.out, name + ".svg")
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(svg)
        print(f"wrote {os.path.relpath(target)} ({len(svg.encode()) // 1024} KB)")
        for p in FIT_PROBLEMS:
            print("  warning: text may overflow ->", p)
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
