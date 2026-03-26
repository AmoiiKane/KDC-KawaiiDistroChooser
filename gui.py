#!/usr/bin/env python3
# KDC - Kawaii Distro Chooser
# gui.py — PyQt6 kawaii GUI with neko catgirls, animations, rainbow sweep

import sys
import json
import math
import subprocess
import threading
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGraphicsOpacityEffect, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QThread, pyqtSignal, QRect, QPoint, QSize
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QLinearGradient, QRadialGradient,
    QPen, QBrush, QPainterPath, QFontDatabase, QPixmap
)
import urllib.request
import os

# ─── Worker thread: runs bash + python scraper ───────────────────────────────

class ScanWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def run(self):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            bash_script = os.path.join(script_dir, "detect_specs.sh")
            scraper_script = os.path.join(script_dir, "scraper.py")

            # Run bash detector
            bash_result = subprocess.run(
                ["bash", bash_script],
                capture_output=True, text=True, timeout=15
            )
            specs_json = bash_result.stdout.strip()
            if not specs_json:
                specs_json = '{"ram_mb":4096,"cpu_cores":4,"cpu_gen":"modern","gpu_vendor":"unknown","disk_gb":50,"cpu_model":"Unknown","bios_type":"uefi","current_os":"Unknown"}'

            # Run scraper
            scraper_result = subprocess.run(
                [sys.executable, scraper_script],
                input=specs_json, capture_output=True, text=True, timeout=30
            )
            result = json.loads(scraper_result.stdout.strip())
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

# ─── Worker thread: loads distro logo from URL ────────────────────────────────

class LogoLoader(QThread):
    finished = pyqtSignal(bytes)

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.url = url

    def run(self):
        try:
            req = urllib.request.Request(
                self.url, headers={"User-Agent": "Mozilla/5.0"}
            )
            data = urllib.request.urlopen(req, timeout=5).read()
            self.finished.emit(data)
        except Exception:
            self.finished.emit(b"")


class ImageBackground(QWidget):
    """Full-window image background with animated particle sparkles overlay."""
    def __init__(self, parent=None):
        super().__init__(parent)
        import random
        self._pixmap = None
        self._overlay_alpha = 120  # darkness overlay
        self.particles = [
            (random.randint(0, 900), random.randint(0, 650), random.random(), random.random())
            for _ in range(60)
        ]
        self.t = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(50)

    def set_image(self, path: str, overlay_alpha: int = 120):
        px = QPixmap(path)
        if not px.isNull():
            self._pixmap = px
        self._overlay_alpha = overlay_alpha
        self.update()

    def _tick(self):
        self.t += 0.04
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Draw image scaled to fill
        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(w, h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation)
            # Center crop
            ox = (scaled.width() - w) // 2
            oy = (scaled.height() - h) // 2
            painter.drawPixmap(0, 0, scaled, ox, oy, w, h)
        else:
            grad = QLinearGradient(0, 0, 0, h)
            grad.setColorAt(0, QColor("#0d001a"))
            grad.setColorAt(1, QColor("#1a0033"))
            painter.fillRect(self.rect(), grad)

        # Dark overlay for readability
        painter.fillRect(self.rect(), QColor(0, 0, 0, self._overlay_alpha))

        # Floating sparkle particles
        for x, y, phase, speed in self.particles:
            alpha = int(80 + 120 * abs(math.sin(self.t * speed + phase * 6.28)))
            hue = int((self.t * 20 + phase * 360)) % 360
            color = QColor.fromHsv(hue, 180, 255, alpha)
            size = 2 + 3 * abs(math.sin(self.t + phase))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(
                int(x + 30 * math.sin(self.t * speed + phase)),
                int(y + 20 * math.cos(self.t * speed * 0.7 + phase)),
                int(size), int(size)
            )

        painter.end()

