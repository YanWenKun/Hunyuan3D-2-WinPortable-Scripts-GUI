# -*- coding: utf-8 -*-
import sys
import os
import json
import shutil
import subprocess
import psutil
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QFormLayout, QComboBox, QPlainTextEdit,
    QLineEdit, QCheckBox, QTabWidget, QLabel
)
from PySide6.QtCore import QObject, QThread, Signal, Qt, Slot

RUN_PATH = Path.cwd()
SRC_PATH = Path(__file__).resolve()
SCRIPTS_PATH = RUN_PATH / "python_standalone" / "Scripts"
PYTHON_EXE = sys.executable
CONFIG_FILE = os.path.join(RUN_PATH, "launcher_config.json")


# --- 1. 程序与参数定义 ---
PROGRAMS = [
    {
        "name": "global_settings",
        "label": "通用设置",
        "common_env_vars": [
            {"name": "HTTP_PROXY", "type": "string", "label": "HTTP 代理服务器", "help": "设置 HTTP_PROXY 环境变量，例: http://localhost:1080", "default": ""},
            {"name": "HTTPS_PROXY", "type": "string", "label": "HTTPS 代理服务器", "help": "设置 HTTPS_PROXY 环境变量，例: http://localhost:1080", "default": ""},
            {"name": "PIP_INDEX_URL", "type": "string", "label": "PyPI 镜像", "help": "安装 Python 包的 PyPI 镜像源", "default": "https://mirrors.cernet.edu.cn/pypi/web/simple"},
            {"name": "HF_ENDPOINT", "type": "string", "label": "HuggingFace 镜像", "help": "HuggingFace Hub 下载使用的镜像源", "default": "https://hf-mirror.com"},
        ],
    },
    {
        "name": "Hunyuan3D-2",
        "label": "混元 3D 2.0 | 功能全面",
        "folder": "Hunyuan3D-2",
        "script": "gradio_app.py",
        "parameters": [
            {"name": "_enable_texture_gen", "type": "boolean", "label": "启用纹理生成功能", "help": "需要安装CUDA与MSVC。默认设置下，生成网格需4G显存，生成纹理需6G显存"},
            {"name": "_model_select", "type": "choice", "label": "模型选择", "options": [
                  {"name": "--mini", "label":"单视图输入 - 迷你模型: 默认选项，适合大多数情况"},
                  {"name": "--h2", "label":"单视图输入 - 标准模型: 需要更多显存"},
                  {"name": "--mv", "label":"多视图输入（MV）"},
                  ],
                  "default": "--mini"},
            {"name": "--turbo", "type": "boolean", "label": "使用 Turbo 模型", "help": "默认启用，速度显著更快，质量轻微下降", "default": True},
            {"name": "--enable_t23d", "type": "boolean", "label": "启用文生3D功能", "help": "原理：先由提示词生图，再由图生3D", "default": False},
            {"name": "--profile", "type": "choice", "label": "显存优化等级", "help":"选择 mmgp 优化等级以启用量化、分片、显存卸载等机制", "options": [
                  {"name": "1", "label":"1-高内存，高显存"},
                  {"name": "2", "label":"2-高内存，低显存"},
                  {"name": "3", "label":"3-低内存，高显存"},
                  {"name": "4", "label":"4-低内存，低显存"},
                  {"name": "5", "label":"5-超低内存，低显存"},
                  ],
                  "default": "4"},
        ]
    },
    {
        "name": "Hunyuan3D-2-vanilla",
        "label": "混元 3D 2.0 官方代码 | 适合显存充裕的用户",
        "folder": "Hunyuan3D-2-vanilla",
        "script": "gradio_app.py",
        "parameters": [
            {"name": "_enable_texture_gen", "type": "boolean", "label": "启用纹理生成功能", "help": "需要安装CUDA与MSVC。默认设置下，可能需要16G以上显存"},
            {"name": "--low_vram_mode", "type": "boolean", "label": "低显存模式", "default": True},
            {"name": "--enable_flashvdm", "type": "boolean", "label": "启用 FlashVDM", "help": "配合 Turbo 模型使用", "default": False},
            {"name": "--enable_t23d", "type": "boolean", "label": "启用文生3D功能", "help": "原理：先由提示词生图，再由图生3D", "default": False},
            {"name": "--model_path", "type": "string", "label": "使用模型", "default": "tencent/Hunyuan3D-2"},
            {"name": "--subfolder", "type": "string", "label": "模型子目录", "default": "hunyuan3d-dit-v2-0"},
            {"name": "--texgen_model_path", "type": "string", "label": "纹理功能使用模型", "default": "tencent/Hunyuan3D-2"},
            {"name": "--mc_algo", "type": "choice", "label": "Marching Cubes 算法", "options": [
                  {"name": "mc", "label":"Lewiner et al.（Scikit-image 内置 CPU 算法）"},
                  {"name": "dmc", "label":"Differentiable Dual Marching Cubes（调用 DISO）"},
                  ],
                  "default": "mc"},
            {"name": "--host", "type": "string", "label": "HTTP 服务监听地址", "default": "0.0.0.0"},
            {"name": "--port", "type": "string", "label": "HTTP 服务监听端口", "default": "8080"},
        ]
    },
    {
        "name": "Hunyuan3D-2.1",
        "label": "混元 3D 2.1 | 质量更佳，运行更慢，无 MV",
        "folder": "Hunyuan3D-2.1",
        "script": "gradio_app.py",
        "parameters": [
            {"name": "_enable_texture_gen", "type": "boolean", "label": "启用纹理生成功能", "help": "需要安装CUDA与MSVC。默认最大优化设置下，生成网格需3G显存，生成纹理需10G显存"},
            {"name": "--low_vram_mode", "type": "boolean", "label": "低显存模式", "help": "默认启用，与 mmgp 优化不冲突，关闭后显存占用明显上升", "default": True},
            {"name": "--profile", "type": "choice", "label": "显存优化等级", "help":"默认为5（最大优化），4会显著更快，但需要40G以上内存", "options": [
                  {"name": "1", "label":"1-高内存，高显存"},
                  {"name": "2", "label":"2-高内存，低显存"},
                  {"name": "3", "label":"3-低内存，高显存"},
                  {"name": "4", "label":"4-低内存，低显存"},
                  {"name": "5", "label":"5-超低内存，低显存"},
                  ],
                  "default": "5"},
        ]
    },
    {
        "name": "API-Hunyuan3D-2",
        "label": "API 2.0 | 用于 Blender Addon 等",
        "folder": "Hunyuan3D-2",
        "script": "api_server.py",
        "parameters": [
            {"name": "_enable_texture_gen", "type": "boolean", "label": "启用纹理生成功能", "help": "API 模式运行较快，但可能显存占用较多"},
            {"name": "--model_path", "type": "string", "label": "使用模型", "default": "tencent/Hunyuan3D-2mini"},
            {"name": "--texgen_model_path", "type": "string", "label": "纹理功能使用模型", "default": "tencent/Hunyuan3D-2"},
            {"name": "--host", "type": "string", "label": "HTTP 服务监听地址", "default": "0.0.0.0"},
            {"name": "--port", "type": "string", "label": "HTTP 服务监听端口", "default": "8081"},
        ]
    },
    {
        "name": "API-Hunyuan3D-2.1",
        "label": "API 2.1 | 用于 Blender Addon 等",
        "folder": "Hunyuan3D-2.1",
        "script": "api_server.py",
        "parameters": [
            {"name": "--low_vram_mode", "type": "boolean", "label": "低显存模式", "default": True},
            {"name": "--model_path", "type": "string", "label": "使用模型", "default": "tencent/Hunyuan3D-2.1"},
            {"name": "--subfolder", "type": "string", "label": "模型子目录", "default": "hunyuan3d-dit-v2-1"},
            {"name": "--host", "type": "string", "label": "HTTP 服务监听地址", "default": "0.0.0.0"},
            {"name": "--port", "type": "string", "label": "HTTP 服务监听端口", "default": "8081"},
        ]
    },
]


