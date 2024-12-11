# main.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import asyncio
import os
import subprocess
import sys

from utils import (
    load_recent_downloads,
    save_recent_downloads,
    load_settings,
    save_settings,
)
from transcript_fetcher import process_videos

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
# Initialize the main window
root = tk.Tk()
root.title("YouTube Transcript Downloader")
root.geometry("900x600")
root.iconbitmap(resource_path("icon.ico" if sys.platform.startswith("win") else "icon.ico"))

# Load settings
settings = load_settings()
dark_mode = settings.get("dark_mode", False)



# Variables to store settings with defaults
save_directory_var = tk.StringVar(
    value=settings.get("save_directory", os.path.join(os.getcwd(), "downloads"))
)
recent_downloads = load_recent_downloads()

# Theme variable
dark_mode = False

# Function to toggle between dark and light themes
def toggle_theme():
    global dark_mode
    if not globals().get("recent_frame"):  # Check if UI elements are initialized
        return
    dark_mode = not dark_mode
    settings["dark_mode"] = dark_mode  # Save to settings
    save_settings(settings)  # Update settings.json

    # Create a ttk.Style instance for comboboxes
    style = ttk.Style()

    if dark_mode:
        # Set dark mode colors
        root.configure(bg="#2e2e2e")
        recent_frame.configure(bg="#2e2e2e")
        input_frame.configure(bg="#2e2e2e")
        format_frame.configure(bg="#2e2e2e")
        console_frame.configure(bg="#2e2e2e")
        console_text.configure(bg="#1e1e1e", fg="white", insertbackground="white")
        console_text.tag_configure("info", foreground="white")  # Normal text in white
        console_text.tag_configure("error", foreground="red")   # Errors in red
        console_text.tag_configure("success", foreground="lightgreen")  # Success messages
        recent_label.configure(bg="#2e2e2e", fg="white")
        status_bar.configure(bg="#2e2e2e", fg="white")
        console_text.configure(bg="#1e1e1e", fg="white", insertbackground="white")  # Ensure cursor is visible
        recent_listbox.configure(bg="#1e1e1e", fg="white")
        clear_button.configure(bg="#3a3a3a", fg="white")
        theme_button.configure(bg="#3a3a3a", fg="white")
        url_label.configure(bg="#2e2e2e", fg="white")
        format_label.configure(bg="#2e2e2e", fg="white")
        language_label.configure(bg="#2e2e2e", fg="white")
        file_handling_label.configure(bg="#2e2e2e", fg="white")
        download_button.configure(bg="#3a3a3a", fg="white")
        cancel_button.configure(bg="#3a3a3a", fg="white")
        clear_console_button.configure(bg="#3a3a3a", fg="white")
        save_dir_button.configure(bg="#3a3a3a", fg="white")

        # Style ttk.Combobox for dark mode
        style.theme_use("default")
        style.map(
        "TCombobox",
        fieldbackground=[("readonly", "#3a3a3a")],  # Darker gray for better contrast
        background=[("readonly", "#2e2e2e")],  # Dropdown menu background
        foreground=[("readonly", "white")],  # Default text color when not selected
    )
    else:
        # Reset to light mode colors
        root.configure(bg="SystemButtonFace")
        recent_frame.configure(bg="SystemButtonFace")
        recent_label.configure(bg="SystemButtonFace", fg="black")
        input_frame.configure(bg="SystemButtonFace")
        format_frame.configure(bg="SystemButtonFace")
        console_frame.configure(bg="SystemButtonFace")
        status_bar.configure(bg="SystemButtonFace", fg="black")
        console_text.configure(bg="white", fg="black", insertbackground="black")
        console_text.configure(bg="white", fg="black", insertbackground="black")
        console_text.tag_configure("info", foreground="black")  # Normal text in black
        console_text.tag_configure("error", foreground="red")   # Errors in red
        console_text.tag_configure("success", foreground="green")  # Success messages
        recent_listbox.configure(bg="white", fg="black")
        clear_button.configure(bg="SystemButtonFace", fg="black")
        theme_button.configure(bg="SystemButtonFace", fg="black")
        url_label.configure(bg="SystemButtonFace", fg="black")
        format_label.configure(bg="SystemButtonFace", fg="black")
        language_label.configure(bg="SystemButtonFace", fg="black")
        file_handling_label.configure(bg="SystemButtonFace", fg="black")
        download_button.configure(bg="SystemButtonFace", fg="black")
        cancel_button.configure(bg="SystemButtonFace", fg="black")
        clear_console_button.configure(bg="SystemButtonFace", fg="black")
        save_dir_button.configure(bg="SystemButtonFace", fg="black")

        # Reset ttk.Combobox styling for light mode
        style.theme_use("default")
        style.map(
        "TCombobox",
        fieldbackground=[("readonly", "white")],
        background=[("readonly", "SystemButtonFace")],
        foreground=[("readonly", "black")],
    )


