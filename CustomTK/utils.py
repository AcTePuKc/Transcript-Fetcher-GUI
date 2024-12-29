# utils.py
import sys
import re
import json
import os
import tkinter as tk
from tkinter import ttk

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

# Function to paste from clipboard
def paste_from_clipboard(root, entry, console_output):
    """Paste clipboard content into the specified entry widget."""
    try:
        clipboard_content = root.clipboard_get()
        entry.delete(0, tk.END)
        entry.insert(0, clipboard_content)
    except tk.TclError:
        console_output("Clipboard is empty or invalid content.", "error")

