# main.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tktooltip import ToolTip
import threading
import asyncio
import os

from utils import (
    load_recent_downloads,
    save_recent_downloads,
    load_settings,
    save_settings,
)

from transcript_fetcher import process_videos

# Initialize the main window
root = tk.Tk()
root.title("YouTube Transcript Downloader")
root.geometry("900x600")

# Load settings
settings = load_settings()

# Variables to store settings
save_directory_var = tk.StringVar(
    value=settings.get("save_directory", os.path.join(os.getcwd(), "downloads"))
)
recent_downloads = load_recent_downloads()

# Function to select the save directory
def select_save_directory():
    directory = filedialog.askdirectory()
    if directory:
        save_directory_var.set(directory)
        settings["save_directory"] = directory
        save_settings(settings)
        console_output(f"Save directory set to: {directory}")

# Function to update recent downloads list
def update_recent_downloads(title, url):
    global recent_downloads
    # Add new entry
    recent_downloads.insert(0, {'title': title, 'url': url})
    # Keep only the last 10 entries
    recent_downloads = recent_downloads[:100]
    # Save the updated list
    save_recent_downloads(recent_downloads)
    # Update the listbox
    recent_listbox.delete(0, tk.END)
    for idx, item in enumerate(recent_downloads):
        display_title = item['title']
        if len(display_title) > 50:
            display_title = display_title[:47] + '...'
        recent_listbox.insert(tk.END, display_title)

# Function to clear recent downloads
def clear_recent_downloads():
    global recent_downloads
    recent_downloads = []
    save_recent_downloads(recent_downloads)
    recent_listbox.delete(0, tk.END)
    console_output("Recent downloads cleared.")

# Function to clear the console output
def clear_console():
    console_text.configure(state='normal')
    console_text.delete('1.0', tk.END)
    console_text.configure(state='disabled')

# Function to handle recent item clicks
def on_recent_item_click(event):
    selection = recent_listbox.curselection()
    if selection:
        index = selection[0]
        url = recent_downloads[index]['url']
        root.clipboard_clear()
        root.clipboard_append(url)
        messagebox.showinfo("Copied to Clipboard", f"URL copied to clipboard:\n{url}")

# Function to output messages to the console and update status bar
def console_output(message):
    console_text.configure(state='normal')
    console_text.insert(tk.END, message + '\n')
    console_text.configure(state='disabled')
    console_text.see(tk.END)
    # Update the status bar
    status_var.set(message)

# Add a global stop event
stop_event = threading.Event()

# Function to handle download button click
def on_download_button_click():
    url = url_entry.get().strip()
    if not url:
        console_output("Please enter a YouTube video or playlist URL.")
        return

    download_button.config(state='disabled')
    cancel_button.config(state='normal')
    stop_event.clear()
    threading.Thread(target=start_processing, args=(url,)).start()

# Function to handle cancel button click
def on_cancel_button_click():
    stop_event.set()
    console_output("Cancelling download...")
    cancel_button.config(state='disabled')

# Function to start processing videos
def start_processing(url):
    output_formats = []
    if txt_var.get():
        output_formats.append('txt')
    if json_var.get():
        output_formats.append('json')
    language = language_var.get()
    save_directory = save_directory_var.get()
    file_policy = file_handling_var.get()

    asyncio.run(process_videos(
        url,
        output_formats,
        language,
        save_directory,
        console_output,
        update_recent_downloads,
        stop_event,
        file_policy
    ))

    download_button.config(state='normal')
    cancel_button.config(state='disabled')
# Function to update tooltip text based on mouse position
def on_listbox_motion(event):
    # Get the index of the item under the mouse
    index = recent_listbox.nearest(event.y)

    # Ensure the index is valid and corresponds to an actual item
    if 0 <= index < recent_listbox.size():
        # Fetch the text of the item at this index
        item = recent_listbox.get(index)
        
        # Only show tooltip if there is text in the item
        if item:
            listbox_tooltip.msg = recent_downloads[index]['title']
        else:
            # Clear tooltip if the item is empty
            listbox_tooltip.msg = ''
    else:
        # Clear tooltip if the index is invalid
        listbox_tooltip.msg = ''

