import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QCheckBox, QSlider, QPushButton, QProgressBar, QTextEdit,
    QTableWidget, QTableWidgetItem, QDialog, QFileDialog, QFormLayout
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from ofscraper.ui.api import build_scrape_context, run_scraper, update_queue, get_log_queue  # Updated for log integration

class ScraperWorker(QObject):
    progress_update = Signal(str)
    log_update = Signal(str)
    finished = Signal()

    def run(self):
        inputs = self.inputs  # Set from main thread
        context = build_scrape_context(inputs)
        thread, monitor_thread = run_scraper(context, self.progress_update.emit)
        thread.join()
        monitor_thread.join()
        self.finished.emit()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        layout = QFormLayout(self)
        # Add settings fields here, e.g., config options
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        layout.addWidget(self.save_button)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OF-Scraper Desktop UI")
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        # Home Page
        home_page = QWidget()
        home_layout = QVBoxLayout(home_page)
        self.api_key_input = QLineEdit()
        self.profile_url_input = QLineEdit()
        self.download_checkbox = QCheckBox("Download Media")
        self.folder_picker = QPushButton("Select Folder")
        self.folder_picker.clicked.connect(self.select_folder)
        self.folder_path = QLineEdit()
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_scraping)
        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.show_settings)

        home_layout.addWidget(QLabel("API Key:"))
        home_layout.addWidget(self.api_key_input)
        home_layout.addWidget(QLabel("Profile URL:"))
        home_layout.addWidget(self.profile_url_input)
        home_layout.addWidget(self.download_checkbox)
        home_layout.addWidget(QLabel("Download Folder:"))
        home_layout.addWidget(self.folder_path)
        home_layout.addWidget(self.folder_picker)
        home_layout.addWidget(self.start_button)
        home_layout.addWidget(self.settings_button)
        self.central_widget.addWidget(home_page)

        # Progress Page
        progress_page = QWidget()
        progress_layout = QVBoxLayout(progress_page)
        self.progress_bar = QProgressBar()
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_scraping)
        progress_layout.addWidget(QLabel("Progress:"))
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(QLabel("Logs:"))
        progress_layout.addWidget(self.log_console)
        progress_layout.addWidget(self.cancel_button)
        self.central_widget.addWidget(progress_page)

        # Results Page
        results_page = QWidget()
        results_layout = QVBoxLayout(results_page)
        self.results_table = QTableWidget(0, 3)  # Columns: File, Size, Status
        self.results_table.setHorizontalHeaderLabels(["File", "Size", "Status"])
        self.export_button = QPushButton("Export to CSV")
        self.export_button.clicked.connect(self.export_results)
        results_layout.addWidget(QLabel("Results:"))
        results_layout.addWidget(self.results_table)
        results_layout.addWidget(self.export_button)
        self.central_widget.addWidget(results_page)

        self.worker = None
        self.thread = None

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.folder_path.setText(folder)

    def show_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def start_scraping(self):
        try:
            inputs = {
                'api_key': self.api_key_input.text(),
                'profiles': [self.profile_url_input.text()],
                'actions': ['download'] if self.download_checkbox.isChecked() else [],
                'download_options': {'folder': self.folder_path.text()},
                # Add more inputs as per specs
            }
            self.central_widget.setCurrentIndex(1)  # Switch to progress page

            self.thread = QThread()
            self.worker = ScraperWorker()
            self.worker.inputs = inputs
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.scraping_finished)
            self.worker.progress_update.connect(self.update_progress)
            self.worker.log_update.connect(self.update_log)  # Ensure this connects to UI log handling
            self.thread.start()
        except Exception as e:
            self.log_console.append(f"Error starting scraping: {str(e)}")  # Local UI error handling

    def cancel_scraping(self):
        # Implement cancel logic, perhaps signal to thread
        self.central_widget.setCurrentIndex(0)

    def update_progress(self, message):
        # Parse message for progress value if needed
        self.progress_bar.setValue(int(float(message) * 100))  # Assuming message is progress fraction

    def update_log(self, message):
        # Assuming message is from update_queue or log_queue
        level, msg = message  # Unpack if from CustomLogger
        self.log_console.append(f"[{level.upper()}] {msg}")

    def scraping_finished(self):
        self.thread.quit()
        self.thread.wait()
        self.central_widget.setCurrentIndex(2)  # Switch to results page
        # Populate results table (assuming results are available, perhaps from api)

    def export_results(self):
        # Implement export logic
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())