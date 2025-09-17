import os
import tkinter as tk
from tkinter import filedialog, messagebox
from pytubefix import YouTube  # ✅ updated import

# Function to handle download button click event
def download_video():
    try:
        youtube_link = link_entry.get().strip()
        folder_path = folder_entry.get().strip()

        if not youtube_link:
            update_status("Please enter a YouTube link")
            return
        if not folder_path:
            update_status("Please choose a folder")
            return

        mp3_choice = mp3_var.get()
        mp4_choice = mp4_var.get()

        if not mp3_choice and not mp4_choice:
            update_status("Select MP3 or MP4")
            return

        youtube = YouTube(youtube_link)

        audio_folder = os.path.join(folder_path, "audio")
        video_folder = os.path.join(folder_path, "video")

        if mp4_choice:
            os.makedirs(video_folder, exist_ok=True)
            stream = youtube.streams.get_highest_resolution()
            stream.download(output_path=video_folder)

        if mp3_choice:
            os.makedirs(audio_folder, exist_ok=True)
            stream = youtube.streams.get_audio_only()
            downloaded_file = stream.download(output_path=audio_folder)

            # Change extension to .mp3 (note: file is still AAC/WEBM unless converted)
            base, ext = os.path.splitext(downloaded_file)
            new_file = base + ".mp3"
            os.rename(downloaded_file, new_file)

        update_status("Download completed")

    except Exception as e:
        update_status(f"Error: {e}")

# Function to handle the context menu
def show_context_menu(event):
    context_menu.tk_popup(event.x_root, event.y_root)

# Function to handle paste button click event
def paste_from_clipboard():
    try:
        clipboard_text = window.clipboard_get()
        link_entry.delete(0, tk.END)
        link_entry.insert(tk.END, clipboard_text)
    except:
        pass

# Function to handle browse button click event
def browse_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        folder_entry.delete(0, tk.END)
        folder_entry.insert(0, folder_path)

# Create a new window
window = tk.Tk()
window.title("YouTube Downloader")
window.geometry("350x180")

# YouTube link
link_label = tk.Label(window, text="YouTube Link:")
link_label.grid(row=0, column=0, sticky="w")
link_entry = tk.Entry(window, width=30)
link_entry.grid(row=0, column=1, padx=5, pady=5)

# Folder path
folder_label = tk.Label(window, text="Folder Path:")
folder_label.grid(row=1, column=0, sticky="w")
folder_entry = tk.Entry(window, width=30)
folder_entry.grid(row=1, column=1, padx=5, pady=5)
browse_button = tk.Button(window, text="Browse", command=browse_folder)
browse_button.grid(row=1, column=2, padx=5, pady=5)

# Checkboxes
mp3_var = tk.IntVar()
mp3_checkbox = tk.Checkbutton(window, text="MP3", variable=mp3_var)
mp3_checkbox.grid(row=2, column=0)
mp4_var = tk.IntVar()
mp4_checkbox = tk.Checkbutton(window, text="MP4", variable=mp4_var)
mp4_checkbox.grid(row=2, column=1)

# Context menu
context_menu = tk.Menu(window, tearoff=0)
context_menu.add_command(label="Cut", command=lambda: link_entry.event_generate("<<Cut>>"))
context_menu.add_command(label="Copy", command=lambda: link_entry.event_generate("<<Copy>>"))
context_menu.add_separator()
context_menu.add_command(label="Paste", command=paste_from_clipboard)
window.bind("<Button-3>", show_context_menu)

# Download button
download_button = tk.Button(window, text="Download", command=download_video)
download_button.grid(row=3, column=0, columnspan=3, padx=5, pady=5)

# Status label
status_label = tk.Label(window, text="", fg="blue")
status_label.grid(row=4, column=0, columnspan=3, padx=5, pady=5)

def update_status(message):
    status_label.config(text=message)

# Run loop
window.mainloop()
