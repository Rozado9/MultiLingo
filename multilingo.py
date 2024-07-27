import os           # Provides OS interaction functions
import sys          # Provides access to system-specific parameters and functions
import uuid         # Generates unique identifiers
import requests     # Allows sending HTTP requests

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QLineEdit, QComboBox, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap, QFont  # Handles graphics and fonts
from PyQt5.QtCore import QThread, pyqtSignal, Qt  # Core functions such as threading and signals

import azure.cognitiveservices.speech as speechsdk  # Speech service API for Azure Cognitive Services

# Mapping of languages with their language codes
language_map = {
    "Deutsch": "de",
    "Englisch": "en",
    "Französisch": "fr",
    "Spanisch": "es",
    "Chinesisch": "zh",
    "Arabisch": "ar"
}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initialize_window_properties()
        self.set_background_image()
        self.add_widgets()

    def initialize_window_properties(self):
        # Setup main window properties
        self.setWindowTitle('MultiLingo')
        self.setFixedSize(1027, 578)
        self.setWindowIcon(QIcon(self.resource_path('assets/data.ico')))

    def set_background_image(self):
        # Set background image for the main window
        pixmap = QPixmap(self.resource_path("assets/BG-APP.png"))
        self.bg = QLabel(self)
        self.bg.setPixmap(pixmap)
        self.bg.resize(1027, 578)

    def add_widgets(self):
        # Style and add widgets to the main window
        self.setStyleSheet("""
            QPushButton {
                border: 2px solid #5CACEE;
                border-radius: 10px;
                background-color: #87CEFA;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4682B4;
            }
            QLineEdit, QComboBox {
                border: 2px solid #A9A9A9;
                border-radius: 10px;
                padding: 5px;
                font-size: 14px;
            }
            QLabel {
                font-size: 16px;
                color: white;
                font-weight: bold;
            }
        """)

        # Add and position labels and buttons
        self.label_source_language = QLabel('Quellsprache', self)
        self.label_source_language.setGeometry(100, 25, 200, 20)

        self.label_target_language = QLabel('Zielsprache', self)
        self.label_target_language.setGeometry(100, 125, 200, 20)

        self.source_language_selector = QComboBox(self)
        self.source_language_selector.addItems(list(language_map.keys()))
        self.source_language_selector.setGeometry(100, 50, 200, 30)
        self.source_language_selector.setCurrentIndex(self.source_language_selector.findText("Englisch"))

        self.language_selector = QComboBox(self)
        self.language_selector.addItems(list(language_map.keys()))
        self.language_selector.setGeometry(100, 150, 200, 30)
        self.language_selector.setCurrentIndex(self.language_selector.findText("Deutsch"))

        self.input_text = QLineEdit(self)
        self.input_text.setPlaceholderText("Geben Sie hier Text ein...")
        self.input_text.setGeometry(100, 90, 800, 30)

        self.translate_button = QPushButton('Übersetzen', self)
        self.translate_button.setGeometry(320, 150, 100, 30)
        self.translate_button.clicked.connect(self.translate_text)

        self.translated_text_label = QLabel(self)
        self.translated_text_label.setGeometry(100, 200, 800, 220)
        self.translated_text_label.setWordWrap(True)
        self.translated_text_label.setStyleSheet("""
            background-color: #333333;
            color: white;            
            padding: 10px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
        """)

        self.speech_button = QPushButton('Spracheingabe', self)
        self.speech_button.setGeometry(450, 150, 120, 30)
        self.speech_button.clicked.connect(self.start_speech_to_text)

        # Exit Button
        self.exit_button = QPushButton('Exit', self)
        self.exit_button.setGeometry(900, 30, 100, 30)
        self.exit_button.clicked.connect(self.close_application)

    def translate_text(self):
        # Translation function to convert text from one language to another
        subscription_key = ""
        endpoint = "https://api.cognitive.microsofttranslator.com"
        location = "eastus"
        path = '/translate'
        constructed_url = endpoint + path

        source_language_code = language_map[self.source_language_selector.currentText()]
        target_language_code = language_map[self.language_selector.currentText()]

        params = {
            'api-version': '3.0',
            'from': source_language_code,
            'to': [target_language_code]
        }

        headers = {
            'Ocp-Apim-Subscription-Key': subscription_key,
            'Ocp-Apim-Subscription-Region': location,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }

        body = [{'text': self.input_text.text()}]

        try:
            response = requests.post(constructed_url, params=params, headers=headers, json=body)
            response.raise_for_status()
            result = response.json()
            translated_text = result[0]['translations'][0]['text']
            self.translated_text_label.setText(translated_text)
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, 'Fehler', 'Netzwerkfehler: ' + str(e))
        except Exception as e:
            QMessageBox.critical(self, 'Fehler', 'Ein Fehler ist aufgetreten: ' + str(e))

    def start_speech_to_text(self):
        # Speech-to-text conversion function
        speech_key, service_region = "", "eastus"
        source_language_code = 'de-DE'  # Set source language to German
        target_language_code = language_map[self.language_selector.currentText()]  # Target language from GUI selection

        translation_config = speechsdk.translation.SpeechTranslationConfig(
            subscription=speech_key, region=service_region,
            speech_recognition_language=source_language_code,
            target_languages=(target_language_code,))

        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)  # Use default microphone

        recognizer = speechsdk.translation.TranslationRecognizer(
            translation_config=translation_config, audio_config=audio_config)

        QMessageBox.information(self, "Spracheingabe", "Bitte sprechen Sie jetzt auf Deutsch...")  # Prompt user to speak

        result = recognizer.recognize_once()

        # Check the result and update GUI accordingly
        if result.reason == speechsdk.ResultReason.TranslatedSpeech:
            translated_text = result.translations[target_language_code]
            self.translated_text_label.setText(f"Erkannt: {result.text}\nÜbersetzung: {translated_text}")
        elif result.reason == speechsdk.ResultReason.RecognizedSpeech:
            self.translated_text_label.setText(f"Erkannt, aber nicht übersetzt: {result.text}")
        elif result.reason == speechsdk.ResultReason.NoMatch:
            QMessageBox.information(self, "Keine Spracheingabe erkannt", "Es konnte keine Sprache erkannt werden.")
        elif result.reason == speechsdk.ResultReason.Canceled:
            details = result.cancellation_details
            reason = details.reason
            error_info = details.error_details if reason == speechsdk.CancellationReason.Error else "Keine Details verfügbar"
            QMessageBox.warning(self, "Übersetzung abgebrochen", f"Grund: {reason}\nFehlerdetails: {error_info}")

    def close_application(self):
        # Function to close the application
        self.close()

    def resource_path(self, relative_path):
        # Function to handle resource path issues in bundled applications
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")
        return os.path.join(base_path,
