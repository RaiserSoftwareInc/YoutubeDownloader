import os
import sys
import subprocess
import platform
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QFileDialog, QMessageBox, QProgressBar, 
    QMainWindow, QStackedLayout
)
from PySide6.QtCore import Qt, QThread, Signal, QSettings
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

class DownloadPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        self.settings = QSettings("test", "YoutubeDownloaderApp")
        # Load last saved folder path
        last_folder = self.settings.value("last_folder", "")
        if last_folder:
            self.folder_entry.setText(last_folder)

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

        # --- Open Folder Button ---
        open_button = QPushButton("Open Folder")
        open_button.clicked.connect(self.open_folder)
        layout.addWidget(open_button)

        # --- Status Label ---
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_entry.setText(folder)
            self.settings.setValue("last_folder", folder)

    def open_folder(self):
        folder_path = self.folder_entry.text().strip()
        if not folder_path or not os.path.exists(folder_path):
            QMessageBox.warning(self, "Folder Not Found", "Please select a valid folder first.")
            return

        if platform.system() == "Windows":
            os.startfile(folder_path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", folder_path])
        else:  # Linux
            subprocess.run(["xdg-open", folder_path])


    def update_status(self, message: str):
        self.status_label.setText(message)

        # Show popup for errors
        if message.lower().startswith("error"):
            QMessageBox.warning(self, "Error", message)
    
    def update_progress(self, value: int):
        self.progress_bar.setValue(value)

    # Function to handle download button click event
    def download_video(self):
        youtube_link = self.link_entry.text().strip()
        folder_path = self.folder_entry.text().strip()
        mp3_choice = self.mp3_checkbox.isChecked()
        mp4_choice = self.mp4_checkbox.isChecked()

        if not youtube_link:
            QMessageBox.warning(self, "Missing Link", "Please enter a YouTube link.")
            return
        if not folder_path:
            QMessageBox.warning(self, "Missing Folder", "Please choose a folder.")
            return
        if not mp3_choice and not mp4_choice:
            QMessageBox.warning(self, "Format Required", "Select at least one format (MP3 or MP4).")
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
        self.settings.setValue("last_folder", folder_path)
        self.download_button.setEnabled(True)
        self.progress_bar.setValue(100)
        QMessageBox.information(self, "Download Complete", "Your download has finished successfully!")

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("test", "YoutubeDownloaderApp")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Default download folder
        folder_layout = QHBoxLayout()
        folder_label = QLabel("Default Download Folder:")
        self.folder_entry = QLineEdit()
        self.folder_entry.setText(self.settings.value("last_folder", ""))
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_folder)
        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.folder_entry)
        folder_layout.addWidget(browse_button)
        layout.addLayout(folder_layout)

        # Dark theme toggle
        self.dark_theme_checkbox = QCheckBox("Enable Dark Theme")
        self.dark_theme_checkbox.setChecked(
            self.settings.value("dark_theme", False, type=bool)
        )
        layout.addWidget(self.dark_theme_checkbox)

        # Save button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)
        layout.addStretch()

        self.setLayout(layout)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_entry.setText(folder)

    def save_settings(self):
        self.settings.setValue("last_folder", self.folder_entry.text())
        self.settings.setValue("dark_theme", self.dark_theme_checkbox.isChecked())
        QMessageBox.information(
            self, "Settings Saved", "Your settings have been saved successfully!"
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Downloader App")
        self.setMinimumSize(1080, 720)
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # --- Sidebar ---
        sidebar = QVBoxLayout()
        self.download_btn = QPushButton("Download")
        self.settings_btn = QPushButton("Settings")
        self.history_btn = QPushButton("History")
        sidebar.addWidget(self.download_btn)
        sidebar.addWidget(self.settings_btn)
        sidebar.addWidget(self.history_btn)
        sidebar.addStretch()

        # --- Pages ---
        self.stack = QStackedLayout()
        self.download_page = DownloadPage()
        self.settings_page = SettingsPage()
        self.history_page = QWidget()   # placeholder
        self.stack.addWidget(self.download_page)
        self.stack.addWidget(self.settings_page)
        self.stack.addWidget(self.history_page)

        main_layout.addLayout(sidebar)
        main_layout.addLayout(self.stack)

        # --- Connect sidebar ---
        self.download_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.download_page))
        self.settings_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.settings_page))
        self.history_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.history_page))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())