# -*- coding: utf-8 -*-
import sys
import os
import json
import shutil
import subprocess
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QFormLayout, QComboBox, QPlainTextEdit,
    QLineEdit, QCheckBox, QTabWidget, QLabel
)
from PySide6.QtCore import QObject, QThread, Signal, Qt

RUN_PATH = Path.cwd()
SRC_PATH = Path(__file__).resolve()
SCRIPTS_PATH = RUN_PATH / "python_standalone" / "Scripts"
PYTHON_EXE = sys.executable
CONFIG_FILE = os.path.join(RUN_PATH, "launcher_config.json")


# --- 1. Program and Parameter Definitions ---
PROGRAMS = [
    {
        "name": "global_settings",
        "label": "General Settings",
        "common_env_vars": [
            {"name": "HTTP_PROXY", "type": "string", "label": "HTTP Proxy Server", "help": "Set HTTP_PROXY environment variable, e.g., http://localhost:1080", "default": ""},
            {"name": "HTTPS_PROXY", "type": "string", "label": "HTTPS Proxy Server", "help": "Set HTTPS_PROXY environment variable, e.g., http://localhost:1080", "default": ""},
            {"name": "PIP_INDEX_URL", "type": "string", "label": "PyPI Mirror", "help": "PyPI mirror source for installing Python packages", "default": ""},
            {"name": "HF_ENDPOINT", "type": "string", "label": "HuggingFace Mirror", "help": "Mirror source for HuggingFace Hub downloads", "default": ""},
        ],
    },
    {
        "name": "Hunyuan3D-2",
        "label": "Hunyuan 3D 2.0 | Comprehensive Features",
        "folder": "Hunyuan3D-2",
        "script": "gradio_app.py",
        "parameters": [
            {"name": "_enable_texture_gen", "type": "boolean", "label": "Enable Texture Generation", "help": "Requires CUDA and MSVC installation. By default, generating mesh requires 4GB VRAM, generating texture requires 6GB VRAM"},
            {"name": "_model_select", "type": "choice", "label": "Model Selection", "options": [
                  {"name": "--mini", "label":"Single-view Input - Mini Model: Default option, suitable for most cases"},
                  {"name": "--h2", "label":"Single-view Input - Standard Model: Requires more VRAM"},
                  {"name": "--mv", "label":"Multi-view Input (MV)"},
                  ],
                  "default": "--mini"},
            {"name": "--turbo", "type": "boolean", "label": "Use Turbo Model", "help": "Enabled by default, significantly faster with slightly lower quality", "default": True},
            {"name": "--enable_t23d", "type": "boolean", "label": "Enable Text-to-3D", "help": "Principle: Generate image from prompt first, then generate 3D from image", "default": False},
            {"name": "--profile", "type": "choice", "label": "VRAM Optimization Level", "help":"Select mmgp optimization level to enable quantization, slicing, VRAM offloading, etc.", "options": [
                  {"name": "1", "label":"1-High Memory, High VRAM"},
                  {"name": "2", "label":"2-High Memory, Low VRAM"},
                  {"name": "3", "label":"3-Low Memory, High VRAM"},
                  {"name": "4", "label":"4-Low Memory, Low VRAM"},
                  {"name": "5", "label":"5-Very Low Memory, Low VRAM"},
                  ],
                  "default": "4"},
        ]
    },
    {
        "name": "Hunyuan3D-2-vanilla",
        "label": "Hunyuan 3D 2.0 Official Code | Suitable for Users with Ample VRAM",
        "folder": "Hunyuan3D-2-vanilla",
        "script": "gradio_app.py",
        "parameters": [
            {"name": "_enable_texture_gen", "type": "boolean", "label": "Enable Texture Generation", "help": "Requires CUDA and MSVC installation. By default, may require over 16GB VRAM"},
            {"name": "--low_vram_mode", "type": "boolean", "label": "Low VRAM Mode", "default": True},
            {"name": "--enable_flashvdm", "type": "boolean", "label": "Enable FlashVDM", "help": "Use with Turbo model", "default": False},
            {"name": "--enable_t23d", "type": "boolean", "label": "Enable Text-to-3D", "help": "Principle: Generate image from prompt first, then generate 3D from image", "default": False},
            {"name": "--model_path", "type": "string", "label": "Model to Use", "default": "tencent/Hunyuan3D-2"},
            {"name": "--subfolder", "type": "string", "label": "Model Subfolder", "default": "hunyuan3d-dit-v2-0"},
            {"name": "--texgen_model_path", "type": "string", "label": "Model for Texture Generation", "default": "tencent/Hunyuan3D-2"},
            {"name": "--mc_algo", "type": "choice", "label": "Marching Cubes Algorithm", "options": [
                  {"name": "mc", "label":"Lewiner et al. (Built-in CPU algorithm in Scikit-image)"},
                  {"name": "dmc", "label":"Differentiable Dual Marching Cubes (Calls DISO)"},
                  ],
                  "default": "mc"},
            {"name": "--host", "type": "string", "label": "HTTP Service Listen Address", "default": "0.0.0.0"},
            {"name": "--port", "type": "string", "label": "HTTP Service Listen Port", "default": "8080"},
        ]
    },
    {
        "name": "Hunyuan3D-2.1",
        "label": "Hunyuan 3D 2.1 | Better Quality, Slower, No MV",
        "folder": "Hunyuan3D-2.1",
        "script": "gradio_app.py",
        "parameters": [
            {"name": "_enable_texture_gen", "type": "boolean", "label": "Enable Texture Generation", "help": "Requires CUDA and MSVC installation. Under default maximum optimization settings, generating mesh requires 3GB VRAM, generating texture requires 10GB VRAM"},
            {"name": "--enable_t23d", "type": "boolean", "label": "Enable Text-to-3D", "help": "Principle: Generate image from prompt first, then generate 3D from image", "default": False},
            {"name": "--low_vram_mode", "type": "boolean", "label": "Low VRAM Mode", "help": "Enabled by default, not conflicting with mmgp optimization; disabling will significantly increase VRAM usage", "default": True},
            {"name": "--profile", "type": "choice", "label": "VRAM Optimization Level", "help":"Default is 5 (maximum optimization), 4 is significantly faster but requires over 40GB memory", "options": [
                  {"name": "1", "label":"1-High Memory, High VRAM"},
                  {"name": "2", "label":"2-High Memory, Low VRAM"},
                  {"name": "3", "label":"3-Low Memory, High VRAM"},
                  {"name": "4", "label":"4-Low Memory, Low VRAM"},
                  {"name": "5", "label":"5-Very Low Memory, Low VRAM"},
                  ],
                  "default": "5"},
        ]
    },
    {
        "name": "API-Hunyuan3D-2",
        "label": "API 2.0 | For Blender Addon, etc.",
        "folder": "Hunyuan3D-2",
        "script": "api_server.py",
        "parameters": [
            {"name": "_enable_texture_gen", "type": "boolean", "label": "Enable Texture Generation", "help": "API mode runs faster but may use more VRAM"},
            {"name": "--model_path", "type": "string", "label": "Model to Use", "default": "tencent/Hunyuan3D-2mini"},
            {"name": "--texgen_model_path", "type": "string", "label": "Model for Texture Generation", "default": "tencent/Hunyuan3D-2"},
            {"name": "--host", "type": "string", "label": "HTTP Service Listen Address", "default": "0.0.0.0"},
            {"name": "--port", "type": "string", "label": "HTTP Service Listen Port", "default": "8081"},
        ]
    },
    {
        "name": "API-Hunyuan3D-2.1",
        "label": "API 2.1 | For Blender Addon, etc.",
        "folder": "Hunyuan3D-2.1",
        "script": "api_server.py",
        "parameters": [
            {"name": "--low_vram_mode", "type": "boolean", "label": "Low VRAM Mode", "default": True},
            {"name": "--model_path", "type": "string", "label": "Model to Use", "default": "tencent/Hunyuan3D-2.1"},
            {"name": "--subfolder", "type": "string", "label": "Model Subfolder", "default": "hunyuan3d-dit-v2-1"},
            {"name": "--host", "type": "string", "label": "HTTP Service Listen Address", "default": "0.0.0.0"},
            {"name": "--port", "type": "string", "label": "HTTP Service Listen Port", "default": "8081"},
        ]
    },
]


