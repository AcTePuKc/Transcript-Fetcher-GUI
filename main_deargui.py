# Rewriting the provided Tkinter code to Dear PyGui
# Note: Dear PyGui's procedural style and callback-based structure require restructuring the logic.

import dearpygui.dearpygui as dpg
import os
import asyncio
from utils import load_recent_downloads, save_recent_downloads, load_settings, save_settings

# Initialization and context creation
dpg.create_context()
dpg.create_viewport(title="YouTube Transcript Downloader", width=900, height=600)

settings = load_settings()
dark_mode = settings.get("dark_mode", False)
save_directory = settings.get("save_directory", os.getcwd())
recent_downloads = load_recent_downloads()

# Callbacks
def toggle_theme_callback(sender, app_data):
    global dark_mode
    dark_mode = not dark_mode
    settings["dark_mode"] = dark_mode
    save_settings(settings)
    if dark_mode:
        dpg.set_viewport_clear_color((30, 30, 30))  # Set a dark background
    else:
        dpg.set_viewport_clear_color((255, 255, 255))  # Set a light background

def select_save_directory_callback():
    directory = dpg.open_file_dialog(callback=None, directory=True)
    if directory:
        save_directory = directory
        settings["save_directory"] = directory
        save_settings(settings)
        dpg.set_value("status_bar", f"Save directory set to: {directory}")

def download_callback():
    url = dpg.get_value("url_entry").strip()
    if not url:
        dpg.set_value("status_bar", "Please enter a YouTube video or playlist URL.")
        return
    # Add logic for download handling
    dpg.set_value("status_bar", f"Processing download for URL: {url}")

def clear_recent_downloads_callback():
    global recent_downloads
    recent_downloads.clear()
    save_recent_downloads(recent_downloads)
    dpg.set_value("recent_downloads", [])
    dpg.set_value("status_bar", "Recent downloads cleared.")

def console_output_callback(message, msg_type="info"):
    output = f"[{msg_type.upper()}]: {message}"
    dpg.add_text(output, parent="console_output")

# Function to update recent downloads
def update_recent_downloads_callback(title, url, file_path):
    global recent_downloads
    recent_downloads.insert(0, {"title": title, "url": url, "file_path": file_path})
    recent_downloads = recent_downloads[:10]  # Keep only the last 10
    save_recent_downloads(recent_downloads)
    dpg.configure_item("recent_downloads", items=[item["title"] for item in recent_downloads])

# UI Creation
with dpg.window(label="Main Window", width=900, height=600):
    with dpg.group(horizontal=True):
        dpg.add_button(label="Toggle Dark Mode", callback=toggle_theme_callback)
        dpg.add_input_text(label="YouTube URL", tag="url_entry", width=300)
        dpg.add_button(label="Download Transcript", callback=download_callback)
        dpg.add_button(label="Select Save Directory", callback=select_save_directory_callback)

    dpg.add_separator()

    with dpg.child_window(label="Recent Downloads", width=400, height=300):
        dpg.add_listbox(items=[item["title"] for item in recent_downloads], tag="recent_downloads", num_items=10)
        dpg.add_button(label="Clear", callback=clear_recent_downloads_callback)

    with dpg.child_window(label="Console", width=500, height=300, tag="console_output"):
        dpg.add_text("Console output will appear here.")

    dpg.add_separator()

    with dpg.group(horizontal=True):
        dpg.add_progress_bar(tag="progress_bar", width=800, default_value=0.0)
        dpg.add_text("Status Bar", tag="status_bar")

# Apply initial theme
if dark_mode:
    dpg.set_viewport_clear_color((30, 30, 30))  # Set a dark background
else:
    dpg.set_viewport_clear_color((255, 255, 255))  # Set a light background

# Finalize and run
dpg.create_viewport()
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
