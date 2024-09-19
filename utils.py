# utils.py

import re
import json
import os

# Function to clean filenames
def clean_filename(title):
    title = re.sub(r'[\\/*?:"<>|]', '', title)
    title = re.sub(r'[^\w\s-]', '', title)
    return re.sub(r'[-\s]+', '_', title).strip().lower()

# Function to load recent downloads
def load_recent_downloads():
    if os.path.exists('recent_downloads.json'):
        with open('recent_downloads.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Function to save recent downloads
def save_recent_downloads(recent_downloads):
    with open('recent_downloads.json', 'w', encoding='utf-8') as f:
        json.dump(recent_downloads, f, ensure_ascii=False, indent=4)
# Function to load settings
def load_settings():
    if os.path.exists('settings.json'):
        with open('settings.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Function to save settings
def save_settings(settings):
    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)