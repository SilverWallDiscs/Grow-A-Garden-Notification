import sys
import asyncio
import json
import threading
import websockets
from datetime import datetime, timedelta, timezone
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QHBoxLayout, QPushButton, QSpacerItem, QSizePolicy, 
    QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import QTimer, Qt, QPoint
from PyQt6.QtGui import QColor, QMouseEvent, QPainter, QIcon, QAction, QPixmap
from win10toast import ToastNotifier
import winsound
import os

WS_URL = "wss://ws.growagardenpro.com"

QUALITY_COLORS = {
    "Common": QColor(150, 150, 150),
    "Uncommon": QColor(50, 200, 50),
    "Rare": QColor(100, 150, 255),
    "Legendary": QColor(255, 215, 0),
    "Mythical": QColor(180, 70, 255),
    "Divine": QColor(255, 150, 50),
    "Prismatic": QColor(200, 240, 255),
    "Transcendant": QColor(255, 50, 50)
}

ITEM_QUALITIES = {
    # Common
    "Carrot": "Common",
    "Strawberry": "Common",
    # Uncommon
    "Blueberry": "Uncommon",
    "Rose": "Uncommon",
    "Orange Tulip": "Uncommon",
    "Stonebite": "Uncommon",
    # Rare
    "Tomato": "Rare",
    "Daffodil": "Rare",
    "Cauliflower": "Rare",
    "Raspberry": "Rare",
    "Foxglove": "Rare",
    "Peace Lily": "Rare",
    "Corn": "Rare",
    "Paradise Petal": "Rare",
    # Legendary
    "Watermelon": "Legendary",
    "Pumpkin": "Legendary",
    "Avocado": "Legendary",
    "Green Apple": "Legendary",
    "Apple": "Legendary",
    "Banana": "Legendary",
    "Lilac": "Legendary",
    "Aloe Vera": "Legendary",
    "Bamboo": "Legendary",
    "Rafflesia": "Legendary",
    "Horned Dinoshroom": "Legendary",
    "Boneboo": "Legendary",
    # Mythical
    "Peach": "Mythical",
    "Pineapple": "Mythical",
    "Guanabana": "Mythical",
    "Coconut": "Mythical",
    "Cactus": "Mythical",
    "Dragon Fruit": "Mythical",
    "Mango": "Mythical",
    "Kiwi": "Mythical",
    "Bell Pepper": "Mythical",
    "Prickly Pear": "Mythical",
    "Pink Lily": "Mythical",
    "Purple Dahlia": "Mythical",
    "Firefly Fern": "Mythical",
    # Divine
    "Grape": "Divine",
    "Loquat": "Divine",
    "Mushroom": "Divine",
    "Pepper": "Divine",
    "Cacao": "Divine",
    "Feijoa": "Divine",
    "Pitcher Plant": "Divine",
    "Sunflower": "Divine",
    "Fossilight": "Divine",
    # Prismatic
    "Beanstalk": "Prismatic",
    "Ember Lily": "Prismatic",
    "Sugar Apple": "Prismatic",
    "Burning Bud": "Prismatic",
    # Transcendant
    "Bone Blossom": "Transcendant"
}

class StoreApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grow A Garden By: SilverWallDisc")
        self.setGeometry(100, 100, 700, 500)
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.dragging = False
        self.offset = QPoint()
        
        self.update_interval = timedelta(minutes=5, seconds=3)
        self.last_update_time = None
        self.next_update_time = None
        
        self.ws_connected = False
        self.ws = None
        self.ws_thread = None
        self.loop = None
        
        self.toaster = ToastNotifier()
        
        # Configurar el system tray
        self.tray_icon = QSystemTrayIcon(self)
        self.create_tray_icon()
        
        self.init_ui()
        
        self.store_data = []
        self._lock = threading.Lock()

        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)

        self.start_websocket()

    def create_tray_icon(self):
        """Crea y configura el icono de la bandeja del sistema"""
        # Crear un icono temporal si no existe
        if not os.path.exists("icon.ico"):
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor(60, 60, 60))
            painter = QPainter(pixmap)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "GG")
            painter.end()
            pixmap.save("icon.ico")
        
        self.tray_icon.setIcon(QIcon("icon.ico"))
        self.tray_icon.setToolTip("Grow A Garden Monitor")
        
        # Crear menú para el system tray
        tray_menu = QMenu()
        show_action = QAction("Mostrar", self)
        show_action.triggered.connect(self.show_normal)
        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close_app)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)
        
        # Conectar eventos del system tray
        self.tray_icon.activated.connect(self.tray_icon_clicked)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Barra de título
        title_bar = QWidget()
        title_bar.setStyleSheet("""
            background-color: #1E1E1E;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        """)
        title_bar.setFixedHeight(30)

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 5, 0)

        self.title_label = QLabel("Grow A Garden By: SilverWallDisc")
        self.title_label.setStyleSheet("color: white; font-size: 12px;")
        title_layout.addWidget(self.title_label)

        title_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.minimize_button = QPushButton("─")
        self.minimize_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 14px;
                padding: 0 8px;
            }
            QPushButton:hover {
                background-color: #333;
                border-radius: 3px;
            }
        """)
        self.minimize_button.setFixedSize(20, 20)
        self.minimize_button.clicked.connect(self.minimize_to_tray)
        title_layout.addWidget(self.minimize_button)
        
        self.close_button = QPushButton("✕")
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 12px;
                padding: 0 8px;
            }
            QPushButton:hover {
                background-color: #E81123;
                border-radius: 3px;
            }
        """)
        self.close_button.setFixedSize(20, 20)
        self.close_button.clicked.connect(self.close_app)
        title_layout.addWidget(self.close_button)
        
        main_layout.addWidget(title_bar)
        
        # Contenido principal
        content = QWidget()
        content.setStyleSheet("""
            background-color: rgba(60, 60, 60, 220); 
            border-radius: 0 0 5px 5px;
        """)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        self.label = QLabel("Cargando el websocket...")
        self.label.setStyleSheet("""
            color: #DDD; font-weight: bold; font-size: 14px;
            padding-bottom: 5px; background-color: rgba(40, 40, 40, 220);
        """)
        content_layout.addWidget(self.label)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Categoría", "Artículo", "Calidad", "Stock"])
        self.set_table_style()
        content_layout.addWidget(self.table)
        
        main_layout.addWidget(content)

    def minimize_to_tray(self):
        self.hide()
        self.tray_icon.show()
    def show_normal(self):
        """Restaura la ventana desde la bandeja del sistema"""
        self.show()
        self.tray_icon.hide()
        self.activateWindow()
        self.raise_()

    def tray_icon_clicked(self, reason):
        """Maneja los clics en el icono del system tray"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_normal()

    def close_app(self):
        """Cierra completamente la aplicación"""
        self.tray_icon.hide()
        if self.ws_connected and self.ws:
            asyncio.run_coroutine_threadsafe(self.ws.close(), self.loop)
        if self.loop and self.loop.is_running():
            self.loop.stop()
        QApplication.quit()

    def set_table_style(self):
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(40, 40, 40, 220);
                color: white; border: 1px solid #333;
                gridline-color: #2D2D2D;
                alternate-background-color: rgba(50, 50, 50, 220);
            }
            QHeaderView::section {
                background-color: rgba(60, 60, 60, 220);
                color: white; padding: 5px;
                border: 1px solid #444; font-weight: bold;
            }
            QTableWidget::item { background-color: rgba(40, 40, 40, 220); }
            QTableWidget::item:selected { background-color: rgba(85, 85, 85, 200); }
        """)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(60, 60, 60, 220))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())

    def get_item_quality(self, item_name):
        return ITEM_QUALITIES.get(item_name, None)

    def start_websocket(self):
        if self.ws_thread and self.ws_thread.is_alive():
            return

        self.loop = asyncio.new_event_loop()
        self.ws_thread = threading.Thread(
            target=self.run_websocket_loop,
            args=(self.loop,),
            daemon=True
        )
        self.ws_thread.start()

    def run_websocket_loop(self, loop):
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.websocket_listener())

    async def websocket_listener(self):
        try:
            async with websockets.connect(WS_URL, ping_interval=None) as ws:
                self.ws = ws
                self.ws_connected = True
                self.label.setText("Conectado. Obteniendo datos...")

                await self.request_update()

                async for message in ws:
                    try:
                        data = json.loads(message)
                        if "data" in data:
                            self.process_websocket_data(data["data"])
                    except Exception as e:
                        print(f"Error procesando mensaje: {e}")
        except Exception as e:
            print(f"Error en conexión WebSocket: {e}")
            self.ws_connected = False
            self.label.setText("Error de conexión. Reconectando...")
            QTimer.singleShot(5000, self.start_websocket)

    async def request_update(self):
        if self.ws_connected and self.ws:
            try:
                await self.ws.send(json.dumps({"action": "get_store_data"}))
            except Exception as e:
                print(f"Error solicitando actualización: {e}")
                self.ws_connected = False
                self.label.setText("Error de conexión. Reconectando...")
                QTimer.singleShot(5000, self.start_websocket)

    def process_websocket_data(self, data):
        items = []
        latest_update = None
        
        for category, items_list in data.items():
            if isinstance(items_list, list):
                for item in items_list:
                    items.append({
                        "category": category.upper(),
                        "name": item.get("name", "—"),
                        "price": item.get("price", "—"),
                        "stock": item.get("quantity", 0),
                        "lastUpdated": item.get("lastUpdated")
                    })
                    
                    if "lastUpdated" in item:
                        item_time = datetime.strptime(
                            item["lastUpdated"], 
                            "%Y-%m-%dT%H:%M:%S.%fZ"
                        ).replace(tzinfo=timezone.utc)
                        
                        if latest_update is None or item_time > latest_update:
                            latest_update = item_time
        
        with self._lock:
            self.store_data = items
        if latest_update:
            self.last_update_time = latest_update
            self.next_update_time = latest_update + self.update_interval
        self.reload_table()
        self.update_countdown()

    def update_countdown(self):
        now = datetime.now(timezone.utc)
        if self.next_update_time:
            if now >= self.next_update_time:
                self.label.setText("Actualizando datos...")
                self.next_update_time = now + self.update_interval

                with self._lock:
                    self.store_data = []
                self.reload_table()

                if self.ws_connected and self.loop:
                    asyncio.run_coroutine_threadsafe(self.request_update(), self.loop)
            else:
                remaining = self.next_update_time - now
                mins, secs = divmod(remaining.seconds, 60)
                self.label.setText(f"Próxima actualización en: {mins:02d}:{secs:02d}")

    def reload_table(self):
        with self._lock:
            items = self.store_data.copy()

        self.table.setRowCount(len(items))

        has_prismatic = False

        for row, item in enumerate(items):
            cat_item = QTableWidgetItem(item["category"])
            cat_item.setForeground(QColor(200, 230, 255))

            name_item = QTableWidgetItem(item["name"])
            name_item.setForeground(QColor("white"))

            quality = self.get_item_quality(item["name"])
            if quality is not None:
                quality_item = QTableWidgetItem(quality)
                quality_item.setForeground(QUALITY_COLORS.get(quality, QColor("white")))
                if quality == "Prismatic":
                    has_prismatic = True
            else:
                quality_item = QTableWidgetItem("-")
                quality_item.setForeground(QColor("white"))

            stock_item = QTableWidgetItem(str(item["stock"]))
            stock = item["stock"]
            if isinstance(stock, int):
                color = QColor(100, 255, 100) if stock > 3 else QColor(255, 100, 100)
                stock_item.setForeground(color)

            self.table.setItem(row, 0, cat_item)
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, quality_item)
            self.table.setItem(row, 3, stock_item)

        if has_prismatic:
            self.show_notification("✨ Prismatic encontrado",
                                "Hay un artículo Prismatic en la tienda",
                                duration=5)
            self.play_chime_sound()

    def show_notification(self, title, message, icon_path=None, duration=5):
        try:
            self.toaster.show_toast(
                title,
                message,
                icon_path=icon_path,
                duration=duration,
                threaded=True
            )
        except Exception as e:
            print(f"Error mostrando notificación: {e}")

    def play_chime_sound(self):
        try:
            notes = [440, 523, 659, 784, 988]
            duration = 130

            for freq in notes:
                winsound.Beep(freq, duration)
        except Exception as e:
            print(f"Error reproduciendo sonido: {e}")

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if event.pos().y() < 30:
                self.dragging = True
                self.offset = event.pos()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging:
            self.move(self.pos() + event.pos() - self.offset)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False

def main():
    app = QApplication(sys.argv)
    
    # Asegurarse de que el sistema soporte system tray
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("System Tray no está disponible en este sistema")
        return 1
        
    # Esto es importante para que la aplicación no se cierre al minimizar
    app.setQuitOnLastWindowClosed(False)
    
    window = StoreApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()