import os
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QFileDialog, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal
from pytubefix import YouTube  # ✅ updated import

class DownloadWorker(QThread):
    progress = Signal(int)
    status = Signal(str)
    done = Signal()

    def __init__(self, youtube_link, folder_path, mp3_choice, mp4_choice):
        super().__init__()
        self.youtube_link = youtube_link
        self.folder_path = folder_path
        self.mp3_choice = mp3_choice
        self.mp4_choice = mp4_choice

    def run(self):
        try:
            yt = YouTube(self.youtube_link, on_progress_callback=self.on_progress)
            self.status.emit("Fetching video info...")

            if self.mp4_choice:
                os.makedirs(os.path.join(self.folder_path, "video"), exist_ok=True)
                stream = yt.streams.get_highest_resolution()
                self.status.emit("Downloading video...")
                stream.download(output_path=os.path.join(self.folder_path, "video"))

            if self.mp3_choice:
                os.makedirs(os.path.join(self.folder_path, "audio"), exist_ok=True)
                stream = yt.streams.get_audio_only()
                self.status.emit("Downloading audio...")
                file = stream.download(output_path=os.path.join(self.folder_path, "audio"))
                base, _ = os.path.splitext(file)
                new_file = base + ".mp3"
                os.rename(file, new_file)

            self.status.emit("Download complete ✅")
            self.done.emit()

        except Exception as e:
            self.status.emit(f"Error: {e}")
            self.done.emit()

    def on_progress(self, stream, chunk, bytes_remaining):
        total = stream.filesize
        percent = int((total - bytes_remaining) / total * 100)
        self.progress.emit(percent)

class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Downloader (Qt Edition)")
        self.setMinimumSize(420, 250)
        self.init_ui()
        self.worker = None

    def init_ui(self):
        layout = QVBoxLayout()

        # --- YouTube Link ---
        link_layout = QHBoxLayout()
        link_label = QLabel("YouTube Link:")
        self.link_entry = QLineEdit()
        link_layout.addWidget(link_label)
        link_layout.addWidget(self.link_entry)
        layout.addLayout(link_layout)

        # --- Folder Selection ---
        folder_layout = QHBoxLayout()
        folder_label = QLabel("Save to:")
        self.folder_entry = QLineEdit()
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_folder)
        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.folder_entry)
        folder_layout.addWidget(browse_button)
        layout.addLayout(folder_layout)

        # --- Format Selection ---
        format_layout = QHBoxLayout()
        self.mp3_checkbox = QCheckBox("MP3")
        self.mp4_checkbox = QCheckBox("MP4")
        format_layout.addWidget(self.mp3_checkbox)
        format_layout.addWidget(self.mp4_checkbox)
        layout.addLayout(format_layout)

        # --- Progress Bar ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # --- Download Button ---
        self.download_button = QPushButton("Download")
        self.download_button.clicked.connect(self.download_video)
        layout.addWidget(self.download_button)

        # --- Status Label ---
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_entry.setText(folder)

    def update_status(self, message: str):
        self.status_label.setText(message)
    
    def update_progress(self, value: int):
        self.progress_bar.setValue(value)

    # Function to handle download button click event
    def download_video(self):
        youtube_link = self.link_entry.text().strip()
        folder_path = self.folder_entry.text().strip()
        mp3_choice = self.mp3_checkbox.isChecked()
        mp4_choice = self.mp4_checkbox.isChecked()

        if not youtube_link:
            self.update_status("Please enter a YouTube link")
            return
        if not folder_path:
            self.update_status("Please choose a folder")
            return
        if not mp3_choice and not mp4_choice:
            self.update_status("Select MP3 or MP4")
            return

        # Disable button during download
        self.download_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.update_status("Starting download...")

        self.worker = DownloadWorker(youtube_link, folder_path, mp3_choice, mp4_choice)
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.done.connect(self.on_download_complete)
        self.worker.start()
            
    def on_download_complete(self):
        self.download_button.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec())