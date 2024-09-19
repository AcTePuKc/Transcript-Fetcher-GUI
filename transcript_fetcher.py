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
    file_policy
):
    try:
        video_urls = []
        if is_playlist(url):
            console_output("Processing playlist...")
            playlist = Playlist(url)
            video_urls = playlist.video_urls  # List of video URLs
        elif is_video(url):
            video_urls = [convert_short_url_to_full(url)]  # Convert if necessary
        else:
            console_output("Invalid URL. Please enter a valid YouTube video or playlist URL.")
            return

        total_videos = len(video_urls)
        for idx, video_url in enumerate(video_urls, 1):
            if stop_event.is_set():
                console_output("Download cancelled by user.")
                break
            console_output(f"Processing video {idx}/{total_videos}: {video_url}")
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
    except Exception as e:
        console_output(f"An error occurred: {e}")

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
        console_output(f"Fetching transcript for: {video_title}")

        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript([language])
        transcript_data = transcript.fetch()

        filename = clean_filename(video_title)
        processed = False  # Flag to track if the video was actually processed

        if "txt" in output_formats:
            if save_transcript_as_txt(transcript_data, filename, save_directory, file_policy):
                processed = True
        if "json" in output_formats:
            if save_transcript_as_json(transcript_data, filename, save_directory, file_policy):
                processed = True

        # Only update recent downloads if the video was actually processed
        if processed:
            update_recent_downloads(video_title, video_url)
            console_output(f"Successfully processed: {video_title}")
        else:
            console_output(f"Skipped: {video_title} (file already exists)")
    except (TranscriptsDisabled, NoTranscriptFound, NoTranscriptAvailable) as e:
        console_output(f"Transcript not available for {video_url}: {e}")
    except Exception as e:
        console_output(f"Could not process {video_url}: {e}")

def save_transcript_as_txt(transcript_data, filename, save_directory, file_policy):
    os.makedirs(save_directory, exist_ok=True)
    file_path = os.path.join(save_directory, f"{filename}.txt")
    
    # Skip if the file exists and the policy is 'skip'
    if file_policy == 'skip' and os.path.exists(file_path):
        return False

    # Handle append case
    if file_policy == 'append' and os.path.exists(file_path):
        counter = 1
        while os.path.exists(os.path.join(save_directory, f"{filename}_{counter}.txt")):
            counter += 1
        file_path = os.path.join(save_directory, f"{filename}_{counter}.txt")

    # Save the transcript
    text = ' '.join([entry['text'].strip() for entry in transcript_data])
    text = re.sub(r'\s+', ' ', text)
    wrapped_text = textwrap.fill(text, width=80, replace_whitespace=False)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(wrapped_text)

    return True


def save_transcript_as_json(transcript_data, filename, save_directory, file_policy):
    os.makedirs(save_directory, exist_ok=True)
    file_path = os.path.join(save_directory, f"{filename}.json")
    
    # Skip if the file exists and the policy is 'skip'
    if file_policy == 'skip' and os.path.exists(file_path):
        return False

    # Handle append case
    if file_policy == 'append' and os.path.exists(file_path):
        counter = 1
        while os.path.exists(os.path.join(save_directory, f"{filename}_{counter}.json")):
            counter += 1
        file_path = os.path.join(save_directory, f"{filename}_{counter}.json")

    # Save the transcript
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(transcript_data, f, ensure_ascii=False, indent=4)

    return True