# Output Formats
output_formats = ["TXT", "JSON", "SRT", "VTT"]
output_format_default = settings.get("output_format", "TXT")
output_format_var = tk.StringVar(value=output_format_default)

# Apply theme at startup
if dark_mode:
    toggle_theme()  # Set the UI to dark mode

# Language Selection
language_var = tk.StringVar(value=settings.get("language", "en"))

# File Handling Policy
file_policy_var = tk.StringVar(value=settings.get("file_policy", "skip"))

# Function to select the save directory
def select_save_directory():
    directory = filedialog.askdirectory()
    if directory:
        save_directory_var.set(directory)
        settings["save_directory"] = directory
        save_settings(settings)
        console_output(f"Save directory set to: {directory}", "info")



# Function to update recent downloads list
def update_recent_downloads(title, url, file_path):
    global recent_downloads
    # Add new entry
    recent_downloads.insert(0, {'title': title, 'url': url, 'file_path': file_path})
    # Keep only the last 10 entries
    recent_downloads = recent_downloads[:10]
    # Save the updated list
    save_recent_downloads(recent_downloads)
    # Update the listbox
    recent_listbox.delete(0, tk.END)
    max_length = 100  # Change this value if needed
    for item in recent_downloads:
        display_title = item['title']
        if len(display_title) > max_length:
            display_title = display_title[:max_length - 3] + '...'
        recent_listbox.insert(tk.END, display_title)

# Function to clear recent downloads
def clear_recent_downloads():
    global recent_downloads
    recent_downloads = []
    save_recent_downloads(recent_downloads)
    recent_listbox.delete(0, tk.END)
    console_output("Recent downloads cleared.", "info")
# Save pane position
def save_pane_position(event):
    settings["pane_position"] = pane_window.sash_coord(0)[0]
    save_settings(settings)

# Function to clear the console output
def clear_console():
    console_text.configure(state='normal')
    console_text.delete('1.0', tk.END)
    console_text.configure(state='disabled')
    update_clear_console_button()

# Function to handle recent item double-click
def on_recent_item_double_click(event):
    selection = recent_listbox.curselection()
    if selection:
        index = selection[0]
        file_path = recent_downloads[index].get('file_path', '')
        if file_path and os.path.exists(file_path):
            try:
                if sys.platform.startswith('darwin'):
                    subprocess.call(('open', file_path))
                elif os.name == 'nt':
                    os.startfile(file_path)
                elif os.name == 'posix':
                    subprocess.call(('xdg-open', file_path))
                console_output(f"Opened file: {file_path}", "info")
            except Exception as e:
                console_output(f"Failed to open file: {e}", "error")
        else:
            console_output("File does not exist.", "error")

# Function to output messages to the console and update status bar with color
def console_output(message, msg_type="info"):
    console_text.configure(state='normal')
    if msg_type == "error":
        console_text.insert(tk.END, message + '\n', 'error')
    elif msg_type == "success":
        console_text.insert(tk.END, message + '\n', 'success')
    else:
        console_text.insert(tk.END, message + '\n', 'info')
    console_text.configure(state='disabled')
    console_text.see(tk.END)
    # Update the status bar with the latest message
    status_var.set(message)
    update_clear_console_button()

    # Icon handling code
    try:
        root.iconbitmap(default=os.path.join(os.getcwd(), "icon.ico"))
        root.iconbitmap(default=os.path.join(os.getcwd(), "icon_16.ico"))
    except Exception as e:
        console_output(f"Failed to load icon: {e}", "error")

