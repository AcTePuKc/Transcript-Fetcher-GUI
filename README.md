# 💬⬇️ Transcript Fetcher GUI ⬇️💬

A simple tool to fetch YouTube transcripts.

## Features
- Fetch transcripts from YouTube videos
- Simple UI for seamless user interaction
- Supports **Single Videos and Playlists**
- Any Language YouTube supports

## Installation

1. Clone this repository:

```bash
git clone https://github.com/AcTePuKc/Transcript-Fetcher-GUI/
cd Transcript-Fetcher-GUI/
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the main script to open the interface:

```bash
python main.py
```

2. Follow the on-screen instructions to fetch transcripts:
   - By default, transcripts will be saved in the `downloads` folder located inside the project directory.
   - To change the save directory, click the **"Select Folder"** button and choose a different folder before downloading.

3. Paste the video URL in the **"YouTube URL:"** Text Box.

3. Click **"Download Transcript"** to fetch and save the transcript of the specified YouTube video.

## OTHER STUFF
1. To add/remove language - change this code in `main.py`
```bash
language_dropdown['values'] = ('en', 'de', 'fr', 'es', 'it', 'pt', 'nl', 'ru', 'zh', 'ja')  # Add/remove if needed
```
## Requirements

- `pytubefix`
- `youtube-transcript-api`

Make sure you have Python 3.6+ installed before installing these dependencies.

## Credits

This project uses the [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api/) created by [jdepoix](https://github.com/jdepoix). Special thanks for providing such a valuable tool to interact with YouTube’s transcript feature programmatically.

## To-Do
1. Localization [Doubt that]
