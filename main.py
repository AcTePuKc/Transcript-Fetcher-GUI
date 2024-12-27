import os
import sys
import asyncio
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy,
    QLabel, QLineEdit, QPushButton, QComboBox, QListWidget, QTextEdit, QProgressBar, QFileDialog, QStatusBar, QSplitter, QMenu
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
    update_progress_bar
    )
from fetcher import process_videos
import subprocess


# Ensure script directory is in Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Event handler for download progress
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
        self.setWindowTitle("YouTube Transcript Downloader")
        self.resize(1150, 600)
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.stop_download = False

        # Load settings or defaults
        self.settings = load_settings()
        self.output_format = self.settings.get("output_format", "TXT")
        self.language = self.settings.get("language", "en")
        self.file_policy = self.settings.get("file_policy", "Skip")
        self.current_theme = self.settings.get("current_theme", "default")


        # Initialize UI components
        self.init_ui()

        # Apply initial theme
        self.apply_theme()

    def init_ui(self):
        """Initialize the UI components and layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
    
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

        # Format Selection Section
        self.output_format_dropdown = QComboBox()
        self.output_format_dropdown.addItems(["TXT", "JSON", "SRT", "VTT"])
        self.language_dropdown = QComboBox()
        self.language_dropdown.addItems(["en", "de", "fr", "es", "it", "pt", "nl", "ru", "zh", "ja"])
        self.file_policy_dropdown = QComboBox()
        self.file_policy_dropdown.addItems(["Skip", "Overwrite", "Append Number"])

        # Add theme dropdown
        self.theme_dropdown = QComboBox()
        self.theme_dropdown.setPlaceholderText("Select Theme")
        self.populate_theme_dropdown()
        self.theme_dropdown.currentIndexChanged.connect(self.change_theme)

        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Select Output Format:"))
        format_layout.addWidget(self.output_format_dropdown)
        format_layout.addWidget(QLabel("Select Language:"))
        format_layout.addWidget(self.language_dropdown)
        format_layout.addWidget(QLabel("If File Exists:"))
        format_layout.addWidget(self.file_policy_dropdown)
        format_layout.addWidget(QLabel("Change Theme:"))  # Add label for theme
        format_layout.addWidget(self.theme_dropdown)  # Add theme dropdown
        # Save Directory Section
        self.select_dir_button = QPushButton("Select Save Directory")

        self.open_dir_button = QPushButton("Open Save Directory")
        self.clear_console_button = QPushButton("Clear Console")

        directory_layout = QHBoxLayout()
        directory_layout.addWidget(self.select_dir_button)
        directory_layout.addWidget(self.open_dir_button)
        directory_layout.addWidget(self.clear_console_button)

        # Recent Downloads and Console
        self.recent_list = QListWidget()
        self.console_output = QTextEdit()
        self.recent_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.recent_list.itemClicked.connect(self.load_url_from_recent)
        self.recent_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.recent_list.customContextMenuRequested.connect(self.open_menu)

        self.console_output.setReadOnly(True)
        self.console_output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.recent_list)
        splitter.addWidget(self.console_output)
        splitter.setSizes([self.settings.get("pane_position", 200), 600])

        main_layout.addLayout(input_layout)
        main_layout.addLayout(format_layout)
        main_layout.addLayout(directory_layout)
        main_layout.addWidget(splitter)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Connect Buttons
        self.paste_button.clicked.connect(self.paste_from_clipboard)
        self.download_button.clicked.connect(self.start_download)
        self.clear_console_button.clicked.connect(self.clear_console)
        self.select_dir_button.clicked.connect(self.select_save_directory)
        self.open_dir_button.clicked.connect(self.open_save_directory)
        self.cancel_button.clicked.connect(self.cancel_download)

        # Populate Dropdown Defaults
        self.output_format_dropdown.setCurrentText(self.output_format)
        self.language_dropdown.setCurrentText(self.language)
        self.file_policy_dropdown.setCurrentText(self.file_policy)
        self.output_format_dropdown.currentIndexChanged.connect(self.save_output_format)
        self.language_dropdown.currentIndexChanged.connect(self.save_language)
        self.file_policy_dropdown.currentIndexChanged.connect(self.save_file_policy)

        # Load Recent Downloads
        recent_downloads = load_recent_downloads()
        for item in recent_downloads:
            lang_tag = f"[{item.get('language', 'N/A').upper()}]"
            display_title = f"{item['title']} ({lang_tag}, {os.path.splitext(item['file_path'])[1][1:].upper()})"
            self.recent_list.addItem(display_title)

    def get_available_themes(self):
        """Return a list of available themes."""
        themes_dir = resource_path("themes")
        if not os.path.exists(themes_dir):
            os.makedirs(themes_dir)
        return [f[:-4] for f in os.listdir(themes_dir) if f.endswith(".css")]

    def populate_theme_dropdown(self):
        """Populate the theme dropdown with available themes."""
        self.theme_dropdown.clear()
        themes = self.get_available_themes()
        if not themes:
            self.theme_dropdown.addItem("Default Theme")
        for theme in themes:
            formatted_name = " ".join(word.capitalize() for word in theme.replace("_", " ").split())
            self.theme_dropdown.addItem(formatted_name, theme)

    def change_theme(self, index):
        """Handle theme changes from the dropdown."""
        if index < 0:
            return
        theme_key = self.theme_dropdown.itemData(index)
        self.settings["current_theme"] = theme_key
        save_settings(self.settings)
        self.apply_theme()

    def apply_theme(self):
        """Apply the selected theme or fallback if unavailable."""
        themes = self.get_available_themes()
        current_theme = self.settings.get("current_theme", "default")

        if current_theme in themes:
            self.load_theme_from_file(current_theme)
        else:
            self.apply_fallback_theme()
            if not os.path.exists(resource_path("themes")):
                self.apply_fallback_theme()
                return

        self.populate_theme_dropdown()

    def load_theme_from_file(self, theme_name):
        """Load and apply a theme from a file."""
        theme_file = resource_path(f"themes/{theme_name}.css")
        if os.path.exists(theme_file):
            try:
                with open(theme_file, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
                self.console_output.append(f"Applied theme: {theme_name}")
            except Exception as e:
                self.console_output.append(f"Failed to load theme '{theme_name}': {e}")
        else:
            self.apply_fallback_theme()

    def apply_fallback_theme(self):
        """Apply a fallback theme."""
        self.setStyleSheet("""
            QMainWindow { background-color: #EDEDED; color: #222222; }
            QPushButton { background-color: #D6D6D6; color: #222222; border: 1px solid #AAAAAA; }
        """)
        self.console_output.append("Applied fallback theme.")


    
    def save_pane_position(self, pos, index):
        self.settings["pane_position"] = pos
        save_settings(self.settings)

    def paste_from_clipboard(self):
        try:
            paste_from_clipboard(self.url_input)
        except Exception as e:
            display_message(self.console_output, f"Error: {e}", "error")

    def load_url_from_recent(self, item):
        recent_downloads = load_recent_downloads()
        index = self.recent_list.row(item)
        if 0 <= index < len(recent_downloads):
            self.url_input.setText(recent_downloads[index]["url"])
    
    def open_menu(self, position):
        menu = QMenu(self)
        open_action = menu.addAction("Open file")
        action = menu.exec(self.recent_list.viewport().mapToGlobal(position)) # changed from exec_ to exec
        if action == open_action:
            self.open_file_from_recent_list(position)
            
    def open_file_from_recent_list(self,position):
        item = self.recent_list.itemAt(position)
        if item:
             recent_downloads = load_recent_downloads()
             index = self.recent_list.row(item)
             if 0 <= index < len(recent_downloads):
                file_path = recent_downloads[index].get('file_path', '')
                if file_path and os.path.exists(file_path):
                    try:
                        if sys.platform.startswith('darwin'):
                            subprocess.call(('open', file_path))
                        elif os.name == 'nt':
                            os.startfile(file_path)
                        elif os.name == 'posix':
                           subprocess.call(('xdg-open', file_path))
                        display_message(self.console_output, f"Opened file: {file_path}", "info")
                    except Exception as e:
                        display_message(self.console_output, f"Failed to open file: {e}", "error")
                else:
                    display_message(self.console_output, "File does not exist.", "error")

    def clear_console(self):
        self.console_output.clear()

    def select_save_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if directory:
            self.settings["save_directory"] = directory
            save_settings(self.settings)
            display_message(self.console_output, f"Save directory selected: {directory}")

    def open_save_directory(self):
        os.startfile(self.settings.get("save_directory", os.getcwd()))

    def update_recent_downloads(self, title, url, file_path):
        format_type = os.path.splitext(file_path)[1][1:].upper()  # Extract file format
        language = self.language_dropdown.currentText()  # Get selected language

        # Load existing recent downloads
        recent_downloads = load_recent_downloads()

        # Remove duplicates (same title, URL, format, and language)
        recent_downloads = [
            item for item in recent_downloads
            if not (item['title'] == title and item['url'] == url and item['file_path'] == file_path and item.get('language') == language)
        ]

        # Add the new entry to the top
        recent_downloads.insert(0, {
            'title': title,
            'url': url,
            'file_path': file_path,
            'language': language
        })

        # Save back to the JSON file
        save_recent_downloads(recent_downloads)

        # Update the UI: Clear and reload
        self.recent_list.clear()
        for item in recent_downloads:
            lang_tag = f"[{item.get('language', 'N/A').upper()}]"  # Show language
            display_title = f"{item['title']} ({lang_tag}, {os.path.splitext(item['file_path'])[1][1:].upper()})"
            self.recent_list.addItem(display_title)



    def toggle_theme(self):
        self.dark_mode = not self.dark_mode # <-- Updated the logic
        self.settings["dark_mode"] = self.dark_mode
        self.apply_theme() # Applying the theme on toggle
        save_settings(self.settings)

    
    

    def change_theme(self, index):
        if index < 0:  # No valid selection
            return
        
        theme_key = self.theme_dropdown.itemData(index)
        if theme_key == "Default Theme":
            self.apply_fallback_theme("default")
            self.settings["current_theme"] = "default"
        else:
            self.settings["current_theme"] = theme_key
            self.load_theme_from_file(theme_key)

        save_settings(self.settings)
        display_message(self.console_output, f"Applied theme: {self.theme_dropdown.currentText()}")

    def save_output_format(self):
        self.settings["output_format"] = self.output_format_dropdown.currentText()
        save_settings(self.settings)
    
    def save_language(self):
        self.settings["language"] = self.language_dropdown.currentText()
        save_settings(self.settings)
        
    def save_file_policy(self):
        self.settings["file_policy"] = self.file_policy_dropdown.currentText()
        save_settings(self.settings)


    def start_download(self):
        video_url = self.url_input.text()
        if not video_url:
            display_message(self.console_output, "YouTube URL cannot be empty.", "error")
            return
        display_message(self.console_output, f"Starting download for: {video_url}")
        self.progress_bar.setValue(0)
        self.cancel_button.setEnabled(True)

        # Retrieve settings
        output_format = self.output_format_dropdown.currentText().lower()
        language = self.language_dropdown.currentText().lower()
        file_policy = self.file_policy_dropdown.currentText().lower()

        save_directory = self.settings.get("save_directory", os.getcwd())
        os.makedirs(save_directory, exist_ok=True)
        
        self.download_worker = DownloadWorker(
            video_url,
            [output_format],
            language,
            save_directory,
            self.console_output,
            self.update_recent_downloads,
            file_policy
        )
        self.download_worker.progress_updated.connect(self.update_progress)
        self.download_worker.finished.connect(self.download_finished)
        self.download_worker.start()

    def update_progress(self, current, total):
        update_progress_bar(self.progress_bar, current, total)

    def cancel_download(self):
        self.download_worker.stop()
        self.cancel_button.setEnabled(False)
        display_message(self.console_output, "Download cancelled by user.", "info")

    def download_finished(self):
        self.progress_bar.setValue(100)
        self.cancel_button.setEnabled(False)
        #display_message(self.console_output, "Download finished", "info") # Removed from here

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeTranscriptDownloader()
    window.show()
    sys.exit(app.exec())