# Left Pane: Recent Downloads
recent_frame = tk.Frame(root, width=200)
recent_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

recent_label = tk.Label(recent_frame, text="Recent Downloads")
recent_label.pack()

# Recent Downloads Listbox
recent_listbox = tk.Listbox(recent_frame, width=30, height=15)
recent_listbox.pack(fill=tk.BOTH, expand=True)
recent_listbox.bind('<ButtonRelease-1>', on_recent_item_click)

# Scrollbar for the recent downloads list
recent_scrollbar = tk.Scrollbar(recent_frame, command=recent_listbox.yview)
recent_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
recent_listbox.config(yscrollcommand=recent_scrollbar.set)

# Create a tooltip for the recent downloads Listbox
listbox_tooltip = ToolTip(recent_listbox, msg='', delay=0.1, follow=True)

# Bind the motion event to the Listbox
recent_listbox.bind('<Motion>', on_listbox_motion)

# Ensure tooltip is hidden when leaving the Listbox area
def on_listbox_leave(event):
    listbox_tooltip.msg = ''  # Clear the tooltip message when leaving the Listbox area

# Bind the leave event to ensure tooltip is cleared on exit
recent_listbox.bind('<Leave>', on_listbox_leave)

# Clear Button in recent frame
clear_button = tk.Button(recent_frame, text="Clear", command=clear_recent_downloads)
clear_button.pack(pady=5)

# Center Pane: Input and Controls
input_frame = tk.Frame(root)
input_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

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

format_label = tk.Label(format_frame, text="Select Output Formats:")
format_label.grid(row=0, column=0, sticky='w')

txt_var = tk.BooleanVar(value=True)
txt_checkbox = tk.Checkbutton(format_frame, text="TXT", variable=txt_var)
txt_checkbox.grid(row=0, column=1)

json_var = tk.BooleanVar(value=False)
json_checkbox = tk.Checkbutton(format_frame, text="JSON", variable=json_var)
json_checkbox.grid(row=0, column=2)

# Language Selection
language_label = tk.Label(format_frame, text="Select Language:")
language_label.grid(row=0, column=3, padx=(20, 0))

language_var = tk.StringVar(value='en')
language_dropdown = ttk.Combobox(format_frame, textvariable=language_var, width=5)
language_dropdown['values'] = ('en', 'de', 'fr', 'es', 'it', 'pt', 'nl', 'ru', 'zh', 'ja')  # Add more as needed
language_dropdown.grid(row=0, column=4)

# Save Directory Selection
save_dir_button = tk.Button(format_frame, text="Select Save Directory", command=select_save_directory)
save_dir_button.grid(row=0, column=5, padx=(20, 0))

# Clear Console Button
clear_console_button = tk.Button(format_frame, text="Clear Console", command=clear_console)
clear_console_button.grid(row=0, column=6, padx=(10, 0))

# File Handling Options
file_handling_label = tk.Label(format_frame, text="If File Exists:")
file_handling_label.grid(row=1, column=0, sticky='w', pady=(10, 0))

file_handling_var = tk.StringVar(value='skip')

skip_radio = tk.Radiobutton(format_frame, text="Skip", variable=file_handling_var, value='skip') 
skip_radio.grid(row=1, column=1, sticky='w', pady=(10, 0))


overwrite_radio = tk.Radiobutton(format_frame, text="Overwrite", variable=file_handling_var, value='overwrite')
overwrite_radio.grid(row=1, column=2, sticky='w', pady=(10, 0)) 

append_radio = tk.Radiobutton(format_frame, text="Append Number", variable=file_handling_var, value='append')
append_radio.grid(row=1, column=3, sticky='w', pady=(10, 0))


# Console Output
console_frame = tk.Frame(root)
console_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=5, pady=5)

console_text = tk.Text(console_frame, state='disabled', height=15)
console_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Scrollbar for the console
console_scrollbar = tk.Scrollbar(console_frame, command=console_text.yview)
console_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
console_text.config(yscrollcommand=console_scrollbar.set)

# Status Bar at the bottom
status_var = tk.StringVar()
status_bar = tk.Label(root, textvariable=status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
status_bar.pack(side=tk.BOTTOM, fill=tk.X)

# Start the Tkinter event loop
root.mainloop()
