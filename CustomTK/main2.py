import os
import customtkinter as ctk
from tkinter import StringVar
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled, NoTranscriptAvailable
from youtube_transcript_api.formatters import JSONFormatter, SRTFormatter, WebVTTFormatter

# Initialize CustomTkinter appearance
ctk.set_appearance_mode("System")  # Modes: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")

# Helper function to clean filenames
def clean_filename(title):
    return "".join(c if c.isalnum() or c in " .-_" else "_" for c in title)

# Helper function to save the transcript
def save_transcript(transcript_data, title, directory, file_policy, extension, formatter=None):
    file_path = os.path.join(directory, f"{title}.{extension}")

    # Handle file policy
    if os.path.exists(file_path):
        if file_policy.lower() == "skip":
            return False, file_path
        elif file_policy.lower() == "overwrite":
            pass  # Overwrite the file
        elif file_policy.lower() == "append number":
            base, ext = os.path.splitext(file_path)
            counter = 1
            while os.path.exists(file_path):
                file_path = f"{base} ({counter}){ext}"
                counter += 1

    # Save the transcript
    with open(file_path, "w", encoding="utf-8") as file:
        if formatter:
            file.write(formatter.format_transcript(transcript_data))
        else:
            file.write("\n".join([entry["text"] for entry in transcript_data]))

    return True, file_path

# Application Class
class TranscriptDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Transcript Downloader")
        self.geometry("1150x600")
        self.grid_rowconfigure(2, weight=1)  # Middle section expands vertically
        self.grid_columnconfigure(0, weight=1)  # Center alignment

        # Variables
        self.output_format_var = StringVar(value="TXT")
        self.language_var = StringVar(value="en")
        self.file_policy_var = StringVar(value="Skip")

        # =======================
        # Top Section: Input Controls
        # =======================
        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(input_frame, text="YouTube URL:").grid(row=0, column=0, padx=5, pady=5)
        self.url_entry = ctk.CTkEntry(input_frame, width=400)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5)

        paste_button = ctk.CTkButton(input_frame, text="Paste", command=self.paste_from_clipboard)
        paste_button.grid(row=0, column=2, padx=5)

        download_button = ctk.CTkButton(input_frame, text="Download", command=self.download_transcript)
        download_button.grid(row=0, column=3, padx=5)

        cancel_button = ctk.CTkButton(input_frame, text="Cancel", state="disabled")
        cancel_button.grid(row=0, column=4, padx=5)

        theme_button = ctk.CTkButton(input_frame, text="Toggle Dark Mode", command=self.toggle_theme)
        theme_button.grid(row=0, column=5, padx=5)

        # =======================
        # Middle Section: Format Controls
        # =======================
        format_frame = ctk.CTkFrame(self)
        format_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(format_frame, text="Select Output Format:").grid(row=0, column=0, padx=5, pady=5)
        format_dropdown = ctk.CTkOptionMenu(format_frame, variable=self.output_format_var, values=["TXT", "JSON", "SRT", "VTT"])
        format_dropdown.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(format_frame, text="Select Language:").grid(row=0, column=2, padx=5)
        language_dropdown = ctk.CTkOptionMenu(format_frame, variable=self.language_var, values=["en", "de", "fr", "es", "it", "pt", "nl", "ru", "zh", "ja"])
        language_dropdown.grid(row=0, column=3, padx=5)

        save_dir_button = ctk.CTkButton(format_frame, text="Select Save Directory", command=self.select_save_directory)
        save_dir_button.grid(row=0, column=4, padx=5)

        open_dir_button = ctk.CTkButton(format_frame, text="Open Save Directory", command=self.open_save_directory)
        open_dir_button.grid(row=0, column=5, padx=5)

        clear_console_button = ctk.CTkButton(format_frame, text="Clear Console", command=self.clear_console)
        clear_console_button.grid(row=0, column=6, padx=5)

        ctk.CTkLabel(format_frame, text="If File Exists:").grid(row=1, column=0, padx=5, pady=5)
        file_policy_dropdown = ctk.CTkOptionMenu(format_frame, variable=self.file_policy_var, values=["Skip", "Overwrite", "Append Number"])
        file_policy_dropdown.grid(row=1, column=1, padx=5, pady=5)

        # =======================
        # Center Section: Recent Downloads + Console
        # =======================
        pane_window = ctk.CTkFrame(self)
        pane_window.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        pane_window.grid_rowconfigure(0, weight=1)
        pane_window.grid_columnconfigure((0, 1), weight=1)

        # Recent Downloads
        recent_frame = ctk.CTkFrame(pane_window)
        recent_frame.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(recent_frame, text="Recent Downloads").pack(pady=5)

        self.recent_listbox = ctk.CTkTextbox(recent_frame, height=15)
        self.recent_listbox.pack(fill="both", expand=True)

        clear_button = ctk.CTkButton(recent_frame, text="Clear", command=self.clear_recent)
        clear_button.pack(pady=5)

        # Console Output
        console_frame = ctk.CTkFrame(pane_window)
        console_frame.grid(row=0, column=1, sticky="nsew")

        self.console_text = ctk.CTkTextbox(console_frame, height=15)
        self.console_text.pack(fill="both", expand=True)

        # =======================
        # Progress Bar
        # =======================
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.progress_bar.set(0)

        # =======================
        # Status Bar
        # =======================
        self.status_var = StringVar()
        status_bar = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w")
        status_bar.grid(row=4, column=0, sticky="ew")


    def paste_from_clipboard(self):
        self.url_entry.delete(0, ctk.END)
        self.url_entry.insert(0, self.clipboard_get())

    def download_transcript(self):
        pass

    def toggle_theme(self):
        current_mode = ctk.get_appearance_mode()
        new_mode = "Dark" if current_mode == "Light" else "Light"
        ctk.set_appearance_mode(new_mode)

    def select_save_directory(self):
        pass

    def open_save_directory(self):
        pass

    def clear_console(self):
        self.console_text.delete("1.0", ctk.END)

    def clear_recent(self):
        self.recent_listbox.delete("1.0", ctk.END)

if __name__ == "__main__":
    app = TranscriptDownloaderApp()
    app.mainloop()