# --- 2. Configuration Management ---
class ConfigManager:
    """Responsible for reading and writing JSON configuration files."""
    def __init__(self, filename):
        self.filename = filename

    def load_config(self):
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_config(self, config_data):
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving configuration: {e}")


# --- 3. Background Worker Thread ---
class ProcessWorker(QObject):
    """Executes subprocesses in a separate thread."""
    output_received = Signal(str)
    process_finished = Signal(int)
    status_update = Signal(str)

    def __init__(self):
        super().__init__()
        self.process = None
        self.is_running = False

    def run_process(self, program_data, common_env_vars):

        def pip_install(package):
            pip_cmd = [PYTHON_EXE, "-sm", "pip", "install", package]
            pip_process = subprocess.Popen(
                pip_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
                env=env
            )
            for line in iter(pip_process.stdout.readline, ''):
                self.output_received.emit(line)
            pip_process.wait()
            return pip_process.returncode

        self.is_running = True
        script_path = program_data['script']
        folder = program_data['folder']
        params = program_data['parameters']
        program_name = program_data['program_name']

        self.output_received.emit(f"Current working directory: {RUN_PATH}")
        self.output_received.emit(f"Script location: {SRC_PATH}")

        # Step 1: Prepare environment variables
        env = os.environ.copy()
        for key, value in common_env_vars.items():
            if value:
                env[key] = value
                if key.upper() == "HTTP_PROXY": 
                    env["http_proxy"] = value
                    self.output_received.emit(f"Configured HTTP proxy server: {value}")
                elif key.upper() == "HTTPS_PROXY": 
                    env["https_proxy"] = value
                    self.output_received.emit(f"Configured HTTPS proxy server: {value}")

        # Copy u2net.onnx to user directory if needed
        user_u2net = Path.home() / ".u2net" / "u2net.onnx"
        bundled_u2net = RUN_PATH / "extras" / "u2net.onnx"
        if not user_u2net.exists():
            if bundled_u2net.exists():
                self.output_received.emit("Copying u2net.onnx...")
                user_u2net.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(bundled_u2net, user_u2net)

        # Reinstall huggingface-hub (execute only once)
        marker = SCRIPTS_PATH / ".hf-reinstalled"
        if not marker.exists():
            self.output_received.emit("Reinstalling huggingface-hub...")
            subprocess.run([PYTHON_EXE, "-sm", "pip", "uninstall", "--yes", "huggingface-hub"])
            result = pip_install("huggingface-hub[hf-transfer,cli,hf-xet]")
            if result == 0:
                marker.touch()

        # Step 2: Execute texture generation installation if needed
        enable_texture_gen = params.get("_enable_texture_gen", False)
        if enable_texture_gen:
            self.status_update.emit("Performing compilation and installation for texture generation...")
            self.output_received.emit("--- Starting texture generation setup ---\n")

            self.output_received.emit("Compiling and installing DISO...")
            result = pip_install("diso")
            if result != 0:
                self.output_received.emit("--- Error: Failed to compile and install DISO! ---\n")
                self.output_received.emit("Note: The program can still attempt to run without DISO, but will not be able to use the dmc algorithm\n")
                self.output_received.emit("--- Falling back to compatible mc algorithm ---\n")

            # Generic pip install + pyd copy function
            def _install_and_copy(pkg_dir, pkg_name, pyd_src_rel=None, pyd_dst_rel=None):
                """Compile and install specified package, and copy pyd file if needed"""
                self.status_update.emit(f"Compiling and installing {pkg_name}...")
                self.output_received.emit(f"Compiling and installing {pkg_name}...")
                result = pip_install(str(pkg_dir))
                if result != 0:
                    self.output_received.emit(f"Error: Failed to compile and install {pkg_name}!")
                    self.process_finished.emit(-1)
                    return False
                if pyd_src_rel and pyd_dst_rel:
                    src = Path(pkg_dir) / pyd_src_rel
                    dst = Path(pkg_dir) / pyd_dst_rel
                    if src.exists():
                        shutil.copy(src, dst)
                        self.output_received.emit(f"Copied file: {pyd_dst_rel}")
                return True

            def install_hy3d2():
                base = os.path.join(RUN_PATH, "Hunyuan3D-2", "hy3dgen", "texgen")
                if not _install_and_copy(
                    os.path.join(base, "custom_rasterizer"),
                    "custom_rasterizer"
                ):
                    return False
                if not _install_and_copy(
                    os.path.join(base, "differentiable_renderer"),
                    "differentiable_renderer",
                    os.path.join("build", "lib.win-amd64-cpython-312", "mesh_processor.cp312-win_amd64.pyd"),
                    "mesh_processor.cp312-win_amd64.pyd",
                ):
                    return False
                return True

            def install_hy3d2_vanilla():
                base = os.path.join(RUN_PATH, "Hunyuan3D-2-vanilla", "hy3dgen", "texgen")
                if not _install_and_copy(
                    os.path.join(base, "custom_rasterizer"),
                    "custom_rasterizer"
                ):
                    return False
                if not _install_and_copy(
                    os.path.join(base, "differentiable_renderer"),
                    "differentiable_renderer",
                    os.path.join("build", "lib.win-amd64-cpython-312", "mesh_processor.cp312-win_amd64.pyd"),
                    "mesh_processor.cp312-win_amd64.pyd",
                ):
                    return False
                return True

            def install_hy3d21():
                base = os.path.join(RUN_PATH, "Hunyuan3D-2.1", "hy3dpaint")
                if not _install_and_copy(
                    os.path.join(base, "custom_rasterizer"),
                    "custom_rasterizer"
                ):
                    return False
                if not _install_and_copy(
                    os.path.join(base, "DifferentiableRenderer"),
                    "DifferentiableRenderer",
                    os.path.join("build", "lib.win-amd64-cpython-312", "mesh_inpaint_processor.cp312-win_amd64.pyd"),
                    "mesh_inpaint_processor.cp312-win_amd64.pyd",
                ):
                    return False
                return True

            # Execute different texture generation setup based on the program
            success = True
            if program_name == "Hunyuan3D-2":
                success = install_hy3d2()
            
            elif program_name == "Hunyuan3D-2-vanilla":
                success = install_hy3d2_vanilla()
                
            elif program_name == "Hunyuan3D-2.1":
                success = install_hy3d21()

            elif program_name == "API-Hunyuan3D-2":
                success = install_hy3d2()

            if not success:
                self.output_received.emit("\n--- Texture generation setup failed ---\n")
                self.process_finished.emit(-1)
                return

            self.output_received.emit("\n--- Texture generation setup completed ---\n")

        # Step 3: Switch to corresponding directory and start main script
        program_dir = RUN_PATH / folder
        self.output_received.emit(f"Changing to directory: {program_dir}")
        
        command = [PYTHON_EXE, "-s", script_path]

        # Special handling for model selection parameter in Hunyuan3D-2
        if program_name == "Hunyuan3D-2":
            model_select = params.get("_model_select", "--mini")
            if model_select:
                command.append(model_select)
        
        # Add other parameters
        for key, value in params.items():
            if key.startswith('_'):  # Skip internal parameters
                continue
            if isinstance(value, bool):
                if value: 
                    command.append(key)
            elif isinstance(value, str) and value.strip():
                command.append(key)
                command.append(value)
            elif isinstance(value, (int, float)):
                command.append(key)
                command.append(str(value))

        self.status_update.emit("Starting subprocess...")
        self.output_received.emit(f"\nStarting subprocess...\n")
        self.output_received.emit(f"Executing command:\ncd {program_dir} && {' '.join(command)}\n\n")

        try:
            # Switch to program directory and start process
            self.process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace', env=env,
                cwd=program_dir,  # Key modification: set working directory
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            for line in iter(self.process.stdout.readline, ''):
                if not self.is_running: 
                    break
                self.output_received.emit(line)
            self.process.wait()
            if self.is_running: 
                self.process_finished.emit(self.process.returncode)
        except FileNotFoundError:
            self.output_received.emit(f"Error: Script not found {script_path}\n")
            self.process_finished.emit(-1)
        except Exception as e:
            self.output_received.emit(f"Unexpected error occurred: {e}\n")
            self.process_finished.emit(-1)
        self.is_running = False

    def stop_process(self):
        if self.process and self.is_running:
            self.is_running = False
            try:
                self.process.terminate()
                self.output_received.emit("\n--- Process terminated by user ---\n")
                self.process_finished.emit(-1)
            except Exception as e:
                self.output_received.emit(f"\n--- Error terminating process: {e} ---\n")

