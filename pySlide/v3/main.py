import os
import sys
import logging
import asyncio
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy,
    QLabel, QLineEdit, QPushButton, QComboBox, QListWidget, QTextEdit, QProgressBar, QFileDialog, QTabWidget,
    QCheckBox, QMenu
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon
from threading import Event
from utils import (
    load_settings,
    save_settings,
    paste_from_clipboard,
    load_recent_downloads,
    save_recent_downloads,
    resource_path,
    display_message,
    setup_logging
)
from fetcher import process_videos

class DownloadWorker(QThread):
    progress_updated = Signal(int, int)
    finished = Signal()

    def __init__(self, url, output_formats, language, save_directory, console_output, update_recent_downloads, file_policy):
        super().__init__()
        self.url = url
        self.output_formats = output_formats
        self.language = language
        self.save_directory = save_directory
        self.console_output = console_output
        self.update_recent_downloads = update_recent_downloads
        self.file_policy = file_policy
        self.stop_event = Event()

    
    def run(self):
        asyncio.run(
            process_videos(
                self.url,
                self.output_formats,
                self.language,
                self.save_directory,
                lambda msg, level: display_message(self.console_output, msg, level),
                self.update_recent_downloads,
                self.stop_event,
                self.file_policy,
                lambda current, total: self.progress_updated.emit(current, total)
            )
        )
        self.finished.emit()

    def stop(self):
        self.stop_event.set()


class YouTubeTranscriptDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        setup_logging()
        self.setWindowTitle("YouTube Transcript Downloader v1.4")
        self.resize(1150, 600)
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        
        # Load settings or defaults
        self.settings = load_settings()
        self.language = self.settings.get("language", "English")
        self.dark_mode = self.settings.get("dark_mode", False)
        self.save_directory = self.settings.get("save_directory", os.getcwd())
        self.show_timestamps = self.settings.get("show_timestamps", True)

        # Main Layout
        self.tab_widget = QTabWidget()
        self.main_tab = QWidget()
        self.preferences_tab = QWidget()

        # Set up tabs
        self.tab_widget.addTab(self.main_tab, "Main")
        self.tab_widget.addTab(self.preferences_tab, "Preferences")
        self.setCentralWidget(self.tab_widget)

        # Build tabs
        self.setup_main_tab()
        self.setup_preferences_tab()

        # Apply theme
        self.apply_theme()

    def setup_main_tab(self):
        main_layout = QVBoxLayout(self.main_tab)

        # Input Section
        self.url_input = QLineEdit()
        self.paste_button = QPushButton("Paste")
        self.download_button = QPushButton("Download")
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)

        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("YouTube URL:"))
        input_layout.addWidget(self.url_input)
        input_layout.addWidget(self.paste_button)
        input_layout.addWidget(self.download_button)
        input_layout.addWidget(self.cancel_button)

        # Recent Downloads and Console
        self.recent_list = QListWidget()
        self.recent_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.recent_list.itemClicked.connect(self.load_url_from_recent)
        self.recent_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.recent_list.customContextMenuRequested.connect(self.open_menu)

        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout.addLayout(input_layout)
        main_layout.addWidget(self.recent_list)
        main_layout.addWidget(self.console_output)

        # Connect Buttons
        self.paste_button.clicked.connect(self.paste_from_clipboard)
        self.download_button.clicked.connect(self.start_download)
        self.cancel_button.clicked.connect(self.cancel_download)

        # Load recent downloads
        recent_downloads = load_recent_downloads()
        for item in recent_downloads:
            self.add_recent_download_to_ui(item)

    def setup_preferences_tab(self):
        layout = QVBoxLayout(self.preferences_tab)

        # Language Selection
        self.language_dropdown = QComboBox()
        self.language_dropdown.addItems(["English", "Deutsch", "Español"])
        self.language_dropdown.setCurrentText(self.language)
        self.language_dropdown.currentIndexChanged.connect(self.change_language)
        layout.addWidget(QLabel("Select Language:"))
        layout.addWidget(self.language_dropdown)

        # Theme Toggle
        self.theme_toggle = QCheckBox("Enable Dark Mode")
        self.theme_toggle.setChecked(self.dark_mode)
        self.theme_toggle.stateChanged.connect(self.toggle_theme_from_preferences)
        layout.addWidget(self.theme_toggle)

        # Default Save Directory
        self.save_dir_button = QPushButton("Set Default Save Directory")
        self.save_dir_button.clicked.connect(self.select_save_directory)
        layout.addWidget(self.save_dir_button)

        # Show Timestamps
        self.timestamps_toggle = QCheckBox("Show Timestamps in Recent Downloads")
        self.timestamps_toggle.setChecked(self.show_timestamps)
        self.timestamps_toggle.stateChanged.connect(self.toggle_timestamps)
        layout.addWidget(self.timestamps_toggle)

        # App Info
        layout.addWidget(QLabel("App Version: v1.4"))
        layout.addWidget(QLabel("GitHub: https://github.com/your-repo-link"))
        layout.addStretch()

    def toggle_theme_from_preferences(self):
        self.dark_mode = self.theme_toggle.isChecked()
        self.settings["dark_mode"] = self.dark_mode
        save_settings(self.settings)
        self.apply_theme()

    def toggle_timestamps(self):
        self.show_timestamps = self.timestamps_toggle.isChecked()
        self.settings["show_timestamps"] = self.show_timestamps
        save_settings(self.settings)
        self.recent_list.clear()
        recent_downloads = load_recent_downloads()
        for item in recent_downloads:
            self.add_recent_download_to_ui(item)

    def apply_theme(self):
        if self.dark_mode:
            self.setStyleSheet("QMainWindow { background-color: #212121; color: #FFFFFF; }")
        else:
            self.setStyleSheet("QMainWindow { background-color: #FFFFFF; color: #000000; }")

    def change_language(self, index):
        language_map = {0: "English", 1: "Deutsch", 2: "Español"}
        self.language = language_map[index]
        self.settings["language"] = self.language
        save_settings(self.settings)

    def add_recent_download_to_ui(self, item):
        timestamp = f" ({item['timestamp']})" if self.show_timestamps else ""
        lang_tag = f"[{item.get('language', 'N/A').upper()}]"
        display_title = f"{lang_tag} {item['title']} ({os.path.splitext(item['file_path'])[1][1:].upper()}){timestamp}"
        self.recent_list.addItem(display_title)

    def open_menu(self, position):
        menu = QMenu(self)
        open_action = menu.addAction("Open File")
        open_dir_action = menu.addAction("Open Save Directory")
        clear_all_action = menu.addAction("Clear All Downloads")
        remove_entry_action = menu.addAction("Remove Selected Entry")
        redownload_action = menu.addAction("Re-download")

        action = menu.exec(self.recent_list.viewport().mapToGlobal(position))
        if action == open_action:
            self.open_file_from_recent_list(position)
        elif action == open_dir_action:
            self.open_save_directory()
        elif action == clear_all_action:
            self.clear_all_downloads()
        elif action == remove_entry_action:
            self.remove_selected_entry(position)
        elif action == redownload_action:
            self.redownload_entry(position)

    
    # Other functions omitted for brevity (start_download, cancel_download, etc.)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeTranscriptDownloader()
    window.show()
    sys.exit(app.exec())