# --- 2. 配置管理 ---
class ConfigManager:
    """负责读写 JSON 配置文件。"""
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
            print(f"保存配置时出错: {e}")


# --- 3. 后台工作线程 ---
class ProcessWorker(QObject):
    """在独立线程中执行子进程。"""
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

        self.output_received.emit(f"当前运行路径: {RUN_PATH}")
        self.output_received.emit(f"脚本所在路径: {SRC_PATH}")

        # 步骤 1: 准备环境变量
        env = os.environ.copy()
        for key, value in common_env_vars.items():
            if value:
                env[key] = value
                if key.upper() == "HTTP_PROXY": 
                    env["http_proxy"] = value
                    self.output_received.emit(f"配置 HTTP 代理服务器: {value}")
                elif key.upper() == "HTTPS_PROXY": 
                    env["https_proxy"] = value
                    self.output_received.emit(f"配置 HTTPS 代理服务器: {value}")

        # 按需复制 u2net.onnx 到用户目录
        user_u2net = Path.home() / ".u2net" / "u2net.onnx"
        bundled_u2net = RUN_PATH / "extras" / "u2net.onnx"
        if not user_u2net.exists():
            if bundled_u2net.exists():
                self.output_received.emit("正在复制 u2net.onnx...")
                user_u2net.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(bundled_u2net, user_u2net)

        # 重新安装 huggingface-hub（仅执行一次）
        marker = SCRIPTS_PATH / ".hf-reinstalled"
        if not marker.exists():
            self.output_received.emit("正在重新安装 huggingface-hub...")
            subprocess.run([PYTHON_EXE, "-sm", "pip", "uninstall", "--yes", "huggingface-hub"])
            result = pip_install("huggingface-hub[cli,hf-xet]==0.36.0")
            if result == 0:
                marker.touch()

        # 步骤 2: 如果需要，执行纹理生成安装
        enable_texture_gen = params.get("_enable_texture_gen", False)
        if enable_texture_gen:
            self.status_update.emit("正在为纹理生成功能执行编译安装...")
            self.output_received.emit("--- 开始纹理生成功能设置 ---\n")

            self.output_received.emit("编译安装 DISO...")
            result = pip_install("diso")
            if result != 0:
                self.output_received.emit("--- 错误: 编译安装 DISO 失败！ ---\n")
                self.output_received.emit("注意: 程序没有 DISO 依然可以尝试运行，但将无法使用 dmc 算法\n")
                self.output_received.emit("--- 回退到兼容模式 mc 算法 ---\n")

            # 通用的 pip 安装 + pyd 复制函数
            def _install_and_copy(pkg_dir, pkg_name, pyd_src_rel=None, pyd_dst_rel=None):
                """编译安装指定包，并按需复制 pyd 文件"""
                self.status_update.emit(f"编译安装 {pkg_name}...")
                self.output_received.emit(f"编译安装 {pkg_name}...")
                result = pip_install(str(pkg_dir))
                if result != 0:
                    self.output_received.emit(f"错误: 编译安装 {pkg_name} 失败！")
                    self.process_finished.emit(-1)
                    return False
                if pyd_src_rel and pyd_dst_rel:
                    src = Path(pkg_dir) / pyd_src_rel
                    dst = Path(pkg_dir) / pyd_dst_rel
                    if src.exists():
                        shutil.copy(src, dst)
                        self.output_received.emit(f"复制文件: {pyd_dst_rel}")
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

            # 根据不同的程序执行不同的纹理生成设置
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
                self.output_received.emit("\n--- 纹理生成功能设置失败 ---\n")
                self.process_finished.emit(-1)
                return

            self.output_received.emit("\n--- 纹理生成功能设置完毕 ---\n")

        # 步骤 3: 切换到对应目录并启动主脚本
        program_dir = RUN_PATH / folder
        self.output_received.emit(f"切换到目录: {program_dir}")
        
        command = [PYTHON_EXE, "-s", script_path]

        # 特殊处理混元3D-2的模型选择参数
        if program_name == "Hunyuan3D-2":
            model_select = params.get("_model_select", "--mini")
            if model_select:
                command.append(model_select)

        # 未勾选时，主动禁用材质生成
        if program_name in ["Hunyuan3D-2", "Hunyuan3D-2-vanilla", "Hunyuan3D-2.1"]:
            if enable_texture_gen == False:
                command.append("--disable_tex")

        if program_name == "API-Hunyuan3D-2":
            if enable_texture_gen == True:
                command.append("--enable_tex")

        # 添加其他参数
        for key, value in params.items():
            if key.startswith('_'):  # 跳过内部参数
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

        self.status_update.emit("正在启动子程序...")
        self.output_received.emit(f"\n正在启动子程序...\n")
        self.output_received.emit(f"执行命令:\ncd {program_dir} && {' '.join(command)}\n\n")

        try:
            # 切换到程序目录并启动进程
            self.process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace', env=env,
                cwd=program_dir,  # 关键修改：设置工作目录
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
            self.output_received.emit(f"错误: 脚本未找到 {script_path}\n")
            self.process_finished.emit(-1)
        except Exception as e:
            self.output_received.emit(f"发生意外错误: {e}\n")
            self.process_finished.emit(-1)
        self.is_running = False

    def _kill_process_tree(self, pid):
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            for child in children:
                child.kill()
            parent.kill()
            psutil.wait_procs(children + [parent], timeout=3)
            return True
        except psutil.NoSuchProcess:
            return True
        except Exception as e:
            self.output_received.emit(f"--- 终止进程时发生意外错误: {e} ---\n")
            return False

    @Slot()
    def stop_process(self):
        if self.process and self.is_running:
            self.is_running = False
            self.output_received.emit("\n--- 正在尝试终止进程... ---\n")
            _pid = self.process.pid
            _success = self._kill_process_tree(_pid)
            if _success:
                self.output_received.emit(f"--- 进程树 (PID: {_pid}) 已被终止。 ---\n")
            else:
                self.output_received.emit(f"--- 警告: 无法确认进程是否已被终止。 ---\n")
            self.process_finished.emit(-1) # 发送一个表示非正常退出的信号

