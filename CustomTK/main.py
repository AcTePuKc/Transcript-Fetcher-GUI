import customtkinter as ctk
from tkinter import filedialog
import threading
import asyncio
import os
import sys
from utils import (
    load_recent_downloads,
    save_recent_downloads,
    load_settings,
    save_settings,
    resource_path,
    paste_from_clipboard,
)
from transcript_fetcher import process_videos

# Initialize the main window
ctk.set_appearance_mode("Dark")  # Options: "Dark", "Light", "System"
ctk.set_default_color_theme("blue")  # Theme color

root = ctk.CTk()
root.title("YouTube Transcript Downloader")
root.geometry("900x600")

# Load settings
settings = load_settings()
dark_mode = settings.get("dark_mode", False)

# Variables to store settings with defaults
save_directory_var = ctk.StringVar(value=settings.get("save_directory", resource_path("downloads")))
recent_downloads = load_recent_downloads()
output_format_var = ctk.StringVar(value=settings.get("output_format", "TXT"))
language_var = ctk.StringVar(value=settings.get("language", "en"))
file_policy_var = ctk.StringVar(value=settings.get("file_policy", "skip"))

# Function to toggle themes
def toggle_theme():
    current_mode = ctk.get_appearance_mode()
    new_mode = "Light" if current_mode == "Dark" else "Dark"
    ctk.set_appearance_mode(new_mode)
    settings["dark_mode"] = new_mode == "Dark"
    save_settings(settings)

# Function to select save directory
def select_save_directory():
    directory = filedialog.askdirectory()
    if directory:
        save_directory_var.set(directory)
        settings["save_directory"] = directory
        save_settings(settings)
        console_output(f"Save directory set to: {directory}", "info")

# Function to update recent downloads
def update_recent_downloads(title, url, file_path):
    for item in recent_downloads:
        if item["file_path"] == file_path:
            return  # Avoid duplicates
    display_title = f"{title} ({os.path.splitext(file_path)[1][1:].upper()})"
    recent_downloads.append({"title": title, "url": url, "file_path": file_path})
    save_recent_downloads(recent_downloads)
    recent_listbox.insert(0, display_title)

# Function to clear recent downloads
def clear_recent_downloads():
    recent_downloads.clear()
    save_recent_downloads(recent_downloads)
    recent_listbox.delete(0, ctk.END)
    console_output("Recent downloads cleared.", "info")

# Function to clear the console output
def clear_console():
    console_text.delete("1.0", ctk.END)

# Console output function
def console_output(message, msg_type="info"):
    console_text.insert(ctk.END, message + "\n")
    console_text.see(ctk.END)

# Add a global stop event
stop_event = threading.Event()

# Function to handle download button click
def on_download_button_click():
    url = url_entry.get().strip()
    if not url:
        console_output("Please enter a YouTube URL.", "error")
        return

    selected_format = output_format_var.get()
    settings["output_format"] = selected_format
    settings["language"] = language_var.get()
    settings["file_policy"] = file_policy_var.get()
    save_settings(settings)

    download_button.configure(state="disabled")
    cancel_button.configure(state="normal")
    stop_event.clear()
    threading.Thread(target=start_processing, args=(url,)).start()

# Function to handle cancel button click
def on_cancel_button_click():
    stop_event.set()
    console_output("Cancelling download...", "info")
    cancel_button.configure(state="disabled")

# Start processing videos
def start_processing(url):
    asyncio.run(process_videos(
        url,
        [output_format_var.get().lower()],
        language_var.get(),
        save_directory_var.get(),
        console_output,
        update_recent_downloads,
        stop_event,
        file_policy_var.get(),
        progress_bar.set
    ))
    download_button.configure(state="normal")
    cancel_button.configure(state="disabled")

# Initialize UI components
input_frame = ctk.CTkFrame(root)
input_frame.pack(pady=10, padx=10, fill="x")

url_label = ctk.CTkLabel(input_frame, text="YouTube URL:")
url_label.grid(row=0, column=0, padx=5, pady=5)

url_entry = ctk.CTkEntry(input_frame, width=400)
url_entry.grid(row=0, column=1, padx=5, pady=5)

paste_button = ctk.CTkButton(input_frame, text="Paste", command=lambda: paste_from_clipboard(root, url_entry, console_output))
paste_button.grid(row=0, column=2, padx=5, pady=5)

download_button = ctk.CTkButton(input_frame, text="Download", command=on_download_button_click)
download_button.grid(row=0, column=3, padx=5, pady=5)

cancel_button = ctk.CTkButton(input_frame, text="Cancel", command=on_cancel_button_click, state="disabled")
cancel_button.grid(row=0, column=4, padx=5, pady=5)

# Format Controls
format_frame = ctk.CTkFrame(root)
format_frame.pack(pady=10, padx=10, fill="x")

output_format_dropdown = ctk.CTkOptionMenu(format_frame, variable=output_format_var, values=["TXT", "JSON", "SRT", "VTT"])
output_format_dropdown.grid(row=0, column=0, padx=5, pady=5)

language_dropdown = ctk.CTkOptionMenu(format_frame, variable=language_var, values=["en", "de", "fr", "es", "it", "pt"])
language_dropdown.grid(row=0, column=1, padx=5, pady=5)

save_dir_button = ctk.CTkButton(format_frame, text="Select Save Directory", command=select_save_directory)
save_dir_button.grid(row=0, column=2, padx=5, pady=5)

# Recent Downloads
recent_frame = ctk.CTkFrame(root)
recent_frame.pack(side="left", fill="y", padx=10, pady=10)

recent_listbox = ctk.CTkTextbox(recent_frame, width=200, height=400)
recent_listbox.pack(padx=5, pady=5)

clear_button = ctk.CTkButton(recent_frame, text="Clear", command=clear_recent_downloads)
clear_button.pack(pady=5)

# Console Output
console_frame = ctk.CTkFrame(root)
console_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

console_text = ctk.CTkTextbox(console_frame, wrap="word")
console_text.pack(fill="both", expand=True, padx=5, pady=5)

# Progress Bar
progress_bar = ctk.CTkProgressBar(root, orientation="horizontal")
progress_bar.pack(fill="x", padx=10, pady=10)

# Status Bar
status_var = ctk.StringVar()
status_bar = ctk.CTkLabel(root, textvariable=status_var, anchor="w")
status_bar.pack(fill="x", padx=10, pady=5)

# Apply theme based on saved setting
if settings.get("dark_mode", False):
    toggle_theme()

# Start the Tkinter event loop
root.mainloop()
