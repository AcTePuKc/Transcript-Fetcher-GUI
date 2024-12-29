# Updated main.py
import os
import sys
import asyncio
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy,
    QLabel, QLineEdit, QPushButton, QComboBox, QListWidget, QTextEdit, QProgressBar, QFileDialog, QStatusBar, QSplitter, QTabWidget, QDialog, QMenu, 
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QIcon
from threading import Event
from utils import (
    load_settings, save_settings, paste_from_clipboard, load_recent_downloads,
    save_recent_downloads, resource_path, display_message, update_progress_bar
)
from fetcher import process_videos
import subprocess


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
                lambda msg, level: display_message(
                    self.console_output, msg, level),
                self.update_recent_downloads,
                self.stop_event,
                self.file_policy,
                lambda current, total: self.progress_updated.emit(
                    current, total)
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

        # Load settings or defaults
        self.settings = load_settings()
        self.save_directory = self.settings.get(
            "save_directory", os.path.expanduser("~/YT-Transcribe-Downloads"))
        self.output_format = self.settings.get("output_format", "TXT")
        self.language = self.settings.get("language", "en")
        self.file_policy = self.settings.get("file_policy", "Skip")
        self.current_theme = self.settings.get("current_theme", "light")

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

        # Properties Button
        self.properties_button = QPushButton("Properties")
        self.properties_button.clicked.connect(self.open_properties_tab)

        # Recent Downloads and Console
        self.recent_list = QListWidget()  # Initialize recent_list here
        self.recent_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.recent_list.itemClicked.connect(self.load_url_from_recent)
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)

        # Splitter for recent_list and console_output
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.recent_list)
        self.splitter.addWidget(self.console_output)
        
        # Restore splitter state if saved
        splitter_state = self.settings.get("splitter_state")
        if splitter_state:
            self.splitter.restoreState(bytes.fromhex(splitter_state))
        else:
            self.splitter.setSizes([200, 600])  # Default sizes

        main_layout.addLayout(input_layout)
        main_layout.addWidget(self.properties_button)
        main_layout.addWidget(self.splitter)

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
        self.cancel_button.clicked.connect(self.cancel_download)

        # Populate the recent downloads list
        self.populate_recent_downloads()

    def open_recent_menu(self, position):
        """Open the context menu for the recent downloads list."""
        menu = QMenu(self)

        open_action = menu.addAction("Open File")
        remove_action = menu.addAction("Remove from List")

        action = menu.exec(self.recent_list.viewport().mapToGlobal(position))
        selected_item = self.recent_list.currentItem()

        if selected_item:
            if action == open_action:
                self.open_file_from_recent(selected_item)
            elif action == remove_action:
                self.remove_item_from_recent(selected_item)
    def open_file_from_recent(self, item):
        """Open the file associated with a recent download."""
        recent_downloads = load_recent_downloads()  # Load recent downloads from JSON
        index = self.recent_list.row(item)  # Get the selected item's index

        if 0 <= index < len(recent_downloads):
            file_path = recent_downloads[index].get("file_path")
            if file_path and os.path.exists(file_path):  # Ensure the file exists
                try:
                    # Open the file using the default application
                    if sys.platform == "win32":
                        os.startfile(file_path)
                    elif sys.platform == "darwin":
                        subprocess.run(["open", file_path])
                    else:
                        subprocess.run(["xdg-open", file_path])
                except Exception as e:
                    display_message(self.console_output, f"Error opening file: {e}", "error")
            else:
                display_message(self.console_output, "File not found.", "error")

    def remove_item_from_recent(self, item):
        """Remove a recent download from the list."""
        recent_downloads = load_recent_downloads()
        index = self.recent_list.row(item)
        if 0 <= index < len(recent_downloads):
            recent_downloads.pop(index)
            save_recent_downloads(recent_downloads)
            self.recent_list.takeItem(index)

    def populate_recent_downloads(self):
        """Populate the recent downloads list from saved data."""
        recent_downloads = load_recent_downloads()  # Load from JSON file
        self.recent_list.clear()  # Clear the UI list
        for entry in recent_downloads:
            title = entry.get("title", "Untitled")
            url = entry.get("url", "Unknown URL")
            output_format = entry.get("format", "TXT")  # Default to TXT if missing
            language = entry.get("language", "EN")      # Default to EN if missing
            display_text = f"{title} [{output_format.upper()} | {language.upper()}]"
            self.recent_list.addItem(display_text)

    
    def open_properties_tab(self):
        """Open the Properties dialog."""
        self.properties_dialog = QDialog(
            self)  # Create a new dialog every time
        self.properties_dialog.setWindowTitle("Properties")
        layout = QVBoxLayout(self.properties_dialog)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Add tabs
        general_tab = QWidget()
        self.init_general_tab(general_tab)
        self.tab_widget.addTab(general_tab, "General")

        themes_tab = QWidget()
        self.init_themes_tab(themes_tab)  # Refresh the dropdown each time
        self.tab_widget.addTab(themes_tab, "Themes")

        directories_tab = QWidget()
        self.init_directories_tab(directories_tab)
        self.tab_widget.addTab(directories_tab, "Directories")

        # Apply the stylesheet to the dialog explicitly
        theme = self.settings.get("current_theme", "light")
        theme_file = resource_path(f"themes/{theme}.css")
        if os.path.exists(theme_file):
            with open(theme_file, "r", encoding="utf-8") as f:
                self.properties_dialog.setStyleSheet(f.read())

        self.properties_dialog.exec()

    def init_general_tab(self, tab):
        """Initialize the General tab."""
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Output Format
        layout.addWidget(QLabel("Select Output Format:"))
        self.output_format_dropdown = QComboBox()
        self.output_format_dropdown.addItems(["TXT", "JSON", "SRT", "VTT"])
        layout.addWidget(self.output_format_dropdown)

        # Language Selection
        layout.addWidget(QLabel("Select Language:"))
        self.language_dropdown = QComboBox()
        self.language_dropdown.addItems(["en", "de", "fr", "es", "it"])
        layout.addWidget(self.language_dropdown)

        # File Policy
        layout.addWidget(QLabel("File Policy:"))
        self.file_policy_dropdown = QComboBox()
        self.file_policy_dropdown.addItems(
            ["Skip", "Replace", "Append number"])
        self.file_policy_dropdown.setCurrentText(self.file_policy)
        layout.addWidget(self.file_policy_dropdown)

        # Save Button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_general_settings)
        layout.addWidget(save_button)

    def init_themes_tab(self, tab):
        """Initialize the Themes tab."""
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Theme Dropdown
        layout.addWidget(QLabel("Select Theme:"))
        self.theme_dropdown = QComboBox()
        self.populate_theme_dropdown()
        current_theme = self.settings.get("current_theme", "light")
        # Sync dropdown with saved theme
        self.theme_dropdown.setCurrentText(current_theme)
        layout.addWidget(self.theme_dropdown)

        # Apply Theme Button
        button_layout = QHBoxLayout()  # Horizontal layout for buttons
        apply_button = QPushButton("Apply Theme")
        apply_button.clicked.connect(
            self.apply_selected_theme)  # Apply theme immediately
        button_layout.addWidget(apply_button)

        # Reset Theme Button
        reset_button = QPushButton("Reset Theme")
        reset_button.clicked.connect(self.reset_theme)
        button_layout.addWidget(reset_button)

        layout.addLayout(button_layout)

    def save_splitter_state(self):
        """Save the current splitter position to settings."""
        self.settings["splitter_state"] = self.splitter.saveState().data().hex()  # Save as hex string
        save_settings(self.settings)

    def closeEvent(self, event):
        """Handle application close events."""
        self.save_splitter_state()  # Save splitter position
        save_settings(self.settings)  # Save other settings
        super().closeEvent(event)

    def init_directories_tab(self, tab):
        """Initialize the Directories tab."""
        layout = QVBoxLayout()
        tab.setLayout(layout)

        layout.addWidget(QLabel("Save Directory:"))
        self.directory_label = QLabel(self.save_directory)
        layout.addWidget(self.directory_label)

        select_button = QPushButton("Select Directory")
        select_button.clicked.connect(self.select_save_directory)
        layout.addWidget(select_button)

    def populate_theme_dropdown(self):
        """Populate the theme dropdown with available themes."""
        self.theme_dropdown.clear()
        themes_dir = resource_path("themes")
        themes = [f[:-4] for f in os.listdir(themes_dir) if f.endswith(".css")]
        self.theme_dropdown.addItems(themes)

    def apply_selected_theme(self):
        """Save and apply the selected theme immediately."""
        selected_theme = self.theme_dropdown.currentText()  # Get selected theme
        self.settings["current_theme"] = selected_theme  # Update settings
        save_settings(self.settings)  # Save settings to the file
        self.apply_theme()  # Apply the theme dynamically

        # Update Preferences Tab immediately
        if hasattr(self, "properties_dialog"):  # Ensure dialog exists
            theme_file = resource_path(f"themes/{selected_theme}.css")
            if os.path.exists(theme_file):
                with open(theme_file, "r", encoding="utf-8") as f:
                    self.properties_dialog.setStyleSheet(f.read())

        # Status feedback
        self.status_bar.showMessage(f"Theme applied: {selected_theme}", 3000)

    def reset_theme(self):
        """Reset the theme to the default."""
        self.settings["current_theme"] = "light"  # Reset theme to default
        save_settings(self.settings)
        self.apply_theme()
        # Update Preferences Tab immediately
        if hasattr(self, "properties_dialog"):  # Ensure dialog exists
            theme_file = resource_path(f"themes/{self.settings['current_theme']}.css")
            if os.path.exists(theme_file):
                with open(theme_file, "r", encoding="utf-8") as f:
                    self.properties_dialog.setStyleSheet(f.read())
        self.status_bar.showMessage("Theme reset to default", 3000)

    def apply_theme(self):
        """Apply the current theme dynamically."""
        theme = self.settings.get(
            "current_theme", "light")  # Get the current theme
        theme_file = resource_path(f"themes/{theme}.css")
        if os.path.exists(theme_file):
            with open(theme_file, "r", encoding="utf-8") as f:
                theme_css = f.read()
                # Apply theme globally and to the main window
                self.setStyleSheet("")  # Clear existing styles
                QApplication.instance().setStyleSheet(
                    theme_css)  # Global application of stylesheet
                self.setStyleSheet(theme_css)
        else:
            display_message(self.console_output, f"Theme file not found: {
                            theme_file}", "error")

    def apply_custom_theme(self):
        """Apply custom colors defined by the user."""
        bg_color = self.bg_color_input.text() or "#212121"
        text_color = self.text_color_input.text() or "#FFFFFF"

        custom_css = f"""
        QMainWindow {{
            background-color: {bg_color};
            color: {text_color};
        }}
        QPushButton {{
            background-color: #424242;
            color: {text_color};
        }}
        """
        self.setStyleSheet(custom_css)
        display_message(self.console_output,
                        "Custom theme applied!", "success")

    def save_general_settings(self):
        """Save settings from the General tab."""
        self.settings["output_format"] = self.output_format_dropdown.currentText()
        self.settings["language"] = self.language_dropdown.currentText()
        self.settings["file_policy"] = self.file_policy_dropdown.currentText()
        save_settings(self.settings)

    def select_save_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Save Directory")
        if directory:
            self.save_directory = directory
            self.settings["save_directory"] = directory
            save_settings(self.settings)
            self.directory_label.setText(directory)

    def paste_from_clipboard(self):
        paste_from_clipboard(self.url_input)

    def start_download(self):
        video_url = self.url_input.text()
        if not video_url:
            display_message(self.console_output,
                            "YouTube URL cannot be empty.", "error")
            return

        display_message(self.console_output,
                        f"Starting download for: {video_url}", "info")
        self.progress_bar.setValue(0)
        self.cancel_button.setEnabled(True)

        self.download_worker = DownloadWorker(
            video_url,
            [self.output_format.lower()],
            self.language,
            self.save_directory,
            self.console_output,
            self.update_recent_downloads,
            self.settings["file_policy"]
        )

        self.download_worker.progress_updated.connect(self.update_progress)
        self.download_worker.finished.connect(self.download_finished)
        self.download_worker.start()

    def update_progress(self, current, total):
        update_progress_bar(self.progress_bar, current, total)

    def cancel_download(self):
        self.download_worker.stop()
        self.cancel_button.setEnabled(False)
        display_message(self.console_output, "Download cancelled.", "info")

    def download_finished(self):
        self.progress_bar.setValue(100)
        QTimer.singleShot(1000, lambda: self.progress_bar.setValue(0))  # Reset to 0 after 1 seconds
        self.cancel_button.setEnabled(False)


    def load_url_from_recent(self, item):
        recent_downloads = load_recent_downloads()
        index = self.recent_list.row(item)
        if 0 <= index < len(recent_downloads):
            self.url_input.setText(recent_downloads[index]["url"])

    def update_recent_downloads(self, title, url, file_path):
        """Update the recent downloads list."""
        recent_downloads = load_recent_downloads()

        # Avoid duplicate entries
        if any(entry["url"] == url for entry in recent_downloads):
            return

        # Add the new download
        recent_downloads.insert(0, {
            "title": title,
            "url": url,
            "file_path": file_path,
            "format": self.output_format,   # Include format
            "language": self.language       # Include language
        })
        save_recent_downloads(recent_downloads)

        # Update the UI with the new item
        display_text = f"{title} [{self.output_format.upper()} | {self.language.upper()}] - {url}"
        self.recent_list.insertItem(0, display_text)

        # Limit the number of items in the list
        if len(recent_downloads) > 100:
            recent_downloads.pop()
            save_recent_downloads(recent_downloads)


            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeTranscriptDownloader()
    window.show()
    sys.exit(app.exec())
