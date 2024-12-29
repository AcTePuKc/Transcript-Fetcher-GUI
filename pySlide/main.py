import os
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy,
    QLabel, QLineEdit, QPushButton, QComboBox, QListWidget, QTextEdit, QProgressBar, QFileDialog, QStatusBar, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from utils import (
    load_settings, 
    save_settings, 
    paste_from_clipboard, 
    load_recent_downloads, 
    save_recent_downloads, 
    resource_path, 
    clean_filename,
    )
from fetcher import process_single_video, on_download

# Select save directory
def select_save_directory(self):
    directory = QFileDialog.getExistingDirectory(self, "Select Save Directory")
    if directory:
        self.settings["save_directory"] = directory
        save_settings(self.settings)
        self.console_output.append(f"Save directory selected: {directory}")

# Add to recent downloads
def update_recent_downloads(self, title, url, file_path):
    display_title = f"{title} ({os.path.splitext(file_path)[1][1:].upper()})"
    self.recent_list.addItem(display_title)

# Toggle theme
def toggle_theme(self):
    dark_mode_enabled = self.settings.get("dark_mode", False)
    if not dark_mode_enabled:
        self.setStyleSheet("""
            QMainWindow { background-color: #2E2E2E; color: #FFFFFF; }
            QPushButton { background-color: #555555; color: #FFFFFF; }
            QLineEdit, QComboBox, QTextEdit, QListWidget { background-color: #3E3E3E; color: #FFFFFF; }
        """)
        self.console_output.append("Dark mode activated.")
    else:
        self.setStyleSheet("")  # Reverts to default
        self.console_output.append("Light mode activated.")

    self.settings["dark_mode"] = not dark_mode_enabled
    save_settings(self.settings)

def on_download(self):
    video_url = self.url_input.text()
    if not video_url:
        self.console_output.append("Error: YouTube URL cannot be empty.")
        return

    self.console_output.append(f"Starting download for: {video_url}")
    self.progress_bar.setValue(0)

    # Retrieve settings
    output_format = self.output_format_dropdown.currentText().lower()
    language = self.language_dropdown.currentText()
    file_policy = self.file_policy_dropdown.currentText().lower()

    save_directory = self.settings.get("save_directory", os.getcwd())
    os.makedirs(save_directory, exist_ok=True)

    try:
        # Process video
        result = process_single_video(
            video_url, 
            [output_format], 
            language, 
            save_directory, 
            self.console_output.append, 
            self.update_recent_downloads,
            lambda: False,  # Placeholder for stop event
            file_policy
        )
        if result is None:
            self.console_output.append(f"Successfully downloaded transcript for: {video_url}")
    except Exception as e:
        self.console_output.append(f"Error: {str(e)}")
    finally:
        self.progress_bar.setValue(100)
        self.cancel_button.setEnabled(False)

# Main Application Class
class YouTubeTranscriptDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Transcript Downloader")
        self.resize(1150, 600)
        self.setWindowIcon(QIcon(resource_path("icon.ico")))


        # Load settings
        self.settings = load_settings()
        self.output_format = self.settings.get("output_format", "TXT")
        self.language = self.settings.get("language", "en")
        self.file_policy = self.settings.get("file_policy", "Skip")

        # Main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Input Section
        self.url_input = QLineEdit()
        self.paste_button = QPushButton("Paste")
        self.download_button = QPushButton("Download")
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.dark_mode_button = QPushButton("Toggle Dark Mode")
        self.dark_mode_button.clicked.connect(lambda: toggle_theme(self))


        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("YouTube URL:"))
        input_layout.addWidget(self.url_input)
        input_layout.addWidget(self.paste_button)
        input_layout.addWidget(self.download_button)
        input_layout.addWidget(self.cancel_button)
        input_layout.addWidget(self.dark_mode_button)

        # Format Selection Section
        self.output_format_dropdown = QComboBox()
        self.output_format_dropdown.addItems(["TXT", "JSON", "SRT", "VTT"])
        self.language_dropdown = QComboBox()
        self.language_dropdown.addItems(["en", "de", "fr", "es", "it", "pt", "nl", "ru", "zh", "ja"])
        self.file_policy_dropdown = QComboBox()
        self.file_policy_dropdown.addItems(["Skip", "Overwrite", "Append Number"])

        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Select Output Format:"))
        format_layout.addWidget(self.output_format_dropdown)
        format_layout.addWidget(QLabel("Select Language:"))
        format_layout.addWidget(self.language_dropdown)
        format_layout.addWidget(QLabel("If File Exists:"))
        format_layout.addWidget(self.file_policy_dropdown)

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
        self.recent_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.recent_list)
        splitter.addWidget(self.console_output)
        splitter.setSizes([200, 600])  # Initial sizes

        main_layout.addWidget(splitter)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setValue(0)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Add all layouts to main layout
        main_layout.addLayout(input_layout)
        main_layout.addLayout(format_layout)
        main_layout.addLayout(directory_layout)
        main_layout.addWidget(splitter)
        main_layout.addWidget(self.progress_bar)

        # Connect Buttons
        self.paste_button.clicked.connect(self.paste_from_clipboard)
        self.download_button.clicked.connect(on_download)
        self.clear_console_button.clicked.connect(self.clear_console)
        self.select_dir_button.clicked.connect(self.select_save_directory)
        self.open_dir_button.clicked.connect(self.open_save_directory)

    def paste_from_clipboard(self):
        clipboard = QApplication.clipboard()
        self.url_input.setText(clipboard.text())

    

        # Retrieve settings
        output_format = self.output_format_dropdown.currentText().lower()
        language = self.language_dropdown.currentText()
        file_policy = self.file_policy_dropdown.currentText().lower()
        save_directory = self.settings.get("save_directory", os.getcwd())

        os.makedirs(save_directory, exist_ok=True)

        try:
            process_single_video(
                video_url,
                [output_format],
                language,
                save_directory,
                self.console_output.append,
                lambda title, url, file: self.update_recent_downloads(title, url, file),
                lambda: False,  # Stop event placeholder
                file_policy
            )
        except Exception as e:
            self.console_output.append(f"Error: {str(e)}")
        finally:
            self.progress_bar.setValue(100)
    def clear_console(self):
        self.console_output.clear()

    def select_save_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if directory:
            self.console_output.append(f"Save directory selected: {directory}")

    def open_save_directory(self):
        os.startfile(self.settings.get("save_directory", os.getcwd()))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeTranscriptDownloader()
    window.show()
    sys.exit(app.exec())
