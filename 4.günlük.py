import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget, QTabWidget, QMessageBox, QAction, QInputDialog, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import QDateTime, Qt

class GunlukSekmesi(QWidget):
    def __init__(self, db_conn, parent=None):
        super(GunlukSekmesi, self).__init__(parent)
        
        self.db_conn = db_conn
        self.initUI()
        self.load_entries()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        self.entry_list = QListWidget(self)
        self.entry_list.itemDoubleClicked.connect(self.edit_entry)
        layout.addWidget(self.entry_list)
        
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Ekle", self)
        self.add_button.setFixedSize(100, 40)
        self.add_button.setStyleSheet("font-size: 18px;")
        self.add_button.clicked.connect(self.add_entry)
        button_layout.addWidget(self.add_button, alignment=Qt.AlignCenter)
        
        self.delete_button = QPushButton("Sil", self)
        self.delete_button.setFixedSize(100, 40)
        self.delete_button.setStyleSheet("font-size: 18px;")
        self.delete_button.clicked.connect(self.delete_entry)
        button_layout.addWidget(self.delete_button, alignment=Qt.AlignCenter)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def add_entry(self):
        text, ok = QInputDialog.getMultiLineText(self, "Yeni Giriş", "Günlük Girişinizi Yazın:")
        if ok and text:
            datetime_str = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
            entry = f"{datetime_str}\n{text}"
            list_item = QListWidgetItem(entry)
            self.entry_list.addItem(list_item)
            self.save_entry_to_db(datetime_str, text)
    
    def edit_entry(self, item):
        old_text = item.text().split('\n', 1)[1]
        text, ok = QInputDialog.getMultiLineText(self, "Girişi Düzenle", "Günlük Girişinizi Düzenleyin:", old_text)
        if ok and text:
            datetime_str = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
            entry = f"{datetime_str}\n{text}"
            item.setText(entry)
            self.update_entry_in_db(old_text, text)
    
    def delete_entry(self):
        selected_item = self.entry_list.currentItem()
        if selected_item:
            reply = QMessageBox.question(self, 'Silme Onayı', 'Bu girdiyi silmek istediğinize emin misiniz?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.remove_entry_from_db(selected_item.text().split('\n', 1)[1])
                self.entry_list.takeItem(self.entry_list.currentRow())

    def load_entries(self):
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT datetime, entry FROM entries")
        rows = cursor.fetchall()
        for row in rows:
            datetime_str, text = row
            entry = f"{datetime_str}\n{text}"
            list_item = QListWidgetItem(entry)
            self.entry_list.addItem(list_item)
    
    def save_entry_to_db(self, datetime_str, text):
        cursor = self.db_conn.cursor()
        cursor.execute("INSERT INTO entries (datetime, entry) VALUES (?, ?)", (datetime_str, text))
        self.db_conn.commit()
    
    def update_entry_in_db(self, old_text, new_text):
        cursor = self.db_conn.cursor()
        cursor.execute("UPDATE entries SET entry = ? WHERE entry = ?", (new_text, old_text))
        self.db_conn.commit()
    
    def remove_entry_from_db(self, text):
        cursor = self.db_conn.cursor()
        cursor.execute("DELETE FROM entries WHERE entry = ?", (text,))
        self.db_conn.commit()

class GunlukUygulamasi(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.db_conn = sqlite3.connect("gunluk.db")
        self.init_db()
        self.initUI()
    
    def init_db(self):
        cursor = self.db_conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datetime TEXT NOT NULL,
                entry TEXT NOT NULL
            )
        """)
        self.db_conn.commit()
    
    def initUI(self):
        self.setWindowTitle('Kişisel Günlük Uygulaması')
        self.setGeometry(100, 100, 600, 400)
        
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabBarDoubleClicked.connect(self.sekme_ismini_duzenle)
        self.tab_widget.tabCloseRequested.connect(self.sekme_kapat)
        self.setCentralWidget(self.tab_widget)
        
        self.yeni_gunluk_ekle()
        
        menubar = self.menuBar()
        gunluk_menu = menubar.addMenu('Günlük')
        
        yeni_action = QAction("Yeni Günlük Ekle", self)
        yeni_action.setShortcut("Ctrl+N")
        yeni_action.triggered.connect(self.yeni_gunluk_ekle)
        gunluk_menu.addAction(yeni_action)
        
        sekme_duzenle_action = QAction("Sekme İsmini Düzenle", self)
        sekme_duzenle_action.setShortcut("Ctrl+E")
        sekme_duzenle_action.triggered.connect(self.sekme_ismini_duzenle)
        gunluk_menu.addAction(sekme_duzenle_action)
        
        # QSS stili uygula
        self.setStyleSheet(self.qss_stili())
        
        self.show()
    
    def yeni_gunluk_ekle(self):
        yeni_sekme = GunlukSekmesi(self.db_conn)
        self.tab_widget.addTab(yeni_sekme, "Günlük " + str(self.tab_widget.count() + 1))
    
    def sekme_ismini_duzenle(self, index=None):
        if index is None:
            index = self.tab_widget.currentIndex()
        
        if index >= 0:
            current_name = self.tab_widget.tabText(index)
            yeni_isim, ok = QInputDialog.getText(self, "Sekme İsmini Düzenle", "Yeni isim girin:", text=current_name)
            if ok and yeni_isim:
                self.tab_widget.setTabText(index, yeni_isim)
    
    def sekme_kapat(self, index):
        self.tab_widget.removeTab(index)
    
    def qss_stili(self):
        return """
        QMainWindow {
            background-color: #f0f0f0;
        }
        QTabWidget::pane {
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        QTabBar::tab {
            background: #ddd;
            border: 1px solid #ccc;
            border-bottom: none;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            padding: 5px;
            margin-right: 1px;
        }
        QTabBar::tab:selected {
            background: #f0f0f0;
            border-color: #999;
        }
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:pressed {
            background-color: #3e8e41;
        }
        QListWidget {
            font-size: 16px;
        }
        """
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    gunluk_uygulamasi = GunlukUygulamasi()
    sys.exit(app.exec_())