# Function to update the state of the "Clear Console" button
def update_clear_console_button():
    content = console_text.get('1.0', tk.END).strip()
    if content:
        clear_console_button.config(state='normal')
    else:
        clear_console_button.config(state='disabled')

# Configure tags for colored text in the console
def configure_console_tags():
    console_text.tag_config('error', foreground='red')
    console_text.tag_config('success', foreground='green')
    console_text.tag_config('info', foreground='black')

# Add a global stop event
stop_event = threading.Event()

# Function to handle download button click
def on_download_button_click():
    url = url_entry.get().strip()
    if not url:
        console_output("Please enter a YouTube video or playlist URL.", "error")
        return

    selected_format = output_format_var.get()
    if not selected_format:
        console_output("Please select an output format.", "error")
        return

    download_button.config(state='disabled')
    cancel_button.config(state='normal')
    progress_bar['value'] = 0
    progress_bar.pack(pady=(10, 0))
    stop_event.clear()
    threading.Thread(target=start_processing, args=(url,)).start()

# Function to handle cancel button click
def on_cancel_button_click():
    stop_event.set()
    console_output("Cancelling download...", "info")
    cancel_button.config(state='disabled')

# Function to start processing videos
def start_processing(url):
    selected_format = output_format_var.get()
    output_formats_selected = [selected_format.lower()]
    language = language_var.get()
    save_directory = save_directory_var.get()
    file_policy = file_policy_var.get()

    # Save current settings
    settings["output_format"] = selected_format
    settings["language"] = language
    settings["file_policy"] = file_policy
    save_settings(settings)

    # Run the async process_videos function
    asyncio.run(process_videos(
        url,
        output_formats_selected,
        language,
        save_directory,
        console_output_wrapper,
        update_recent_downloads_wrapper,
        stop_event,
        file_policy,
        progress_bar_wrapper
    ))

    download_button.config(state='normal')
    cancel_button.config(state='disabled')
    progress_bar.pack_forget()

# Wrapper for console_output to ensure thread-safe GUI updates
def console_output_wrapper(message, msg_type="info"):
    root.after(0, lambda: console_output(message, msg_type))

# Wrapper for update_recent_downloads to include file_path
def update_recent_downloads_wrapper(title, url, file_path):
    root.after(0, lambda: update_recent_downloads(title, url, file_path))

# Wrapper for progress_bar to update its value
def progress_bar_wrapper(current, total):
    if total > 0:
        progress = (current / total) * 100
        progress_bar['value'] = progress
        progress_bar.update_idletasks()

# =======================
# Layout Configuration
# =======================
# Create a PanedWindow for resizable panes
pane_window = tk.PanedWindow(root, orient=tk.HORIZONTAL)
pane_window.pack(fill=tk.BOTH, expand=True)
pane_window.bind("<ButtonRelease-1>", save_pane_position)

# Left Pane: Recent Downloads
recent_frame = tk.Frame(pane_window, width=200)
recent_label = tk.Label(recent_frame, text="Recent Downloads")
recent_label.pack()

# Restore pane position
saved_position = settings.get("pane_position", None)

