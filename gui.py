import sys
import json
import requests
import subprocess
import time
import webbrowser

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from manager import *

CONFIG_PATH = "config.json"


# ================= CONFIG =================
def load_config():
    default = {
        "mode": "📺 YOUTUBE",
        "background": "",
        "accent": "#6C5CE7",
        "games": []
    }
    try:
        with open(CONFIG_PATH, "r") as f:
            default.update(json.load(f))
    except:
        pass
    return default


def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=4)


# ================= WORKER =================
class Worker(QThread):
    data_ready = Signal(str, str, str, str)

    def run(self):
        try:
            res = subprocess.check_output("warp-cli status", shell=True).decode()
            status = "🟢 ONLINE" if "Connected" in res else "🔴 OFFLINE"
        except:
            status = "⚠️ ERROR"

        try:
            ip = requests.get("https://api.ipify.org", timeout=3).text
        except:
            ip = "error"

        try:
            start = time.time()
            requests.get("https://1.1.1.1", timeout=2)
            ping = str(int((time.time() - start) * 1000))
        except:
            ping = "error"

        try:
            start = time.time()
            requests.get("https://speed.cloudflare.com/__down?bytes=500000", timeout=5)
            speed = str(round((1 / (time.time() - start)) * 8, 1))
        except:
            speed = "error"

        self.data_ready.emit(status, ip, ping, speed)


# ================= BUTTON =================
class NiceButton(QPushButton):
    def __init__(self, text, parent):
        super().__init__(text)
        self.parent = parent
        self.setMinimumHeight(34)
        self.setCursor(Qt.PointingHandCursor)
        self.update_style()

    def update_style(self):
        accent = self.parent.cfg["accent"]
        self.setStyleSheet(f"""
        QPushButton {{
            background-color: #1A1A1A;
            color: white;
            border-radius: 8px;
            padding: 5px;
        }}
        QPushButton:hover {{
            background-color: {accent};
        }}
        """)


