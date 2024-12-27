# utils.py
import sys
import re
import json
import os
import urllib.parse
from PySide6.QtWidgets import QApplication

# Function to get the absolute path to a resource
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller uses _MEIPASS to store resources
        base_path = sys._MEIPASS
    except AttributeError:
        # Use the directory of the current script
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# Function to clean filenames
def clean_filename(title):
    title = re.sub(r'[\\/*?:"<>|]', '', title)
    title = re.sub(r'[^\w\s-]', '', title)
    return re.sub(r'[-\s]+', '_', title).strip().lower()

# Function to load recent downloads
def load_recent_downloads():
    file_path = resource_path('recent_downloads.json')
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Function to save recent downloads
def save_recent_downloads(recent_downloads):
    file_path = resource_path('recent_downloads.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(recent_downloads, f, ensure_ascii=False, indent=4)

# Function to load settings
def load_settings():
    file_path = resource_path('settings.json')
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Function to save settings
def save_settings(settings):
    file_path = resource_path('settings.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def convert_short_url_to_full(url):
    if "youtu.be" in url:
        video_id = url.split("/")[-1]
        # Preserve the query parameters (like playlist) when converting the URL
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        list_param = f"&list={query_params['list'][0]}" if 'list' in query_params else ""
        return f"https://www.youtube.com/watch?v={video_id}{list_param}"
    return url

def is_playlist(url):
    parsed_url = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    return "list" in query_params

def is_video(url):
    url = convert_short_url_to_full(url)  # Convert to full URL if necessary
    parsed_url = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    return "v" in query_params and "list" not in query_params

def handle_file_policy(file_path, policy, filename, extension):
    if policy.lower() == 'skip' and os.path.exists(file_path):
        return None
    if policy.lower() == 'append number':
        counter = 1
        while os.path.exists(file_path):
            file_path = os.path.join(os.path.dirname(file_path), f"{filename}_{counter}.{extension}")
            counter += 1
    return file_path  # Default to overwrite

def save_transcript(transcript_data, filename, save_directory, file_policy, extension, formatter=None):
    os.makedirs(save_directory, exist_ok=True)
    file_path = os.path.join(save_directory, f"{filename}.{extension}")

    # Handle file policy
    file_path = handle_file_policy(file_path, file_policy, filename, extension)
    if not file_path:
        return False, ""

    # Format the transcript
    if formatter:
        formatted_transcript = formatter.format_transcript(transcript_data)
    else:
        # Default to plain text
        formatted_transcript = " ".join([entry['text'].replace('\n', ' ') for entry in transcript_data])

    # Save to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(formatted_transcript)

    return True, file_path

def paste_from_clipboard(entry_widget):
    """Paste clipboard content into the specified entry widget."""
    clipboard = QApplication.clipboard()
    entry_widget.setText(clipboard.text())

def update_progress_bar(progress_bar, current, total):
    progress = int((current / total) * 100) if total > 0 else 0
    progress_bar.setValue(progress)

def display_message(console_output, message, level='info'):
    """Display messages in the console output with different styles based on the level."""
    if level == 'info':
        console_output.append(f"<span style='color: blue;'>Info: {message}</span>")
    elif level == 'success':
        console_output.append(f"<span style='color: green;'>Success: {message}</span>")
    elif level == 'error':
        console_output.append(f"<span style='color: red;'>Error: {message}</span>")
    else:
        console_output.append(f"<span style='color: black;'>{message}</span>")  # Default
