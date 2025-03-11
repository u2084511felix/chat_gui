import sys
import os
import json
import asyncio
import datetime
import re

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QStackedWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QSlider, QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QProgressDialog, QSplitter, QGroupBox
)
from PySide6.QtCore import Qt
from qasync import QEventLoop, asyncSlot

from utils.models.openai_config import Generate, Models
from utils.models.modules import (
    generate_legacy_structured_output_schema,
    legacy_structured_output,
    generate_structured_output_schema,
    structured_outputs_generator
)

class Generator_Modules():
    def __init__(self):
        super().__init__()
        self.Generator = Generate()


class ChatbotWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenAI Configuration GUI")
        self.resize(1200, 900)

        self.instance_keys = [
            "Chat",
            "Structured Schema Generator",
            "Structured Output Generator",
            "Legacy Structured Schema Generator",
            "Legacy Structured Output Generator"
        ]

        self.generator_instances = {
            key: Generator_Modules() for key in self.instance_keys
        }

        self.current_config_instance_key = self.instance_keys[0]

        self.setup_ui()

    def setup_ui(self):
        self.main_tab = QTabWidget()
        self.setCentralWidget(self.main_tab)

        self.setup_chat_tab()
        self.setup_config_tab()
        self.setup_structured_tab()

    # --- Chat Tab ---
    def setup_chat_tab(self):
        chat_tab = QWidget()
        main_layout = QHBoxLayout()

        # Left: Input area (system message and chat input)
        left_widget = QTabWidget()
        left_widget.setMinimumWidth(self.width() // 3)
        # System Message tab
        self.chat_system_edit = QTextEdit()
        self.chat_system_edit.setPlainText("You are a helpful assistant.")
        left_widget.addTab(self.chat_system_edit, "System Message")
        # Chat Input tab
        self.chat_input_edit = QTextEdit()
        self.chat_input_edit.setPlaceholderText("Enter your chat prompt here...")
        left_widget.addTab(self.chat_input_edit, "Chat Input")
        main_layout.addWidget(left_widget)

        # Right: Output, history, and session management
        right_widget = QWidget()
        right_layout = QVBoxLayout()

        # Current model label (pulled from the Chat instance’s model)
        self.current_model_label = QLabel("Current Model: " + str(
            self.generator_instances["Chat"].Generator.model))
        right_layout.addWidget(self.current_model_label)

        self.send_chat_btn = QPushButton("Send Chat")
        self.send_chat_btn.clicked.connect(self.on_send_chat)
        right_layout.addWidget(self.send_chat_btn)

        right_layout.addWidget(QLabel("Chat Output:"))
        self.chat_output = QTextEdit()
        self.chat_output.setReadOnly(False)
        right_layout.addWidget(self.chat_output)

        # Save output edit button
        self.save_output_edit_btn = QPushButton("Save Output Edit")
        self.save_output_edit_btn.clicked.connect(self.on_save_output_edit)
        right_layout.addWidget(self.save_output_edit_btn)

        self.history_combo = QComboBox()
        self.history_combo.currentIndexChanged.connect(self.on_history_changed)
        right_layout.addWidget(QLabel("Message History:"))
        right_layout.addWidget(self.history_combo)

        self.token_label = QLabel("Token Usage: 0")
        right_layout.addWidget(self.token_label)

        session_btn_layout = QHBoxLayout()
        self.export_btn = QPushButton("Export Session")
        self.export_btn.clicked.connect(self.on_export_session)
        self.import_btn = QPushButton("Import Session")
        self.import_btn.clicked.connect(self.on_import_session)
        self.clear_history_btn = QPushButton("Clear History")
        self.clear_history_btn.clicked.connect(self.on_clear_history)
        session_btn_layout.addWidget(self.export_btn)
        session_btn_layout.addWidget(self.import_btn)
        session_btn_layout.addWidget(self.clear_history_btn)
        right_layout.addLayout(session_btn_layout)

        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget)

        chat_tab.setLayout(main_layout)
        self.main_tab.addTab(chat_tab, "Chat")

    # --- Configuration Tab ---
    def setup_config_tab(self):
        self.config_tab = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)

        # Top: a tab widget to choose which instance to configure.
        self.config_instance_tabs = QTabWidget()
        for key in self.instance_keys:
            tab = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel(key))
            layout.addStretch()
            tab.setLayout(layout)
            self.config_instance_tabs.addTab(tab, key)
        self.config_instance_tabs.currentChanged.connect(self.on_config_instance_changed)
        main_layout.addWidget(self.config_instance_tabs)

        # Below: a common configuration form.
        self.config_form = QWidget()
        form_layout = QVBoxLayout()

        self.config_current_instance_label = QLabel("Current Instance: " + self.current_config_instance_key)
        form_layout.addWidget(self.config_current_instance_label)

        # Temperature
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Temperature:"))
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setMinimum(0)
        self.temp_slider.setMaximum(100)
        self.temp_slider.setValue(0)
        self.temp_slider.valueChanged.connect(self.on_temp_slider_changed)
        temp_layout.addWidget(self.temp_slider)
        self.temp_value_label = QLabel("0.00")
        temp_layout.addWidget(self.temp_value_label)
        form_layout.addLayout(temp_layout)

        # Model Selector
        form_layout.addWidget(QLabel("Select Model:"))
        self.model_selector = QComboBox()
        self.model_selector.addItem("gpt-4-turbo (latest)", Models.text.latest)
        self.model_selector.addItem("gpt-4-turbo-preview (previous)", Models.text.previous)
        self.model_selector.addItem("gpt-4-1106-preview (previous1)", Models.text.previous1)
        self.model_selector.addItem("gpt-4 (legacy)", Models.text.legacy)
        self.model_selector.addItem("gpt-4-0314 (og)", Models.text.og)
        self.model_selector.addItem("gpt-4o-64k-output-alpha (alpha)", Models.text.alpha)
        self.model_selector.addItem("gpt-4o (hipster)", Models.text.hipster)
        self.model_selector.addItem("gpt-4o-2024-08-06 (hipster_latest)", Models.text.hipster_latest)
        self.model_selector.addItem("gpt-4o-mini (hipster_mini)", Models.text.hipster_mini)
        form_layout.addWidget(self.model_selector)
        self.model_selector.currentIndexChanged.connect(self.on_model_selector_changed)

        # Max Tokens
        form_layout.addWidget(QLabel("Max Tokens:"))
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(1, 10000)
        self.max_tokens_spin.setValue(100)
        self.max_tokens_spin.valueChanged.connect(self.on_max_tokens_changed)
        form_layout.addWidget(self.max_tokens_spin)

        # Frequency Penalty
        form_layout.addWidget(QLabel("Frequency Penalty:"))
        self.freq_penalty_spin = QDoubleSpinBox()
        self.freq_penalty_spin.setRange(-2.0, 2.0)
        self.freq_penalty_spin.setSingleStep(0.1)
        self.freq_penalty_spin.setValue(0.0)
        self.freq_penalty_spin.valueChanged.connect(self.on_freq_penalty_changed)
        form_layout.addWidget(self.freq_penalty_spin)

        # Presence Penalty
        form_layout.addWidget(QLabel("Presence Penalty:"))
        self.presence_penalty_spin = QDoubleSpinBox()
        self.presence_penalty_spin.setRange(-2.0, 2.0)
        self.presence_penalty_spin.setSingleStep(0.1)
        self.presence_penalty_spin.setValue(0.0)
        self.presence_penalty_spin.valueChanged.connect(self.on_presence_penalty_changed)
        form_layout.addWidget(self.presence_penalty_spin)

        # Top_p
        form_layout.addWidget(QLabel("Top_p:"))
        self.top_p_spin = QDoubleSpinBox()
        self.top_p_spin.setRange(0.0, 1.0)
        self.top_p_spin.setSingleStep(0.05)
        self.top_p_spin.setValue(1.0)
        self.top_p_spin.valueChanged.connect(self.on_top_p_changed)
        form_layout.addWidget(self.top_p_spin)

        # Stop Sequences
        form_layout.addWidget(QLabel("Stop Sequences:"))
        self.stop_seq_edit = QLineEdit()
        self.stop_seq_edit.setPlaceholderText("Enter stop sequences separated by commas")
        self.stop_seq_edit.editingFinished.connect(self.on_stop_sequences_changed)
        form_layout.addWidget(self.stop_seq_edit)

        self.config_form.setLayout(form_layout)
        main_layout.addWidget(self.config_form)
        main_layout.addStretch()

        self.config_tab.setLayout(main_layout)
        self.main_tab.addTab(self.config_tab, "Configuration")
        # Load the initial configuration values for the default instance.
        self.load_config_values()

    def on_config_instance_changed(self, index):
        self.current_config_instance_key = self.instance_keys[index]
        self.config_current_instance_label.setText("Current Instance: " + self.current_config_instance_key)
        self.load_config_values()


    def load_config_values(self):
        instance = self.generator_instances[self.current_config_instance_key].Generator

        # Temperature: ensure fallback of 0 if None
        self.temp_slider.blockSignals(True)
        temp_value = getattr(instance, 'temperature', 0) or 0
        self.temp_slider.setValue(int(temp_value * 100))
        self.temp_value_label.setText(f"{temp_value:.2f}")
        self.temp_slider.blockSignals(False)

        # Model selector: set based on instance.model if available
        for i in range(self.model_selector.count()):
            if self.model_selector.itemData(i) == getattr(instance, 'model', None):
                self.model_selector.blockSignals(True)
                self.model_selector.setCurrentIndex(i)
                self.model_selector.blockSignals(False)
                break

        # Max tokens: fallback to 100 if None
        self.max_tokens_spin.blockSignals(True)
        max_tokens_value = getattr(instance, 'max_tokens', 100)
        if max_tokens_value is None:
            max_tokens_value = 100
        self.max_tokens_spin.setValue(max_tokens_value)
        self.max_tokens_spin.blockSignals(False)

        # Frequency penalty: fallback to 0.0
        self.freq_penalty_spin.blockSignals(True)
        self.freq_penalty_spin.setValue(getattr(instance, 'frequency_penalty', 0.0) or 0.0)
        self.freq_penalty_spin.blockSignals(False)

        # Presence penalty: fallback to 0.0
        self.presence_penalty_spin.blockSignals(True)
        self.presence_penalty_spin.setValue(getattr(instance, 'presence_penalty', 0.0) or 0.0)
        self.presence_penalty_spin.blockSignals(False)

        # Top_p: fallback to 1.0
        self.top_p_spin.blockSignals(True)
        self.top_p_spin.setValue(getattr(instance, 'top_p', 1.0) or 1.0)
        self.top_p_spin.blockSignals(False)

        # Stop sequences: if stored as list, join into a string
        stop_seq = getattr(instance, 'stop', [])
        if isinstance(stop_seq, list):
            stop_seq = ", ".join(stop_seq)
        self.stop_seq_edit.blockSignals(True)
        self.stop_seq_edit.setText(stop_seq)
        self.stop_seq_edit.blockSignals(False)

    def on_temp_slider_changed(self, value):
        temp_value = value / 100.0
        self.temp_value_label.setText(f"{temp_value:.2f}")
        instance = self.generator_instances[self.current_config_instance_key].Generator
        instance.temperature = temp_value

    def on_model_selector_changed(self, index):
        instance = self.generator_instances[self.current_config_instance_key].Generator
        instance.model = self.model_selector.itemData(index)

    def on_max_tokens_changed(self, value):
        instance = self.generator_instances[self.current_config_instance_key].Generator
        instance.max_tokens = value

    def on_freq_penalty_changed(self, value):
        instance = self.generator_instances[self.current_config_instance_key].Generator
        instance.frequency_penalty = value

    def on_presence_penalty_changed(self, value):
        instance = self.generator_instances[self.current_config_instance_key].Generator
        instance.presence_penalty = value

    def on_top_p_changed(self, value):
        instance = self.generator_instances[self.current_config_instance_key].Generator
        instance.top_p = value

    def on_stop_sequences_changed(self):
        text = self.stop_seq_edit.text().strip()
        instance = self.generator_instances[self.current_config_instance_key].Generator
        instance.stop = [s.strip() for s in text.split(",") if s.strip()] if text else []

    # --- Structured Output Tab ---
    def setup_structured_tab(self):
        struct_tab = QWidget()
        main_layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        mode_label = QLabel("Mode:")
        header_layout.addWidget(mode_label)
        mode_info = QPushButton("?")
        mode_info.setFixedSize(25, 25)
        mode_info.clicked.connect(lambda: self.show_alert("Structured Output Information",
            "New Mode (2 Steps):\n• Step 1: Generate Schema using the new generator instance.\n• Step 2: Generate Structured Output using the new generator instance.\n\nLegacy Mode (2 Steps):\n• Step 1: Generate Legacy Schema using the legacy schema generator instance.\n• Step 2: Generate Legacy Structured Output using the legacy output generator instance."))
        header_layout.addWidget(mode_info)
        self.structured_mode_combo = QComboBox()
        self.structured_mode_combo.addItem("Structured Output (New)")
        self.structured_mode_combo.addItem("Legacy Structured Output")
        self.structured_mode_combo.currentIndexChanged.connect(self.on_structured_mode_changed)
        self.structured_mode_combo.setMaximumWidth(300)
        header_layout.addWidget(self.structured_mode_combo)
        self.structured_clear_btn = QPushButton("Clear")
        self.structured_clear_btn.setFixedSize(60, 25)
        self.structured_clear_btn.clicked.connect(self.clear_structured_inputs)
        header_layout.addWidget(self.structured_clear_btn)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        self.structured_stack = QStackedWidget()

        # --- New Mode (Non‑Legacy) Structured Output Page (2 Steps) ---
        nonlegacy_mode_page = QWidget()
        nonlegacy_layout = QVBoxLayout()

        # Step 1: Schema Generation
        step1_box = QGroupBox("Step 1: Schema Generation")
        step1_layout = QVBoxLayout()
        header1_layout = QHBoxLayout()
        header1_layout.addWidget(QLabel("Schema Generation"))
        clear1_btn = QPushButton("Clear")
        clear1_btn.setFixedSize(60, 25)
        clear1_btn.clicked.connect(self.clear_nonlegacy_schema_inputs)
        header1_layout.addStretch()
        header1_layout.addWidget(clear1_btn)
        step1_layout.addLayout(header1_layout)

        splitter_schema = QSplitter(Qt.Horizontal)
        nonlegacy_left = QTabWidget()
        nonlegacy_left.setMinimumWidth(self.width() // 3)
        # System Message tab for schema generation
        schema_sys_tab = QWidget()
        schema_sys_layout = QVBoxLayout()
        self.nonlegacy_schema_system = QTextEdit()
        self.nonlegacy_schema_system.setPlainText("Generate a JSON schema for the given instruction converting from an existing data model outline, using the function.")
        schema_sys_layout.addWidget(self.nonlegacy_schema_system)
        schema_sys_tab.setLayout(schema_sys_layout)
        nonlegacy_left.addTab(schema_sys_tab, "System Message")
        # Input Schema tab
        schema_input_tab = QWidget()
        schema_input_layout = QVBoxLayout()
        self.nonlegacy_input_schema_edit = QTextEdit()
        default_schema = {
            "timestamp": "",
            "recipe_name": "",
            "recipe_description": "",
            "ingredients": "",
            "cooking_instruction": "",
            "nutritional_values": {
                "proteins": "",
                "fats": "",
                "carbs": "",
                "sugar": "",
                "salt": "",
                "minerals": "",
                "nutrients": ""
            },
            "portion_size": "",
            "estimated_calories": ""
        }
        self.nonlegacy_input_schema_edit.setPlainText(json.dumps(default_schema, indent=4))
        schema_input_layout.addWidget(self.nonlegacy_input_schema_edit)
        schema_input_tab.setLayout(schema_input_layout)
        nonlegacy_left.addTab(schema_input_tab, "Input Schema")
        splitter_schema.addWidget(nonlegacy_left)

        nonlegacy_right = QWidget()
        nonlegacy_right_layout = QVBoxLayout()
        schema_label_layout = QHBoxLayout()
        schema_label = QLabel("Generated Schema:")
        schema_label_layout.addWidget(schema_label)
        schema_info_btn = QPushButton("?")
        schema_info_btn.setFixedSize(25, 25)
        schema_info_btn.clicked.connect(lambda: self.show_alert("Schema Info", "The generated JSON schema will be displayed here."))
        schema_label_layout.addWidget(schema_info_btn)
        nonlegacy_right_layout.addLayout(schema_label_layout)
        self.nonlegacy_schema_edit = QTextEdit()
        self.nonlegacy_schema_edit.setReadOnly(True)
        nonlegacy_right_layout.addWidget(self.nonlegacy_schema_edit)
        schema_action_layout = QHBoxLayout()
        self.nonlegacy_generate_schema_btn = QPushButton("Generate Schema")
        self.nonlegacy_generate_schema_btn.clicked.connect(self.on_generate_nonlegacy_schema)
        schema_action_layout.addWidget(self.nonlegacy_generate_schema_btn)
        schema_copy_btn = QPushButton("Copy Schema")
        schema_copy_btn.clicked.connect(lambda: self.copy_to_clipboard(self.nonlegacy_schema_edit.toPlainText()))
        schema_action_layout.addWidget(schema_copy_btn)
        schema_export_btn = QPushButton("Export Schema")
        schema_export_btn.clicked.connect(lambda: self.export_to_folder(self.nonlegacy_schema_edit.toPlainText(), "GeneratedSchemas", "nonlegacy_schema"))
        schema_action_layout.addWidget(schema_export_btn)
        schema_import = QPushButton("Import Schema")
        schema_import.clicked.connect(self.on_import_schema)
        schema_action_layout.addWidget(schema_import)
        nonlegacy_right_layout.addLayout(schema_action_layout)
        nonlegacy_right.setLayout(nonlegacy_right_layout)
        splitter_schema.addWidget(nonlegacy_right)
        step1_layout.addWidget(splitter_schema)
        step1_box.setLayout(step1_layout)
        nonlegacy_layout.addWidget(step1_box)

        # Step 2: Structured Output Generation
        step2_box = QGroupBox("Step 2: Structured Output Generation")
        step2_layout = QVBoxLayout()
        header2_layout = QHBoxLayout()
        header2_layout.addWidget(QLabel("Structured Output Generation"))
        clear2_btn = QPushButton("Clear")
        clear2_btn.setFixedSize(60, 25)
        clear2_btn.clicked.connect(self.clear_nonlegacy_output_inputs)
        header2_layout.addStretch()
        header2_layout.addWidget(clear2_btn)
        step2_layout.addLayout(header2_layout)

        splitter_output = QSplitter(Qt.Horizontal)
        nonlegacy_output_left = QTabWidget()
        nonlegacy_output_left.setMinimumWidth(self.width() // 3)
        # System Message tab for output generation
        output_sys_tab = QWidget()
        output_sys_layout = QVBoxLayout()
        self.nonlegacy_output_system = QTextEdit()
        self.nonlegacy_output_system.setPlainText("Generate a JSON schema for the given content model.")
        output_sys_layout.addWidget(self.nonlegacy_output_system)
        output_sys_tab.setLayout(output_sys_layout)
        nonlegacy_output_left.addTab(output_sys_tab, "System Message")
        # Instructions tab
        output_prompt_tab = QWidget()
        output_prompt_layout = QVBoxLayout()
        self.nonlegacy_prompt_edit = QLineEdit()
        self.nonlegacy_prompt_edit.setPlaceholderText("Enter prompt for structured output generation...")
        output_prompt_layout.addWidget(self.nonlegacy_prompt_edit)
        output_prompt_tab.setLayout(output_prompt_layout)
        nonlegacy_output_left.addTab(output_prompt_tab, "Instructions")
        splitter_output.addWidget(nonlegacy_output_left)

        nonlegacy_output_right = QWidget()
        nonlegacy_output_right_layout = QVBoxLayout()
        output_label_layout = QHBoxLayout()
        output_label = QLabel("Structured Output:")
        output_label_layout.addWidget(output_label)
        output_info_btn = QPushButton("?")
        output_info_btn.setFixedSize(25, 25)
        output_info_btn.clicked.connect(lambda: self.show_alert("Output Info", "The generated structured output will be displayed here."))
        output_label_layout.addWidget(output_info_btn)
        nonlegacy_output_right_layout.addLayout(output_label_layout)
        self.nonlegacy_output_view = QTextEdit()
        self.nonlegacy_output_view.setReadOnly(True)
        nonlegacy_output_right_layout.addWidget(self.nonlegacy_output_view)
        output_action_layout = QHBoxLayout()
        self.nonlegacy_generate_output_btn = QPushButton("Generate Output")
        self.nonlegacy_generate_output_btn.clicked.connect(self.on_generate_nonlegacy_output)
        output_action_layout.addWidget(self.nonlegacy_generate_output_btn)
        output_copy_btn = QPushButton("Copy Output")
        output_copy_btn.clicked.connect(lambda: self.copy_to_clipboard(self.nonlegacy_output_view.toPlainText()))
        output_action_layout.addWidget(output_copy_btn)
        output_export_btn = QPushButton("Export Output")
        output_export_btn.clicked.connect(lambda: self.export_to_folder(self.nonlegacy_output_view.toPlainText(), "StructuredOutputs", "nonlegacy_structured_output"))
        output_action_layout.addWidget(output_export_btn)
        nonlegacy_output_right_layout.addLayout(output_action_layout)
        nonlegacy_output_right.setLayout(nonlegacy_output_right_layout)
        splitter_output.addWidget(nonlegacy_output_right)
        step2_layout.addWidget(splitter_output)
        step2_box.setLayout(step2_layout)
        nonlegacy_layout.addWidget(step2_box)
        nonlegacy_mode_page.setLayout(nonlegacy_layout)
        self.structured_stack.addWidget(nonlegacy_mode_page)

        # --- Legacy Mode Structured Output Page ---
        legacy_mode_page = QWidget()
        legacy_layout = QVBoxLayout()

        # Step 1: Legacy Schema Generation
        step1_box = QGroupBox("Step 1: Legacy Schema Generation")
        step1_layout = QVBoxLayout()
        header1_layout = QHBoxLayout()
        header1_layout.addWidget(QLabel("Legacy Schema Generation"))
        clear1_btn = QPushButton("Clear")
        clear1_btn.setFixedSize(60, 25)
        clear1_btn.clicked.connect(self.clear_legacy_schema_inputs)
        header1_layout.addStretch()
        header1_layout.addWidget(clear1_btn)
        step1_layout.addLayout(header1_layout)
        splitter_legacy_schema = QSplitter(Qt.Horizontal)
        legacy_left = QTabWidget()
        legacy_left.setMinimumWidth(self.width() // 3)
        legacy_sys_tab = QWidget()
        legacy_sys_layout = QVBoxLayout()
        self.legacy_schema_system = QTextEdit()
        self.legacy_schema_system.setPlainText("Generate a JSON schema for the given instruction converting from an existing data model outline, using the function.")
        legacy_sys_layout.addWidget(self.legacy_schema_system)
        legacy_sys_tab.setLayout(legacy_sys_layout)
        legacy_left.addTab(legacy_sys_tab, "System Message")
        legacy_test_tab = QWidget()
        legacy_test_layout = QVBoxLayout()
        self.legacy_input_schema_edit = QTextEdit()
        input_schema = {
            "timestamp": "",
            "name": "",
            "description": "",
            "ingredients": "",
            "cooking_instruction": "",
            "nutritional_values": {
                "proteins": "",
                "fats": "",
                "carbs": "",
                "sugar": "",
                "salt": "",
                "minerals": "",
                "nutrients": ""
            },
            "portion_size": "",
            "estimated_calories": ""
        }
        self.legacy_input_schema_edit.setPlainText(json.dumps(input_schema, indent=4))
        legacy_test_layout.addWidget(self.legacy_input_schema_edit)
        legacy_test_tab.setLayout(legacy_test_layout)
        legacy_left.addTab(legacy_test_tab, "Input Schema")
        splitter_legacy_schema.addWidget(legacy_left)
        legacy_right = QWidget()
        legacy_right_layout = QVBoxLayout()
        legacy_schema_label_layout = QHBoxLayout()
        legacy_schema_label = QLabel("Legacy Schema:")
        legacy_schema_label_layout.addWidget(legacy_schema_label)
        legacy_schema_info = QPushButton("?")
        legacy_schema_info.setFixedSize(25, 25)
        legacy_schema_info.clicked.connect(lambda: self.show_alert("Legacy Schema", "After clicking 'Generate Legacy Schema', the generated legacy schema will be displayed here."))
        legacy_schema_label_layout.addWidget(legacy_schema_info)
        legacy_right_layout.addLayout(legacy_schema_label_layout)
        self.legacy_schema_edit = QTextEdit()
        self.legacy_schema_edit.setReadOnly(True)
        legacy_right_layout.addWidget(self.legacy_schema_edit)
        legacy_schema_action_layout = QHBoxLayout()
        self.legacy_generate_schema_btn = QPushButton("Generate Legacy Schema")
        self.legacy_generate_schema_btn.clicked.connect(self.on_generate_legacy_schema)
        legacy_schema_action_layout.addWidget(self.legacy_generate_schema_btn)
        legacy_schema_copy = QPushButton("Copy Schema")
        legacy_schema_copy.clicked.connect(lambda: self.copy_to_clipboard(self.legacy_schema_edit.toPlainText()))
        legacy_schema_action_layout.addWidget(legacy_schema_copy)
        legacy_schema_export = QPushButton("Export Schema")
        legacy_schema_export.clicked.connect(lambda: self.export_to_folder(self.legacy_schema_edit.toPlainText(), "GeneratedSchemas", "legacy_schema"))
        legacy_schema_action_layout.addWidget(legacy_schema_export)
        legacy_schema_import = QPushButton("Import Schema")
        legacy_schema_import.clicked.connect(self.on_legacy_import_schema)
        legacy_schema_action_layout.addWidget(legacy_schema_import)
        legacy_right_layout.addLayout(legacy_schema_action_layout)
        legacy_right.setLayout(legacy_right_layout)
        splitter_legacy_schema.addWidget(legacy_right)
        step1_layout.addWidget(splitter_legacy_schema)
        step1_box.setLayout(step1_layout)
        legacy_layout.addWidget(step1_box)

        # Step 2: Legacy Structured Output Generation
        step2_box = QGroupBox("Step 2: Legacy Structured Output Generation")
        step2_layout = QVBoxLayout()
        header2_layout = QHBoxLayout()
        header2_layout.addWidget(QLabel("Legacy Output Generation"))
        clear2_btn = QPushButton("Clear")
        clear2_btn.setFixedSize(60, 25)
        clear2_btn.clicked.connect(self.clear_legacy_output_inputs)
        header2_layout.addStretch()
        header2_layout.addWidget(clear2_btn)
        step2_layout.addLayout(header2_layout)
        splitter_legacy_output = QSplitter(Qt.Horizontal)
        legacy_output_left = QTabWidget()
        legacy_output_left.setMinimumWidth(self.width() // 3)
        legacy_output_sys_tab = QWidget()
        legacy_output_sys_layout = QVBoxLayout()
        self.legacy_output_system = QTextEdit()
        self.legacy_output_system.setPlainText("Supply the function variables for the given function according to the instruction.")
        legacy_output_sys_layout.addWidget(self.legacy_output_system)
        legacy_output_sys_tab.setLayout(legacy_output_sys_layout)
        legacy_output_left.addTab(legacy_output_sys_tab, "System Message")
        legacy_prompt_tab = QWidget()
        legacy_prompt_layout = QVBoxLayout()
        self.legacy_prompt_edit = QLineEdit()
        self.legacy_prompt_edit.setPlaceholderText("Enter an instruction prompt (e.g., 'Create a nutritious breakfast recipe')...")
        legacy_prompt_layout.addWidget(self.legacy_prompt_edit)
        legacy_prompt_tab.setLayout(legacy_prompt_layout)
        legacy_output_left.addTab(legacy_prompt_tab, "Instructions")
        splitter_legacy_output.addWidget(legacy_output_left)
        legacy_output_right = QWidget()
        legacy_output_right_layout = QVBoxLayout()
        legacy_output_label_layout = QHBoxLayout()
        legacy_output_label = QLabel("Legacy Structured Output:")
        legacy_output_label_layout.addWidget(legacy_output_label)
        legacy_output_info = QPushButton("?")
        legacy_output_info.setFixedSize(25, 25)
        legacy_output_info.clicked.connect(lambda: self.show_alert("Structured Output", "The generated legacy structured output will appear here."))
        legacy_output_label_layout.addWidget(legacy_output_info)
        legacy_output_right_layout.addLayout(legacy_output_label_layout)
        self.legacy_output_view = QTextEdit()
        self.legacy_output_view.setReadOnly(True)
        legacy_output_right_layout.addWidget(self.legacy_output_view)
        legacy_output_action_layout = QHBoxLayout()
        self.legacy_generate_output_btn = QPushButton("Generate Legacy Output")
        self.legacy_generate_output_btn.clicked.connect(self.on_generate_legacy_output)
        legacy_output_action_layout.addWidget(self.legacy_generate_output_btn)
        legacy_output_copy = QPushButton("Copy Output")
        legacy_output_copy.clicked.connect(lambda: self.copy_to_clipboard(self.legacy_output_view.toPlainText()))
        legacy_output_action_layout.addWidget(legacy_output_copy)
        legacy_output_export = QPushButton("Export Output")
        legacy_output_export.clicked.connect(lambda: self.export_to_folder(self.legacy_output_view.toPlainText(), "StructuredOutputs", "legacy_structured_output"))
        legacy_output_action_layout.addWidget(legacy_output_export)
        legacy_output_right_layout.addLayout(legacy_output_action_layout)
        legacy_output_right.setLayout(legacy_output_right_layout)
        splitter_legacy_output.addWidget(legacy_output_right)
        step2_layout.addWidget(splitter_legacy_output)
        step2_box.setLayout(step2_layout)
        legacy_layout.addWidget(step2_box)
        legacy_mode_page.setLayout(legacy_layout)
        self.structured_stack.addWidget(legacy_mode_page)

        main_layout.addWidget(self.structured_stack)
        struct_tab.setLayout(main_layout)
        self.main_tab.addTab(struct_tab, "Structured Output")

    # --- Clear Methods for Structured Output ---
    def clear_nonlegacy_schema_inputs(self):
        self.nonlegacy_input_schema_edit.clear()
        self.nonlegacy_schema_edit.clear()

    def clear_nonlegacy_output_inputs(self):
        self.nonlegacy_prompt_edit.clear()
        self.nonlegacy_output_view.clear()

    def clear_legacy_schema_inputs(self):
        self.legacy_input_schema_edit.clear()
        self.legacy_schema_edit.clear()

    def clear_legacy_output_inputs(self):
        self.legacy_prompt_edit.clear()
        self.legacy_output_view.clear()

    # New method to clear structured inputs based on current mode
    def clear_structured_inputs(self):
        current_index = self.structured_mode_combo.currentIndex()
        if current_index == 0:  # New Mode
            self.clear_nonlegacy_schema_inputs()
            self.clear_nonlegacy_output_inputs()
        elif current_index == 1:  # Legacy Mode
            self.clear_legacy_schema_inputs()
            self.clear_legacy_output_inputs()

    def on_structured_mode_changed(self, index):
        self.structured_stack.setCurrentIndex(index)

    # --- Chat Methods ---
    @asyncSlot()
    async def on_send_chat(self):
        system_message = self.chat_system_edit.toPlainText().strip()
        chat_input = self.chat_input_edit.toPlainText().strip()
        if not system_message:
            self.show_alert("Validation Error", "System message cannot be empty!")
            return
        if not chat_input:
            self.show_alert("Validation Error", "Chat input cannot be empty!")
            return

        # Use the Chat generator instance.
        chat_gen = self.generator_instances["Chat"].Generator

        try:
            loading = self.show_loading_dialog("Generating output", "please wait")
            response_obj = await chat_gen.generate(
                system_message, chat_input,
                model=chat_gen.model,
                temperature=chat_gen.temperature,
                chat=False
            )
            loading.close()
        except Exception as e:
            response_obj = {"choices": [{"message": {"content": f"Error: {e}"}}], "usage": {"total_tokens": "N/A"}}

        assistant_message = response_obj.choices[0].message.content
        token_use = str(response_obj.usage.total_tokens)

        # Append to the Chat instance's messages.
        chat_gen.messages.append({"role": "assistant", "content": assistant_message})
        self.update_history_combo()

        self.token_label.setText("Token usage: " + token_use)
        self.current_model_label.setText("Current Model: " + str(chat_gen.model))
        self.chat_output.setPlainText(assistant_message)
        self.chat_input_edit.clear()

    def on_history_changed(self, index):
        chat_gen = self.generator_instances["Chat"].Generator
        if 0 <= index < len(chat_gen.messages):
            self.chat_output.setPlainText(chat_gen.messages[index]["content"])

    def on_save_output_edit(self):
        index = self.history_combo.currentIndex()
        chat_gen = self.generator_instances["Chat"].Generator
        if 0 <= index < len(chat_gen.messages):
            new_content = self.chat_output.toPlainText()
            chat_gen.messages[index]["content"] = new_content
            self.show_alert("Saved", "Message updated successfully.")
        else:
            self.show_alert("Error", "No message selected to save.")

    def on_export_session(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Export Session", "", "JSON Files (*.json)")
        if filename:
            chat_gen = self.generator_instances["Chat"].Generator
            session = {
                "messages": chat_gen.messages,
                "config": {
                    "temperature": chat_gen.temperature,
                    "model": chat_gen.model,
                    "max_tokens": chat_gen.max_tokens,
                    "frequency_penalty": chat_gen.frequency_penalty,
                    "presence_penalty": chat_gen.presence_penalty,
                    "top_p": chat_gen.top_p,
                    "stop": chat_gen.stop
                }
            }
            try:
                with open(filename, "w") as f:
                    json.dump(session, f, indent=4)
                self.show_alert("Export Successful", f"Session exported to {filename}")
            except Exception as e:
                self.show_alert("Export Error", str(e))

    def on_import_session(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Import Session", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, "r") as f:
                    session = json.load(f)
            except Exception as e:
                self.show_alert("Import Error", str(e))
                return
            config = session.get("config", {})
            chat_gen = self.generator_instances["Chat"].Generator
            chat_gen.temperature = float(config.get("temperature", 0))
            model_value = config.get("model", "")
            index = self.model_selector.findData(model_value)
            if index != -1:
                self.model_selector.setCurrentIndex(index)
                chat_gen.model = self.model_selector.itemData(index)
            chat_gen.max_tokens = config.get("max_tokens", 100)
            chat_gen.frequency_penalty = config.get("frequency_penalty", 0.0)
            chat_gen.presence_penalty = config.get("presence_penalty", 0.0)
            chat_gen.top_p = config.get("top_p", 1.0)
            chat_gen.stop = config.get("stop", [])
            chat_gen.messages = session.get("messages", [])
            self.update_history_combo()

    def on_clear_history(self):
        chat_gen = self.generator_instances["Chat"].Generator
        chat_gen.messages = []
        self.update_history_combo()
        self.chat_output.clear()
        chat_gen.token_usage = 0

    def update_history_combo(self):
        chat_gen = self.generator_instances["Chat"].Generator
        self.history_combo.clear()
        for i, msg in enumerate(chat_gen.messages):
            self.history_combo.addItem(f"Message {i+1}")

    def show_loading_dialog(self, title, content):
        dlg = QProgressDialog(content, None, 0, 0, self)
        dlg.setWindowTitle(title)
        dlg.setLabelText(content)
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.setCancelButton(None)
        dlg.setMinimumDuration(0)
        dlg.show()
        QApplication.processEvents()
        return dlg

    # --- Structured Output: New (Non‑Legacy) Mode Methods ---
    @asyncSlot()
    async def on_generate_nonlegacy_schema(self):
        input_schema_text = self.nonlegacy_input_schema_edit.toPlainText().strip()
        if not input_schema_text:
            self.show_alert("Validation Error", "Input schema is required for schema generation!")
            return
        try:
            json.loads(input_schema_text)
        except Exception as e:
            self.show_alert("Validation Error", f"Invalid input schema JSON: {e}")
            return

        instance = self.generator_instances["Structured Schema Generator"].Generator
        system_message = self.nonlegacy_schema_system.toPlainText().strip()
        loading = self.show_loading_dialog("Generating schema", "please wait")
        try:

            generated_schema = await generate_structured_output_schema(input_schema_text, system_message)
            loading.close()
        except Exception as e:
            self.show_alert("Error", f"Schema generation failed: {e}")
            loading.close()
            return
        try:
            parsed = json.loads(generated_schema)
            formatted = json.dumps(parsed, indent=4)
        except Exception:
            formatted = generated_schema
        self.nonlegacy_schema_edit.setPlainText(formatted)

    @asyncSlot()
    async def on_generate_nonlegacy_output(self):
        prompt = self.nonlegacy_prompt_edit.text().strip()
        if not prompt:
            self.show_alert("Validation Error", "Prompt is required for structured output generation!")
            return
        schema_text = self.nonlegacy_schema_edit.toPlainText().strip()
        if not schema_text:
            self.show_alert("Validation Error", "Generated schema is required! Please generate schema first.")
            return
        try:
            json.loads(schema_text)
        except Exception as e:
            self.show_alert("Validation Error", f"Invalid schema JSON: {e}")
            return

        # Use the Structured Output Generator instance.
        instance = self.generator_instances["Structured Output Generator"].Generator
        system_message = self.nonlegacy_output_system.toPlainText().strip()
        loading = self.show_loading_dialog("Generating structured output", "please wait")
        try:

            nonlegacy_output = await structured_outputs_generator(prompt, schema_text)

            loading.close()
        except Exception as e:
            self.show_alert("Error", f"Structured output generation failed: {e}")
            loading.close()
            return
        try:
            parsed_output = json.loads(nonlegacy_output)
            formatted_output = json.dumps(parsed_output, indent=4)
        except Exception:
            formatted_output = nonlegacy_output
        self.nonlegacy_output_view.setPlainText(formatted_output)

    # --- Structured Output: Legacy Mode Methods ---
    @asyncSlot()
    async def on_generate_legacy_schema(self):
        input_schema_text = self.legacy_input_schema_edit.toPlainText().strip()
        if not input_schema_text:
            self.show_alert("Validation Error", "Input schema is required for legacy schema generation!")
            return
        try:
            json.loads(input_schema_text)
        except Exception as e:
            self.show_alert("Validation Error", f"Invalid input schema JSON: {e}")
            return

        # Use the Legacy Schema Generator instance.
        instance = self.generator_instances["Legacy Structured Schema Generator"].Generator
        system_message = self.legacy_schema_system.toPlainText().strip()
        loading = self.show_loading_dialog("Generating legacy schema", "please wait")
        try:

            generated_schema = await generate_legacy_structured_output_schema(input_schema_text)

            loading.close()
        except Exception as e:
            self.show_alert("Error", f"Legacy schema generation failed: {e}")
            loading.close()
            return
        try:
            parsed = json.loads(generated_schema)
            formatted = json.dumps(parsed, indent=4)
        except Exception:
            formatted = generated_schema
        self.legacy_schema_edit.setPlainText(formatted)

    @asyncSlot()
    async def on_generate_legacy_output(self):
        # For legacy output, ensure the current model is compatible.
        current_model = self.model_selector.currentData()
        if current_model not in [Models.text.hipster]:
            self.show_alert("Model Incompatible", "Please switch to a compatible model for legacy output.")
            return

        prompt = self.legacy_prompt_edit.text().strip()
        if not prompt:
            self.show_alert("Validation Error", "Legacy prompt is required!")
            return
        schema_text = self.legacy_schema_edit.toPlainText().strip()
        if not schema_text:
            self.show_alert("Validation Error", "Input schema is required! Generate it first.")
            return
        try:
            json.loads(schema_text)
        except Exception as e:
            self.show_alert("Validation Error", f"Invalid legacy schema JSON: {e}")
            return

        # Use the Legacy Structured Output Generator instance.
        instance = self.generator_instances["Legacy Structured Output Generator"].Generator
        system_message = self.legacy_output_system.toPlainText().strip()
        loading = self.show_loading_dialog("Generating legacy structured output", "please wait")
        try:

            legacy_output = await legacy_structured_output(prompt, schema_text)

            loading.close()
        except Exception as e:
            self.show_alert("Error", f"Legacy output generation failed: {e}")
            loading.close()
            return
        try:
            parsed_output = json.loads(legacy_output)
            formatted_output = json.dumps(parsed_output, indent=4)
        except Exception:
            formatted_output = legacy_output
        self.legacy_output_view.setPlainText(formatted_output)

    # --- Import / Export Schema Methods ---
    def on_import_schema(self):
        folder_path = os.path.join(os.getcwd(), "GeneratedSchemas")
        os.makedirs(folder_path, exist_ok=True)
        filename, _ = QFileDialog.getOpenFileName(self, "Import Schema", folder_path, "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, "r") as f:
                    schema = json.load(f)
                    self.nonlegacy_schema_edit.setPlainText(json.dumps(schema, indent=4))
                self.show_alert("Import Successful", "Schema imported successfully.")
            except Exception as e:
                self.show_alert("Import Error", str(e))

    def on_legacy_import_schema(self):
        folder_path = os.path.join(os.getcwd(), "GeneratedSchemas")
        os.makedirs(folder_path, exist_ok=True)
        filename, _ = QFileDialog.getOpenFileName(self, "Import Schema", folder_path, "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, "r") as f:
                    schema = json.load(f)
                    self.legacy_schema_edit.setPlainText(json.dumps(schema, indent=4))
                self.show_alert("Import Successful", "Schema imported successfully.")
            except Exception as e:
                self.show_alert("Import Error", str(e))

    # --- Additional Methods ---
    def show_alert(self, title, message):
        QMessageBox.information(self, title, message)

    def copy_to_clipboard(self, text):
        QApplication.clipboard().setText(text)
        self.show_alert("Copied", "Content copied to clipboard.")

    def export_to_folder(self, text, folder_name, prefix):
        if not text:
            self.show_alert("Export Error", "There is no content to export.")
            return
        folder_path = os.path.join(os.getcwd(), folder_name)
        os.makedirs(folder_path, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.json"
        file_path = os.path.join(folder_path, filename)
        try:
            with open(file_path, "w") as f:
                try:
                    parsed = json.loads(text)
                    json.dump(parsed, f, indent=4)
                except Exception:
                    f.write(text)
            self.show_alert("Export Successful", f"File saved to: {file_path}")
        except Exception as e:
            self.show_alert("Export Error", str(e))


def main():
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1.5"
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = ChatbotWindow()
    window.show()
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
