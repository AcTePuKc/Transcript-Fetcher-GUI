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
    progress_bar_callback,
    translate=False  # Pass translation flag
):
    try:
        video_urls = []
        if is_playlist(url):
            try:
                playlist = Playlist(url)
                video_urls = playlist.video_urls  # Attempt to fetch video URLs
                if not video_urls:
                    raise Exception("Playlist is private or inaccessible.")
                console_output("Processing playlist...", "info")
            except Exception as e:
                console_output(f"Error accessing playlist: {e}", "error")
                return

        total_videos = len(video_urls)
        for idx, video_url in enumerate(video_urls, 1):
            if stop_event.is_set():
                console_output("Download cancelled by user.", "info")
                break
            await process_single_video(
            video_url,
            output_formats,
            language,
            save_directory,
            console_output,
            lambda title, url, file_path: update_recent_downloads(title, url, file_path, language),  # Pass update_recent_downloads
            stop_event,
            file_policy,
            translate=translate
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
    file_policy,
    translate=False
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

        if translate and language != "en":  # Translate only if requested and not English
            console_output(f"Translating transcript to {language}...", "info")
            transcript_data = transcript.translate(language).fetch()
        else:
            transcript_data = transcript.fetch()

        # Add language to filename if not English
        filename = clean_filename(f"{video_title}_{language}" if language != "en" else video_title)
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
            console_output(f"Successfully processed: {video_title} ({language})", "success")
        else:
            console_output(f"Skipped: {video_title} (file already exists)", "info")

    except (TranscriptsDisabled, NoTranscriptAvailable) as e:
        console_output(f"Transcript not available for {video_url}: {e}", "error")
    except NoTranscriptFound:
        console_output(f"No transcript found for {video_url} in {language}.", "error")
    except Exception as e:
        console_output(f"Could not process {video_url}: {e}", "error")