# --- 4. UI Interface ---
class SettingsWidget(QWidget):
    """Settings interface."""
    start_requested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.param_widgets = {}
        self.common_widgets = {}

        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        self.common_settings_tab = QWidget()
        self.program_settings_tab = QWidget()
        self.tab_widget.addTab(self.common_settings_tab, "General Settings")
        self.tab_widget.addTab(self.program_settings_tab, "Program Parameters")

        self._create_common_settings_ui()
        self._create_program_settings_ui()

        self.start_button = QPushButton("Save and Start")
        self.start_button.setMinimumHeight(40)
        self.start_button.clicked.connect(self.on_start_clicked)
        main_layout.addWidget(self.start_button)

    def _create_common_settings_ui(self):
        layout = QFormLayout(self.common_settings_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        common_defs = next((p for p in PROGRAMS if p['name'] == "global_settings"), None)
        if not common_defs: return
        for setting in common_defs["common_env_vars"]:
            widget = QLineEdit(setting.get('default', ''))
            self.common_widgets[setting['name']] = widget
            help_label = QLabel(setting.get('help', ''))
            help_label.setWordWrap(True)
            help_label.setStyleSheet("color: #888;")
            layout.addRow(setting['label'], widget)
            layout.addRow(help_label)

    def _create_program_settings_ui(self):
        layout = QVBoxLayout(self.program_settings_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.program_selector = QComboBox()
        for p in PROGRAMS:
            if 'script' in p:
                self.program_selector.addItem(p['label'], p['name'])
        self.program_selector.currentIndexChanged.connect(self.on_program_selected)
        
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Select Program:"))
        selector_layout.addWidget(self.program_selector)
        layout.addLayout(selector_layout)

        self.params_container = QWidget()
        self.params_layout = QFormLayout(self.params_container)
        self.params_layout.setSpacing(15)
        # *** UI FIX: Set alignment for labels and fields ***
        self.params_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.params_container)
        layout.addStretch()

    def on_program_selected(self):
        """Update parameter UI when user selects a new program from dropdown."""
        main_window = self.window()
        if not (main_window and hasattr(main_window, 'full_config')):
            return

        current_program_name = self.program_selector.currentData()
        if not current_program_name:
            return
            
        program_def = next((p for p in PROGRAMS if p['name'] == current_program_name), None)
        program_config = main_window.full_config.get(current_program_name, {})
        
        if program_def:
            self.update_params_ui(program_def, program_config)

    def update_params_ui(self, program_def, program_config):
        """Create or update parameter UI based on given program definition and configuration data."""
        for widget in self.param_widgets.values():
            widget.deleteLater()
        self.param_widgets.clear()
        while self.params_layout.rowCount() > 0:
            self.params_layout.removeRow(0)

        for param in program_def.get("parameters", []):
            label, name, p_type = param['label'], param['name'], param['type']
            
            current_value = program_config.get(name, param.get('default'))

            widget = None
            if p_type == "boolean":
                widget = QCheckBox()
                widget.setChecked(current_value is True)
            elif p_type == "string":
                widget = QLineEdit(str(current_value) if current_value is not None else "")
                widget.setPlaceholderText(f"Default: '{param.get('default', '')}'")
            elif p_type == "choice":
                widget = QComboBox()
                for option in param['options']:
                    widget.addItem(option['label'], option['name'])
                if current_value is not None:
                    index = widget.findData(current_value)
                    if index != -1: widget.setCurrentIndex(index)
            
            if widget:
                widget.setToolTip(param.get('help', ''))
                self.param_widgets[name] = widget
                
                help_label = QLabel(param.get('help', ''))
                help_label.setWordWrap(True)
                help_label.setStyleSheet("color: #888;")

                # *** UI FIX: Place controls and help text in a vertically laid out container ***
                field_container = QWidget()
                field_layout = QVBoxLayout(field_container)
                field_layout.setContentsMargins(0, 0, 0, 0)
                field_layout.setSpacing(5)
                field_layout.addWidget(widget)
                field_layout.addWidget(help_label)
                
                self.params_layout.addRow(label, field_container)

    def on_start_clicked(self):
        selected_program_name = self.program_selector.currentData()
        program_def = next((p for p in PROGRAMS if p['name'] == selected_program_name), None)
        
        common_env_vars = {name: widget.text() for name, widget in self.common_widgets.items()}
        
        parameters = {}
        for name, widget in self.param_widgets.items():
            if isinstance(widget, QCheckBox): parameters[name] = widget.isChecked()
            elif isinstance(widget, QLineEdit): parameters[name] = widget.text()
            elif isinstance(widget, QComboBox): parameters[name] = widget.currentData()

        self.start_requested.emit({
            "program_name": selected_program_name, 
            "script": program_def['script'],
            "folder": program_def['folder'],  # Add this line
            "definition": program_def, 
            "parameters": parameters, 
            "common_env_vars": common_env_vars
        })

    def apply_config(self, config):
        """Populate the entire UI based on complete configuration data (usually called at startup)."""
        common_conf = config.get("global_settings", {})
        for name, widget in self.common_widgets.items():
            widget.setText(str(common_conf.get(name, '')))

        last_program = config.get("last_selected_program")
        
        self.program_selector.blockSignals(True)
        if last_program:
            index = self.program_selector.findData(last_program)
            if index != -1:
                self.program_selector.setCurrentIndex(index)
        self.program_selector.blockSignals(False)
        
        self.on_program_selected()


    def collect_current_ui_config(self):
        """Collect only the values currently on the UI interface."""
        current_program = self.program_selector.currentData()
        config = {
            "last_selected_program": current_program,
            "global_settings": {name: widget.text() for name, widget in self.common_widgets.items()},
            current_program: {}
        }
        for name, widget in self.param_widgets.items():
            if isinstance(widget, QCheckBox): config[current_program][name] = widget.isChecked()
            elif isinstance(widget, QLineEdit): config[current_program][name] = widget.text()
            elif isinstance(widget, QComboBox): config[current_program][name] = widget.currentData()
        return config

class RunningWidget(QWidget):
    """Running interface."""
    stop_requested = Signal()
    back_to_settings_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.output_display = QPlainTextEdit("Subprocess output will appear here...")
        self.output_display.setReadOnly(True)
        self.output_display.setStyleSheet("font-family: Cascadia Mono, Consolas, Courier New, monospace;")
        layout.addWidget(self.output_display)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setMinimumHeight(40)
        self.stop_button.clicked.connect(self.stop_requested)
        
        self.back_button = QPushButton("Back to Settings")
        self.back_button.setMinimumHeight(40)
        self.back_button.clicked.connect(self.back_to_settings_requested)
        self.back_button.setEnabled(False) 

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.back_button)
        layout.addLayout(button_layout)

    def append_output(self, text): self.output_display.appendPlainText(text.strip())
    def clear_output(self): self.output_display.clear()
    def set_running_state(self, is_running):
        self.stop_button.setEnabled(is_running)
        self.back_button.setEnabled(not is_running)

