# transcript_fetcher.py

import os
import urllib.parse
import re
import textwrap
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
    TextFormatter,
    SRTFormatter,
    WebVTTFormatter
)
from utils import clean_filename

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
    try:
        yt = YouTube(video_url)
        video_id = yt.video_id
        video_title = yt.title
        console_output(f"Fetching transcript for: {video_title}", "info")

        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript([language])
        transcript_data = transcript.fetch()

        filename = clean_filename(video_title)
        processed = False  # Flag to track if the video was actually processed

        # Save in the selected format
        selected_format = output_formats[0]  # Only one format selected
        if selected_format == "txt":
            file_saved, file_path = save_transcript_as_txt(transcript_data, filename, save_directory, file_policy)
        elif selected_format == "json":
            file_saved, file_path = save_transcript_as_json(transcript_data, filename, save_directory, file_policy)
        elif selected_format == "srt":
            file_saved, file_path = save_transcript_as_srt(transcript_data, filename, save_directory, file_policy)
        elif selected_format == "vtt":
            file_saved, file_path = save_transcript_as_vtt(transcript_data, filename, save_directory, file_policy)
        else:
            console_output(f"Unsupported format selected: {selected_format}", "error")
            file_saved = False
            file_path = ""

        if file_saved:
            update_recent_downloads(video_title, video_url, file_path)
            console_output(f"Successfully processed: {video_title}", "success")
        else:
            console_output(f"Skipped: {video_title} (file already exists)", "info")
    except (TranscriptsDisabled, NoTranscriptFound, NoTranscriptAvailable) as e:
        console_output(f"Transcript not available for {video_url}: {e}", "error")
    except Exception as e:
        console_output(f"Could not process {video_url}: {e}", "error")

def save_transcript_as_txt(transcript_data, filename, save_directory, file_policy):
    os.makedirs(save_directory, exist_ok=True)
    file_path = os.path.join(save_directory, f"{filename}.txt")
    
    # Handle file policy
    file_path = handle_file_policy(file_path, file_policy, filename, 'txt')
    if not file_path:
        return False, ""

    # Concatenate all transcript texts into a single paragraph
    transcript_text = " ".join([entry['text'].replace('\n', ' ') for entry in transcript_data])

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(transcript_text)

    return True, file_path

def save_transcript_as_json(transcript_data, filename, save_directory, file_policy):
    os.makedirs(save_directory, exist_ok=True)
    file_path = os.path.join(save_directory, f"{filename}.json")
    
    # Handle file policy
    file_path = handle_file_policy(file_path, file_policy, filename, 'json')
    if not file_path:
        return False, ""

    # Save the transcript using JSONFormatter
    formatter = JSONFormatter()
    formatted_json = formatter.format_transcript(transcript_data)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(formatted_json)

    return True, file_path

def save_transcript_as_srt(transcript_data, filename, save_directory, file_policy):
    os.makedirs(save_directory, exist_ok=True)
    file_path = os.path.join(save_directory, f"{filename}.srt")
    
    # Handle file policy
    file_path = handle_file_policy(file_path, file_policy, filename, 'srt')
    if not file_path:
        return False, ""

    # Save the transcript using SRTFormatter
    formatter = SRTFormatter()
    formatted_srt = formatter.format_transcript(transcript_data)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(formatted_srt)

    return True, file_path

def save_transcript_as_vtt(transcript_data, filename, save_directory, file_policy):
    os.makedirs(save_directory, exist_ok=True)
    file_path = os.path.join(save_directory, f"{filename}.vtt")
    
    # Handle file policy
    file_path = handle_file_policy(file_path, file_policy, filename, 'vtt')
    if not file_path:
        return False, ""

    # Save the transcript using WebVTTFormatter
    formatter = WebVTTFormatter()
    formatted_vtt = formatter.format_transcript(transcript_data)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(formatted_vtt)

    return True, file_path

def handle_file_policy(file_path, policy, filename, extension):
    if policy.lower() == 'skip' and os.path.exists(file_path):
        return None
    elif policy.lower() == 'overwrite':
        return file_path
    elif policy.lower() == 'append number':
        counter = 1
        new_file_path = file_path
        while os.path.exists(new_file_path):
            new_file_path = os.path.join(os.path.dirname(file_path), f"{filename}_{counter}.{extension}")
            counter += 1
        return new_file_path
    else:
        return file_path  # Default to overwrite if policy is unrecognized