class RainbowSweep(QWidget):
    """Overlay that sweeps rainbow from left to right."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0.0  # 0.0 to 1.0
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def set_progress(self, v):
        self.progress = v
        self.update()

    def paintEvent(self, event):
        if self.progress <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        sweep_x = int(w * self.progress)

        # Rainbow gradient covering swept area
        grad = QLinearGradient(0, 0, sweep_x, 0)
        colors = [
            (0.0,  QColor(255, 0,   120, 180)),
            (0.17, QColor(255, 100, 0,   180)),
            (0.33, QColor(255, 220, 0,   180)),
            (0.5,  QColor(0,   220, 80,  180)),
            (0.67, QColor(0,   180, 255, 180)),
            (0.83, QColor(120, 0,   255, 180)),
            (1.0,  QColor(255, 0,   180, 180)),
        ]
        for pos, color in colors:
            grad.setColorAt(pos, color)
        painter.fillRect(0, 0, sweep_x, h, grad)

        # Bright leading edge
        edge_grad = QLinearGradient(max(0, sweep_x - 40), 0, sweep_x, 0)
        edge_grad.setColorAt(0, QColor(255, 255, 255, 0))
        edge_grad.setColorAt(1, QColor(255, 255, 255, 220))
        painter.fillRect(max(0, sweep_x - 40), 0, 40, h, edge_grad)
        painter.end()

# ─── Catgirl painter ─────────────────────────────────────────────────────────

class CatgirlWidget(QWidget):
    """Draws a cute chibi catgirl using QPainter."""
    def __init__(self, flip=False, parent=None):
        super().__init__(parent)
        self.flip = flip
        self.frame = 0
        self.setMinimumSize(120, 180)
        self.setMaximumSize(140, 200)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(80)

    def _tick(self):
        self.frame = (self.frame + 1) % 20
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        if self.flip:
            painter.translate(w, 0)
            painter.scale(-1, 1)

        # Dance bounce
        bounce = int(8 * math.sin(self.frame * math.pi / 10))
        arm_angle = 30 * math.sin(self.frame * math.pi / 10)
        leg_swing = 15 * math.sin(self.frame * math.pi / 10)

        cx = w // 2
        base_y = h - 20 + bounce

        skin = QColor("#FFD6C0")
        hair = QColor("#FF69B4")
        outfit = QColor("#FF85C2")
        accent = QColor("#FF1493")
        eye_c = QColor("#9B59B6")
        white = QColor("#FFFFFF")
        black = QColor("#222222")

        # ── Legs ──
        painter.setPen(QPen(black, 2))
        painter.setBrush(QBrush(QColor("#CC88AA")))
        # left leg
        painter.save()
        painter.translate(cx - 10, base_y - 30)
        painter.rotate(leg_swing)
        painter.drawRoundedRect(-6, 0, 12, 35, 4, 4)
        painter.restore()
        # right leg
        painter.save()
        painter.translate(cx + 10, base_y - 30)
        painter.rotate(-leg_swing)
        painter.drawRoundedRect(-6, 0, 12, 35, 4, 4)
        painter.restore()

        # ── Skirt ──
        painter.setBrush(QBrush(accent))
        path = QPainterPath()
        path.moveTo(cx - 22, base_y - 55)
        path.lineTo(cx - 28, base_y - 30)
        path.lineTo(cx + 28, base_y - 30)
        path.lineTo(cx + 22, base_y - 55)
        path.closeSubpath()
        painter.drawPath(path)

        # ── Body ──
        painter.setBrush(QBrush(outfit))
        painter.drawRoundedRect(cx - 18, base_y - 90, 36, 40, 8, 8)

        # ── Arms ──
        painter.setBrush(QBrush(skin))
        # left arm
        painter.save()
        painter.translate(cx - 18, base_y - 82)
        painter.rotate(-arm_angle - 20)
        painter.drawRoundedRect(-5, 0, 10, 28, 4, 4)
        painter.restore()
        # right arm
        painter.save()
        painter.translate(cx + 18, base_y - 82)
        painter.rotate(arm_angle + 20)
        painter.drawRoundedRect(-5, 0, 10, 28, 4, 4)
        painter.restore()

        # ── Head ──
        head_y = base_y - 130
        painter.setBrush(QBrush(skin))
        painter.drawEllipse(cx - 22, head_y, 44, 44)

        # ── Hair ──
        painter.setBrush(QBrush(hair))
        painter.drawEllipse(cx - 24, head_y - 8, 48, 30)
        # Side hair
        painter.drawEllipse(cx - 26, head_y + 5, 14, 28)
        painter.drawEllipse(cx + 12, head_y + 5, 14, 28)

        # ── Cat ears ──
        painter.setBrush(QBrush(hair))
        # left ear
        left_ear = QPainterPath()
        left_ear.moveTo(cx - 18, head_y)
        left_ear.lineTo(cx - 28, head_y - 20)
        left_ear.lineTo(cx - 8, head_y - 6)
        left_ear.closeSubpath()
        painter.drawPath(left_ear)
        # right ear
        right_ear = QPainterPath()
        right_ear.moveTo(cx + 18, head_y)
        right_ear.lineTo(cx + 28, head_y - 20)
        right_ear.lineTo(cx + 8, head_y - 6)
        right_ear.closeSubpath()
        painter.drawPath(right_ear)
        # inner ears
        painter.setBrush(QBrush(QColor("#FFB6C1")))
        il = QPainterPath()
        il.moveTo(cx - 18, head_y - 2)
        il.lineTo(cx - 25, head_y - 15)
        il.lineTo(cx - 10, head_y - 5)
        il.closeSubpath()
        painter.drawPath(il)
        ir = QPainterPath()
        ir.moveTo(cx + 18, head_y - 2)
        ir.lineTo(cx + 25, head_y - 15)
        ir.lineTo(cx + 10, head_y - 5)
        ir.closeSubpath()
        painter.drawPath(ir)

        # ── Eyes ──
        # whites
        painter.setBrush(QBrush(white))
        painter.drawEllipse(cx - 14, head_y + 14, 11, 13)
        painter.drawEllipse(cx + 3,  head_y + 14, 11, 13)
        # pupils
        painter.setBrush(QBrush(eye_c))
        painter.drawEllipse(cx - 11, head_y + 16, 7, 9)
        painter.drawEllipse(cx + 6,  head_y + 16, 7, 9)
        # shine
        painter.setBrush(QBrush(white))
        painter.drawEllipse(cx - 9,  head_y + 17, 3, 3)
        painter.drawEllipse(cx + 8,  head_y + 17, 3, 3)

        # ── Blush ──
        painter.setBrush(QBrush(QColor(255, 150, 150, 100)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cx - 18, head_y + 26, 10, 6)
        painter.drawEllipse(cx + 8,  head_y + 26, 10, 6)

        # ── Mouth ──
        painter.setPen(QPen(QColor("#CC5577"), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(cx - 5, head_y + 30, 10, 7, 0, -180 * 16)

        # ── Cat tail ──
        painter.setPen(QPen(hair, 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        tail_wave = int(12 * math.sin(self.frame * math.pi / 8))
        tail_path = QPainterPath()
        tail_path.moveTo(cx + 15, base_y - 45)
        tail_path.cubicTo(cx + 40, base_y - 60 + tail_wave,
                          cx + 50, base_y - 30 + tail_wave,
                          cx + 35, base_y - 10)
        painter.drawPath(tail_path)

        # ── Sparkles ──
        if self.frame % 5 == 0:
            import random
            painter.setPen(QPen(QColor("#FFFF00"), 2))
            for _ in range(3):
                sx = random.randint(cx - 40, cx + 40)
                sy = random.randint(head_y - 20, head_y + 10)
                painter.drawLine(sx - 4, sy, sx + 4, sy)
                painter.drawLine(sx, sy - 4, sx, sy + 4)

        painter.end()

# ─── Loading widget ───────────────────────────────────────────────────────────

class LoadingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.dots = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(40)

    def _tick(self):
        self.angle = (self.angle + 8) % 360
        self.dots = (self.dots + 1) % 30
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2

        # Spinning rainbow ring
        for i in range(12):
            angle = self.angle + i * 30
            rad = math.radians(angle)
            x = cx + int(55 * math.cos(rad)) - 7
            y = cy + int(55 * math.sin(rad)) - 7
            hue = (i * 30 + self.angle) % 360
            alpha = 80 + int(170 * (i / 12))
            color = QColor.fromHsv(hue, 220, 255, alpha)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            size = 6 + int(8 * (i / 12))
            painter.drawEllipse(x, y, size, size)

        # Center paw print
        painter.setBrush(QBrush(QColor("#FF69B4")))
        painter.drawEllipse(cx - 12, cy - 12, 24, 24)
        painter.setBrush(QBrush(QColor("#FF1493")))
        for ox, oy in [(-8,-14),(0,-16),(8,-14)]:
            painter.drawEllipse(cx + ox - 4, cy + oy - 4, 8, 8)

        # Loading text
        dots_str = "." * (1 + self.dots // 10)
        painter.setPen(QPen(QColor("#FF85C2")))
        font = QFont("Arial", 13, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(QRect(0, cy + 75, w, 30), Qt.AlignmentFlag.AlignCenter,
                         f"Scanning your kawaii machine{dots_str}")
        painter.end()

# ─── Main Window ─────────────────────────────────────────────────────────────

class KDCWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("✿ KDC - Kawaii Distro Chooser ✿")
        self.setFixedSize(900, 650)
        self.setStyleSheet("background: transparent;")

        self.central = QWidget(self)
        self.setCentralWidget(self.central)
        self.central.setGeometry(0, 0, 900, 650)

        # Image background (swappable per screen)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self._bg_start   = os.path.join(script_dir, 'bg_start.jpg')
        self._bg_loading = os.path.join(script_dir, 'bg_loading.jpg')
        self._bg_result  = os.path.join(script_dir, 'bg_start.jpg')

        self.bg = ImageBackground(self.central)
        self.bg.setGeometry(0, 0, 900, 650)
        self.bg.set_image(self._bg_start, overlay_alpha=100)

        # Rainbow sweep overlay
        self.rainbow = RainbowSweep(self.central)
        self.rainbow.setGeometry(0, 0, 900, 650)
        self.rainbow.hide()

        # ── Screen 1: Start ──
        self.screen1 = QWidget(self.central)
        self.screen1.setGeometry(0, 0, 900, 650)
        self.screen1.setStyleSheet("background: transparent;")
        self._build_screen1()

        # ── Screen 2: Loading ──
        self.screen2 = QWidget(self.central)
        self.screen2.setGeometry(0, 0, 900, 650)
        self.screen2.setStyleSheet("background: transparent;")
        self._build_screen2()
        self.screen2.hide()

        # ── Screen 3: Result ──
        self.screen3 = QWidget(self.central)
        self.screen3.setGeometry(0, 0, 900, 650)
        self.screen3.setStyleSheet("background: transparent;")
        self._build_screen3()
        self.screen3.hide()

        self.worker = None
        self.sweep_value = 0.0

    # ── Screen 1 ─────────────────────────────────────────────────────────────

    def _build_screen1(self):
        layout = QVBoxLayout(self.screen1)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # Title
        title = QLabel("✿ KDC ✿")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: #FF69B4;
            font-size: 52px;
            font-weight: 900;
            font-family: 'Arial Black', Arial;
            letter-spacing: 6px;
            text-shadow: 0 0 20px #FF1493;
        """)

        subtitle = QLabel("Kawaii Distro Chooser")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            color: #DDA0DD;
            font-size: 18px;
            font-family: Arial;
            letter-spacing: 3px;
        """)

        tagline = QLabel("(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧  Let me find your perfect Linux distro~  ✧ﾟ･: *ヽ(◕ヮ◕ヽ)")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setStyleSheet("color: #FFB6C1; font-size: 13px; font-family: Arial;")

        # Big kawaii button
        btn = QPushButton("✿ SCAN MY MACHINE ✿")
        btn.setFixedSize(300, 70)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #FF1493, stop:0.5 #FF69B4, stop:1 #DA70D6);
                color: white;
                border-radius: 35px;
                font-size: 16px;
                font-weight: 900;
                font-family: Arial;
                letter-spacing: 2px;
                border: 3px solid #FFB6C1;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #FF69B4, stop:0.5 #FFB6C1, stop:1 #FF1493);
                border: 3px solid white;
            }
            QPushButton:pressed {
                background: #CC0077;
            }
        """)
        btn.clicked.connect(self._start_scan)

        note = QLabel("uwu scanning your CPU, RAM, GPU & disk~")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setStyleSheet("color: #9B59B6; font-size: 11px; font-family: Arial;")

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)
        layout.addWidget(tagline)
        layout.addSpacing(30)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(note)
        layout.addStretch()

    # ── Screen 2 ─────────────────────────────────────────────────────────────

    def _build_screen2(self):
        layout = QVBoxLayout(self.screen2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.loading_widget = LoadingWidget()
        self.loading_widget.setFixedSize(300, 220)

        status = QLabel("Consulting the neko oracle...")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status.setStyleSheet("color: #DDA0DD; font-size: 14px; font-family: Arial;")

        layout.addStretch()
        layout.addWidget(self.loading_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(status)
        layout.addStretch()

    # ── Screen 3 ─────────────────────────────────────────────────────────────

    def _build_screen3(self):
        self.s3_layout = QVBoxLayout(self.screen3)
        self.s3_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.s3_layout.setSpacing(0)

        # Distro logo placeholder
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setFixedHeight(90)

        # Big announcement text
        self.announce_label = QLabel("STOP USING UR OS\nCHANGE TO ???")
        self.announce_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.announce_label.setWordWrap(True)
        self.announce_label.setStyleSheet("""
            color: white;
            font-size: 38px;
            font-weight: 900;
            font-family: 'Arial Black', Arial;
            letter-spacing: 2px;
            text-shadow: 0 0 30px #FF69B4, 0 0 60px #FF1493;
        """)

        # Runner ups
        self.runnerup_label = QLabel("")
        self.runnerup_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.runnerup_label.setStyleSheet("color: #DDA0DD; font-size: 13px; font-family: Arial;")

        # Catgirls row
        catgirl_row = QHBoxLayout()
        catgirl_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.catgirl1 = CatgirlWidget(flip=False)
        self.catgirl2 = CatgirlWidget(flip=True)
        catgirl_row.addWidget(self.catgirl1)
        catgirl_row.addSpacing(60)
        catgirl_row.addWidget(self.catgirl2)

        catgirl_container = QWidget()
        catgirl_container.setLayout(catgirl_row)
        catgirl_container.setStyleSheet("background: transparent;")
        catgirl_container.setFixedHeight(220)

        # Restart button
        restart_btn = QPushButton("✿ Scan Again ✿")
        restart_btn.setFixedSize(180, 44)
        restart_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        restart_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,105,180,0.3);
                color: #FFB6C1;
                border-radius: 22px;
                font-size: 13px;
                font-weight: bold;
                border: 2px solid #FF69B4;
            }
            QPushButton:hover { background: rgba(255,105,180,0.6); }
        """)
        restart_btn.clicked.connect(self._restart)

        self.s3_layout.addSpacing(18)
        self.s3_layout.addWidget(self.logo_label)
        self.s3_layout.addSpacing(10)
        self.s3_layout.addWidget(self.announce_label)
        self.s3_layout.addSpacing(8)
        self.s3_layout.addWidget(self.runnerup_label)
        self.s3_layout.addSpacing(0)
        self.s3_layout.addWidget(catgirl_container)
        self.s3_layout.addWidget(restart_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.s3_layout.addSpacing(12)

    # ── Transitions ──────────────────────────────────────────────────────────

    def _start_scan(self):
        self.bg.set_image(self._bg_loading, overlay_alpha=130)
        self.screen1.hide()
        self.screen2.show()
        self.worker = ScanWorker()
        self.worker.finished.connect(self._on_scan_done)
        self.worker.error.connect(self._on_scan_error)
        self.worker.start()

    def _on_scan_done(self, result):
        self._result = result
        self._load_logo(result.get("logo_url", ""))
        self._do_rainbow_sweep(result)

    def _on_scan_error(self, msg):
        # Fallback result
        fallback = {
            "recommended": "Ubuntu",
            "logo_url": "",
            "runner_ups": ["Fedora", "Linux Mint", "Manjaro"]
        }
        self._on_scan_done(fallback)

    def _load_logo(self, url):
        if not url:
            self._set_logo_fallback()
            return
        self._logo_loader = LogoLoader(url)
        self._logo_loader.finished.connect(self._on_logo_loaded)
        self._logo_loader.start()

    def _on_logo_loaded(self, data: bytes):
        if data:
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                self.logo_label.setPixmap(pixmap)
                return
        self._set_logo_fallback()

    def _set_logo_fallback(self):
        self.logo_label.setText("🐧")
        self.logo_label.setStyleSheet("font-size: 64px;")

    def _do_rainbow_sweep(self, result):
        self.screen2.hide()
        self.rainbow.show()
        self.rainbow.raise_()
        self._sweep_result = result
        self._sweep_v = 0.0

        self._sweep_timer = QTimer(self)
        self._sweep_timer.timeout.connect(self._sweep_tick)
        self._sweep_timer.start(16)

    def _sweep_tick(self):
        self._sweep_v += 0.035
        self.rainbow.set_progress(self._sweep_v)
        if self._sweep_v >= 1.0:
            self._sweep_timer.stop()
            self._show_result(self._sweep_result)

    def _show_result(self, result):
        distro = result.get("recommended", "Ubuntu")
        runner_ups = result.get("runner_ups", [])

        self.announce_label.setText(f"STOP USING UR OS\nCHANGE TO {distro.upper()}!")
        if runner_ups:
            self.runnerup_label.setText(f"Also consider: {' · '.join(runner_ups)}")

        # Switch to result background image
        self.bg.set_image(self._bg_result, overlay_alpha=155)
        self.screen3.setStyleSheet("background: transparent;")

        self.screen3.show()
        self.screen3.raise_()

        # Fade rainbow out
        QTimer.singleShot(400, lambda: self.rainbow.hide())

    def _restart(self):
        self.screen3.hide()
        self.rainbow.hide()
        self.bg.set_image(self._bg_start, overlay_alpha=100)
        self.screen1.show()

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = KDCWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