# --- 5. Main Window ---
class MainWindow(QMainWindow):
    """Main window."""
    request_worker_run = Signal(dict, dict)
    request_worker_stop = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hunyuan 3D 2 Series Launcher")
        self.setGeometry(100, 100, 900, 700)

        self.config_manager = ConfigManager(CONFIG_FILE)
        self.full_config = self.load_full_config()

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        self.settings_page = SettingsWidget()
        self.running_page = RunningWidget()
        self.stacked_widget.addWidget(self.settings_page)
        self.stacked_widget.addWidget(self.running_page)

        self._setup_worker_thread()

        self.settings_page.start_requested.connect(self.start_process)
        self.running_page.back_to_settings_requested.connect(self.show_settings_page)
        self.running_page.stop_requested.connect(self.request_worker_stop)

        self.settings_page.apply_config(self.full_config)

    def load_full_config(self):
        """Load saved configuration and complete missing programs or parameters with default values."""
        saved_config = self.config_manager.load_config()
        
        default_config = {"last_selected_program": ""}
        for p in PROGRAMS:
            program_name = p['name']
            if "common_env_vars" in p:
                default_config[program_name] = {
                    setting['name']: setting['default'] for setting in p['common_env_vars']
                }
            elif "parameters" in p:
                default_config[program_name] = {
                    param['name']: param.get('default') for param in p['parameters']
                }
                if not default_config.get("last_selected_program"):
                    default_config["last_selected_program"] = program_name

        for key, value in saved_config.items():
            if isinstance(value, dict):
                if key not in default_config:
                    default_config[key] = {}
                default_config[key].update(value)
            else:
                default_config[key] = value
                
        return default_config


    def _setup_worker_thread(self):
        self.worker_thread = QThread()
        self.worker = ProcessWorker()
        self.worker.moveToThread(self.worker_thread)
        self.worker.output_received.connect(self.running_page.append_output)
        self.worker.process_finished.connect(self.process_finished)
        self.worker.status_update.connect(self.statusBar().showMessage)
        self.request_worker_run.connect(self.worker.run_process)
        self.request_worker_stop.connect(self.worker.stop_process)
        self.worker_thread.start()

    def save_settings(self):
        """Collect current UI values, update to full configuration, then save."""
        ui_config = self.settings_page.collect_current_ui_config()
        
        current_program_name = ui_config['last_selected_program']
        self.full_config['last_selected_program'] = current_program_name
        self.full_config['global_settings'].update(ui_config['global_settings'])
        if current_program_name in self.full_config:
            self.full_config[current_program_name].update(ui_config[current_program_name])
        else:
            self.full_config[current_program_name] = ui_config[current_program_name]

        self.config_manager.save_config(self.full_config)
        self.statusBar().showMessage("Configuration saved!", 3000)

    def start_process(self, data):
        self.save_settings()
        self.running_page.clear_output()
        self.stacked_widget.setCurrentWidget(self.running_page)
        self.running_page.set_running_state(True)
        self.statusBar().showMessage("Preparing to start...")
        self.request_worker_run.emit(data, data['common_env_vars'])

    def process_finished(self, exit_code):
        self.running_page.append_output(f"\n--- Program execution ended (Exit code: {exit_code}) ---")
        self.running_page.set_running_state(False)
        self.statusBar().showMessage("Task completed", 5000)

    def show_settings_page(self):
        self.stacked_widget.setCurrentWidget(self.settings_page)

    def closeEvent(self, event):
        self.worker_thread.quit()
        self.worker_thread.wait()
        event.accept()

# --- 6. Program Entry ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
