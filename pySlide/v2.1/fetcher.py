# transcript_fetcher.py

import os
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
from utils import (
    clean_filename,
    handle_file_policy,
    save_transcript,
    convert_short_url_to_full,
    is_playlist,
    is_video
)


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
            # console_output(f"Processing video {idx}/{total_videos}: {video_url}", "info") # <-- Removed redundant message
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