# ================= SETTINGS =================
class SettingsWindow(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.cfg = parent.cfg

        self.setWindowTitle("⚙️ Настройки")
        self.resize(480, 420)

        tabs = QTabWidget()

        # ===== UI =====
        tab_ui = QWidget()
        l1 = QVBoxLayout()

        btn_color = NiceButton("🎨 Цвет", parent)
        btn_color.clicked.connect(self.pick_color)

        btn_bg = NiceButton("🖼 Фон", parent)
        btn_bg.clicked.connect(self.select_bg)

        btn_clear = NiceButton("❌ Убрать фон", parent)
        btn_clear.clicked.connect(self.clear_bg)

        l1.addWidget(btn_color)
        l1.addWidget(btn_bg)
        l1.addWidget(btn_clear)
        l1.addStretch()

        tab_ui.setLayout(l1)

        # ===== CONNECTION =====
        tab_conn = QWidget()
        l2 = QVBoxLayout()

        self.mode_box = QComboBox()
        self.mode_box.addItems(["🧠 AUTO", "🎮 GAMING", "📺 YOUTUBE"])
        self.mode_box.setCurrentText(self.cfg.get("mode", "📺 YOUTUBE"))

        self.mode_box.currentTextChanged.connect(self.save_mode)

        info_btn = NiceButton("ℹ️ Что такое AUTO", parent)

        self.info_text = QLabel(
            "🧠 AUTO режим:\n"
            "- включает GAMING при запуске игры\n"
            "- иначе работает как YOUTUBE"
        )
        self.info_text.setWordWrap(True)
        self.info_text.hide()

        info_btn.clicked.connect(
            lambda: self.info_text.setVisible(not self.info_text.isVisible())
        )

        self.games = QListWidget()
        self.games.addItems(self.cfg["games"])

        btn_add = NiceButton("➕ Добавить игру", parent)
        btn_add.clicked.connect(self.add_game)

        l2.addWidget(self.mode_box)
        l2.addWidget(info_btn)
        l2.addWidget(self.info_text)
        l2.addWidget(self.games)
        l2.addWidget(btn_add)

        tab_conn.setLayout(l2)

        tabs.addTab(tab_ui, "Интерфейс")
        tabs.addTab(tab_conn, "Подключение")

        layout = QVBoxLayout()
        layout.addWidget(tabs)
        self.setLayout(layout)

    def save_mode(self, text):
        self.cfg["mode"] = text
        save_config(self.cfg)

    def pick_color(self):
        c = QColorDialog.getColor()
        if c.isValid():
            self.cfg["accent"] = c.name()
            save_config(self.cfg)
            self.parent.refresh_ui()

    def select_bg(self):
        path, _ = QFileDialog.getOpenFileName(filter="Images (*.png *.jpg)")
        if path:
            self.cfg["background"] = path
            save_config(self.cfg)
            self.parent.apply_bg()

    def clear_bg(self):
        self.cfg["background"] = ""
        save_config(self.cfg)
        self.parent.apply_bg()

    def add_game(self):
        path, _ = QFileDialog.getOpenFileName(filter="Exe (*.exe)")
        if path:
            self.cfg["games"].append(path)
            save_config(self.cfg)
            self.games.addItem(path)


# ================= MAIN =================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.cfg = load_config()

        self.setWindowTitle("SKIPFLUX")
        self.resize(400, 460)

        self.init_ui()
        self.apply_bg()
        self.refresh_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.start_worker)
        self.timer.start(3000)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(4)

        self.status = QLabel("🔴 OFFLINE")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("font-size:18px; font-weight:bold;")

        self.ip = QLabel("🌐 ...")
        self.ping = QLabel("📶 ...")
        self.speed = QLabel("🚀 ...")

        for w in [self.ip, self.ping, self.speed]:
            w.setAlignment(Qt.AlignCenter)

        self.proxy = QLabel("🔗 Proxy: OFF")
        self.proxy.setAlignment(Qt.AlignCenter)

        self.btn_on = NiceButton("🚀 ВКЛ", self)
        self.btn_off = NiceButton("⛔ ВЫКЛ", self)
        self.btn_settings = NiceButton("⚙️", self)

        self.btn_on.clicked.connect(self.connect_all)
        self.btn_off.clicked.connect(self.disconnect_all)
        self.btn_settings.clicked.connect(self.open_settings)

        row = QHBoxLayout()
        row.addWidget(self.btn_on)
        row.addWidget(self.btn_off)
        row.addWidget(self.btn_settings)

        layout.addWidget(self.status)
        layout.addWidget(self.ip)
        layout.addWidget(self.ping)
        layout.addWidget(self.speed)
        layout.addWidget(self.proxy)
        layout.addLayout(row)

        w = QWidget()
        w.setLayout(layout)
        self.setCentralWidget(w)

    def refresh_ui(self):
        for b in [self.btn_on, self.btn_off, self.btn_settings]:
            b.update_style()

    def apply_bg(self):
        if self.cfg["background"]:
            self.setStyleSheet(f"""
            QMainWindow {{
                background-image: url("{self.cfg['background']}");
                background-position: center;
            }}
            QLabel {{ color:white; }}
            """)
        else:
            self.setStyleSheet("""
            QMainWindow {{ background:#0D0D0D; }}
            QLabel {{ color:white; }}
            """)

    def open_settings(self):
        SettingsWindow(self).exec()

    def connect_all(self):
        # 1. zapret
        start_zapret()

        # 2. proxy ВСЕГДА
        start_proxy()
        self.proxy.setText("🔗 Proxy: ON")

        # 3. режим
        mode = self.cfg.get("mode", "")

        if "GAMING" in mode or "AUTO" in mode:
            start_warp()
        else:
            stop_warp()

    def disconnect_all(self):
        stop_proxy()
        stop_warp()
        stop_zapret()

        self.proxy.setText("🔗 Proxy: OFF")

    def start_worker(self):
        self.worker = Worker()
        self.worker.data_ready.connect(self.update_ui)
        self.worker.start()

    def update_ui(self, status, ip, ping, speed):
        self.status.setText(status)
        self.ip.setText(f"🌐 {ip}")
        self.ping.setText(f"📶 {ping} ms")
        self.speed.setText(f"🚀 {speed} Mbps")


def run_app():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())