# --- 4. UI 界面 ---
class SettingsWidget(QWidget):
    """设置界面。"""
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
        self.tab_widget.addTab(self.common_settings_tab, "通用设置")
        self.tab_widget.addTab(self.program_settings_tab, "程序参数")

        self._create_common_settings_ui()
        self._create_program_settings_ui()

        self.start_button = QPushButton("保存并启动")
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
        selector_layout.addWidget(QLabel("选择程序:"))
        selector_layout.addWidget(self.program_selector)
        layout.addLayout(selector_layout)

        self.params_container = QWidget()
        self.params_layout = QFormLayout(self.params_container)
        self.params_layout.setSpacing(15)
        self.params_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.params_container)
        layout.addStretch()

    def on_program_selected(self):
        """当用户在下拉菜单中选择一个新程序时，更新参数UI。"""
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
        """根据给定的程序定义和配置数据，创建或更新参数UI。"""
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
                widget.setPlaceholderText(f"默认值: '{param.get('default', '')}'")
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
            "folder": program_def['folder'],
            "definition": program_def, 
            "parameters": parameters, 
            "common_env_vars": common_env_vars
        })

    def apply_config(self, config):
        """根据完整的配置数据填充整个UI (通常在启动时调用)。"""
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
        """仅收集当前UI界面上的值。"""
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
    """运行界面。"""
    stop_requested = Signal()
    back_to_settings_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.output_display = QPlainTextEdit("子程序输出将显示在这里...")
        self.output_display.setReadOnly(True)
        self.output_display.setStyleSheet("font-family: Cascadia Mono, Consolas, Courier New, monospace;")
        layout.addWidget(self.output_display)

        self.stop_button = QPushButton("停止")
        self.stop_button.setMinimumHeight(40)
        self.stop_button.clicked.connect(self.stop_requested)
        
        self.back_button = QPushButton("返回设置")
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

