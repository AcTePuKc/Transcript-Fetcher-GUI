# transcript_fetcher.py

import os
import urllib.parse
import re
import json
from pytubefix import YouTube, Playlist
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    NoTranscriptAvailable,
)
from youtube_transcript_api.formatters import (
    JSONFormatter,
    SRTFormatter,
    WebVTTFormatter
)
from utils import clean_filename

file_path = None  # Ensure file_path is always initialized

def on_download(self):
    video_url = self.url_input.text()
    if not video_url:
        self.console_output.append("Error: YouTube URL cannot be empty.")
        return

    self.console_output.append(f"Starting download for: {video_url}")
    self.progress_bar.setValue(0)

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
            lambda: False,  # Placeholder for stop event
            file_policy
        )
    except Exception as e:
        self.console_output.append(f"Error: {str(e)}")
    finally:
        self.progress_bar.setValue(100)


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

async def process_videos(
    url,
    output_formats,
    language,
    save_directory,
    console_output,
    update_recent_downloads,
    stop_event,
    file_policy,
    progress_bar_callback
):
    try:
        video_urls = []
        if is_playlist(url):
            console_output("Processing playlist...", "info")
            playlist = Playlist(url)
            video_urls = playlist.video_urls  # List of video URLs
        elif is_video(url):
            video_urls = [convert_short_url_to_full(url)]  # Convert if necessary
        else:
            console_output("Invalid URL. Please enter a valid YouTube video or playlist URL.", "error")
            return

        total_videos = len(video_urls)
        for idx, video_url in enumerate(video_urls, 1):
            if stop_event.is_set():
                console_output("Download cancelled by user.", "info")
                break
            console_output(f"Processing video {idx}/{total_videos}: {video_url}", "info")
            await process_single_video(
                video_url,
                output_formats,
                language,
                save_directory,
                console_output,
                update_recent_downloads,
                stop_event,
                file_policy
            )
            progress_bar_callback(idx, total_videos)
    except Exception as e:
        console_output(f"An error occurred: {e}", "error")

async def process_single_video(
    video_url,
    output_formats,
    language,
    save_directory,
    console_output,
    update_recent_downloads,
    stop_event,
    file_policy
):
    if stop_event.is_set():
        return
    file_path = None  # Ensure file_path is initialized
    try:
        yt = YouTube(video_url)
        video_id = yt.video_id
        video_title = yt.title
        console_output(f"Fetching transcript for: {video_title}", "info")

        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript([language])
        transcript_data = transcript.fetch()

        filename = clean_filename(video_title)
        selected_format = output_formats[0]

        # Save in the selected format
        if selected_format == "txt":
            file_saved, file_path = save_transcript(transcript_data, filename, save_directory, file_policy, "txt")
        elif selected_format == "json":
            file_saved, file_path = save_transcript(transcript_data, filename, save_directory, file_policy, "json", JSONFormatter())
        elif selected_format == "srt":
            file_saved, file_path = save_transcript(transcript_data, filename, save_directory, file_policy, "srt", SRTFormatter())
        elif selected_format == "vtt":
            file_saved, file_path = save_transcript(transcript_data, filename, save_directory, file_policy, "vtt", WebVTTFormatter())
        else:
            console_output(f"Unsupported format selected: {selected_format}", "error")
            return

        if file_saved:
            update_recent_downloads(video_title, video_url, file_path)
            console_output(f"Successfully processed: {video_title}", "success")
        else:
            console_output(f"Skipped: {video_title} (file already exists)", "info")

    except (TranscriptsDisabled, NoTranscriptAvailable) as e:
        console_output(f"Transcript not available for {video_url}: {e}", "error")
    except NoTranscriptFound:
        # Show all available transcript languages
        available_languages = (
            list(transcript_list._manually_created_transcripts.keys()) +
            list(transcript_list._generated_transcripts.keys())
        )
        if available_languages:
            console_output(
                f"Transcript not available for {video_url}: No transcripts were found for '{language}'.\n"
                "Available languages:\n" +
                "\n".join(f"- {lang}" for lang in available_languages),
                "error"
            )
        else:
            console_output(f"Transcript not available for {video_url}: No transcripts exist.", "error")
    except Exception as e:
        console_output(f"Could not process {video_url}: {e}", "error")

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

def handle_file_policy(file_path, policy, filename, extension):
    if policy.lower() == 'skip' and os.path.exists(file_path):
        return None
    if policy.lower() == 'append number':
        counter = 1
        while os.path.exists(file_path):
            file_path = os.path.join(os.path.dirname(file_path), f"{filename}_{counter}.{extension}")
            counter += 1
    return file_path  # Default to overwrite