def restore_pane_position():
    # Wait until the main loop initializes the pane
    root.update_idletasks()  # Ensures window and layout are fully initialized
    window_width = root.winfo_width()
    try:
        if saved_position is not None and isinstance(saved_position, (int, float)) and 0 <= saved_position <= window_width:
            pane_window.sash_place(0, int(saved_position), 0)
        else:
            # Default to a valid middle position
            pane_window.sash_place(0, window_width // 3, 0)
    except tk.TclError as e:
        print(f"Error restoring pane position: {e}")

# Call restore after everything is set up
root.after(100, restore_pane_position)


# Inner frame for Listbox and Scrollbar
listbox_frame = tk.Frame(recent_frame)
listbox_frame.pack(fill=tk.BOTH, expand=True)

recent_listbox = tk.Listbox(listbox_frame, width=30, height=15)
recent_listbox.grid(row=0, column=0, sticky='nsew')
recent_listbox.bind('<Double-Button-1>', on_recent_item_double_click)

recent_scrollbar = tk.Scrollbar(listbox_frame, command=recent_listbox.yview)
recent_scrollbar.grid(row=0, column=1, sticky='ns')
recent_listbox.config(yscrollcommand=recent_scrollbar.set)

# Configure grid weights to make Listbox expandable
listbox_frame.grid_rowconfigure(0, weight=1)
listbox_frame.grid_columnconfigure(0, weight=1)

# Clear Button in recent frame
clear_button = tk.Button(recent_frame, text="Clear", command=clear_recent_downloads)
clear_button.pack(pady=5)

pane_window.add(recent_frame)

# Center Pane: Input and Controls
input_frame = tk.Frame(root)
input_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

# Dark mode toggle button
theme_button = tk.Button(input_frame, text="Toggle Dark Mode", command=toggle_theme)
theme_button.grid(row=0, column=4, padx=(20, 0))

# URL Entry
url_label = tk.Label(input_frame, text="YouTube URL:")
url_label.grid(row=0, column=0, sticky='e')
url_entry = tk.Entry(input_frame, width=50)
url_entry.grid(row=0, column=1, padx=5)

# Download Button
download_button = tk.Button(input_frame, text="Download Transcript", command=on_download_button_click)
download_button.grid(row=0, column=2, padx=5)

# Cancel Button
cancel_button = tk.Button(input_frame, text="Cancel", command=on_cancel_button_click, state='disabled')
cancel_button.grid(row=0, column=3, padx=5)

# Format Selection
format_frame = tk.Frame(root)
format_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0, 10))

# Output Formats Dropdown
format_label = tk.Label(format_frame, text="Select Output Format:")
format_label.grid(row=0, column=0, sticky='w')

output_format_dropdown = ttk.Combobox(format_frame, textvariable=output_format_var, width=10, state='readonly')
output_format_dropdown['values'] = output_formats
output_format_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky='w')

# Language Selection
language_label = tk.Label(format_frame, text="Select Language:")
language_label.grid(row=0, column=2, padx=(20, 0))

language_dropdown = ttk.Combobox(format_frame, textvariable=language_var, width=5, state='readonly')
language_dropdown['values'] = ('en', 'de', 'fr', 'es', 'it', 'pt', 'nl', 'ru', 'zh', 'ja')  # Add more as needed
language_dropdown.grid(row=0, column=3)

# Save Directory Selection
save_dir_button = tk.Button(format_frame, text="Select Save Directory", command=select_save_directory)
save_dir_button.grid(row=0, column=4, padx=(20, 0))

# Clear Console Button
clear_console_button = tk.Button(format_frame, text="Clear Console", command=clear_console, state='disabled')
clear_console_button.grid(row=0, column=5, padx=(10, 0))

# File Handling Options as Dropdown
file_handling_label = tk.Label(format_frame, text="If File Exists:")
file_handling_label.grid(row=1, column=0, sticky='w', pady=(10, 0))

file_handling_dropdown = ttk.Combobox(format_frame, textvariable=file_policy_var, width=15, state='readonly')
file_handling_dropdown['values'] = ('Skip', 'Overwrite', 'Append Number')
file_handling_dropdown.grid(row=1, column=1, columnspan=2, sticky='w', pady=(10, 0))

# Progress Bar
progress_bar = ttk.Progressbar(root, orient='horizontal', mode='determinate', length=400)
# Initially hidden; packed when download starts

# Console Output
console_frame = tk.Frame(pane_window)
console_text = tk.Text(console_frame, state='disabled', height=15)
console_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)


# Configure colored tags
configure_console_tags()

# Scrollbar for the console
console_scrollbar = tk.Scrollbar(console_frame, command=console_text.yview)
console_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
console_text.config(yscrollcommand=console_scrollbar.set)

pane_window.add(console_frame)

# Status Bar at the bottom
status_var = tk.StringVar()
status_bar = tk.Label(root, textvariable=status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
status_bar.pack(side=tk.BOTTOM, fill=tk.X)

# Populate the recent downloads list initially
max_length = 100  # Change this value if needed
for item in recent_downloads:
    display_title = item['title']
    if len(display_title) > max_length:
        display_title = display_title[:max_length - 3] + '...'
    recent_listbox.insert(tk.END, display_title)

# Apply theme based on saved setting
if settings.get("dark_mode", False):
    toggle_theme()

# Start the Tkinter event loop
root.mainloop()