# --- 5. 主窗口 ---
class MainWindow(QMainWindow):
    """主窗口。"""
    request_worker_run = Signal(dict, dict)
    request_worker_stop = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("混元 3D 2 系列启动器")
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
        """加载已存配置，并用默认值补全缺失的程序或参数。"""
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
        """收集当前UI的值，更新到完整配置中，然后保存。"""
        ui_config = self.settings_page.collect_current_ui_config()
        
        current_program_name = ui_config['last_selected_program']
        self.full_config['last_selected_program'] = current_program_name
        self.full_config['global_settings'].update(ui_config['global_settings'])
        if current_program_name in self.full_config:
            self.full_config[current_program_name].update(ui_config[current_program_name])
        else:
            self.full_config[current_program_name] = ui_config[current_program_name]

        self.config_manager.save_config(self.full_config)
        self.statusBar().showMessage("配置已保存!", 3000)

    def start_process(self, data):
        self.save_settings()
        self.running_page.clear_output()
        self.stacked_widget.setCurrentWidget(self.running_page)
        self.running_page.set_running_state(True)
        self.statusBar().showMessage("正在准备启动...")
        self.request_worker_run.emit(data, data['common_env_vars'])

    def process_finished(self, exit_code):
        self.running_page.append_output(f"\n--- 程序执行结束 (退出码: {exit_code}) ---")
        self.running_page.set_running_state(False)
        self.statusBar().showMessage("任务完成", 5000)

    def show_settings_page(self):
        self.stacked_widget.setCurrentWidget(self.settings_page)

    def closeEvent(self, event):
        # 确保在关闭窗口前，先尝试停止正在运行的子进程
        if self.worker.is_running:
            self.statusBar().showMessage("Closing... Stopping background processes...")
            self.worker.is_running = False
            try:
                if self.worker.process:
                    self.worker._kill_process_tree(self.worker.process.pid)
            except Exception:
                # 回退：发出信号并短暂等待 worker 结束
                self.request_worker_stop.emit()
                import time
                for _ in range(50):
                    if not self.worker.is_running:
                        break
                    time.sleep(0.05)

        # 现在请求已发送（或已直接停止），退出并等待线程
        self.worker_thread.quit()
        self.worker_thread.wait(2500) # 最多等待2.5秒
        if self.worker_thread.isRunning():
            self.worker_thread.terminate()
        event.accept()

# --- 6. 程序入口 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
