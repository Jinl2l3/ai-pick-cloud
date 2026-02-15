import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QTextEdit, QPushButton,
    QGroupBox, QFormLayout, QMessageBox, QSpinBox,
    QTabWidget, QWidget, QCheckBox
)
from PyQt5.QtCore import Qt
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    load_settings, save_settings, get_default_settings,
    DEFAULT_MODELS, DEFAULT_OLLAMA_URL, DEFAULT_OLLAMA_MODEL,
    CATEGORIES, DEFAULT_PROMPT, DEFAULT_MAX_CONCURRENT,
    DEFAULT_VIDEO_FRAME_COUNT, DEFAULT_OPERATION_MODE,
    DEFAULT_TIME_SOURCE, DEFAULT_FOLDER_STRUCTURE,
    DEFAULT_VIDEO_FRAME_MODE,
    DEFAULT_API_TYPE, DEFAULT_NETWORK_API_URL, DEFAULT_NETWORK_API_KEY,
    DEFAULT_NETWORK_API_MODEL, DEFAULT_NETWORK_API_MAX_CONCURRENT,
    DEFAULT_NETWORK_API_MODELS
)
from core.ollama_client import OllamaClient
from core.network_client import NetworkClient


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(650)
        self.setMinimumHeight(600)
        self.settings = load_settings()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        tab_widget = QTabWidget()

        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)

        # API Type Selection
        api_group = QGroupBox("API 设置")
        api_layout = QFormLayout()
        
        self.api_type_combo = QComboBox()
        self.api_type_combo.addItem("Ollama (本地)", "ollama")
        self.api_type_combo.addItem("网络 API", "network")
        api_type = self.settings.get("api_type", DEFAULT_API_TYPE)
        api_index = self.api_type_combo.findData(api_type)
        if api_index >= 0:
            self.api_type_combo.setCurrentIndex(api_index)
        api_layout.addRow("API 类型:", self.api_type_combo)
        api_group.setLayout(api_layout)

        ollama_group = QGroupBox("Ollama 设置")
        ollama_layout = QFormLayout()

        self.url_edit = QLineEdit(self.settings.get("ollama_url", DEFAULT_OLLAMA_URL))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.refresh_models_btn = QPushButton("刷新模型")
        self.refresh_models_btn.clicked.connect(self.refresh_models)

        model_layout = QHBoxLayout()
        model_layout.addWidget(self.model_combo)
        model_layout.addWidget(self.refresh_models_btn)

        ollama_layout.addRow("服务地址:", self.url_edit)
        ollama_layout.addRow("模型:", model_layout)
        
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setMinimum(1)
        self.concurrent_spin.setMaximum(10)
        self.concurrent_spin.setValue(self.settings.get("max_concurrent", DEFAULT_MAX_CONCURRENT))
        ollama_layout.addRow("最大并发数:", self.concurrent_spin)
        
        ollama_group.setLayout(ollama_layout)
        
        # Network API Settings
        network_group = QGroupBox("网络 API 设置")
        network_layout = QFormLayout()
        
        self.network_api_url_edit = QLineEdit(self.settings.get("network_api_url", DEFAULT_NETWORK_API_URL))
        self.network_api_key_edit = QLineEdit(self.settings.get("network_api_key", DEFAULT_NETWORK_API_KEY))
        # 显示API key为明文
        self.network_api_key_edit.setEchoMode(QLineEdit.Normal)
        self.network_api_model_combo = QComboBox()
        self.network_api_model_combo.setEditable(True)
        
        self.test_api_btn = QPushButton("测试连接")
        self.test_api_btn.clicked.connect(self.test_network_api)
        
        test_layout = QHBoxLayout()
        test_layout.addWidget(self.test_api_btn)
        
        self.network_concurrent_spin = QSpinBox()
        self.network_concurrent_spin.setMinimum(1)
        self.network_concurrent_spin.setMaximum(10)
        self.network_concurrent_spin.setValue(self.settings.get("network_api_max_concurrent", DEFAULT_NETWORK_API_MAX_CONCURRENT))
        
        network_layout.addRow("API URL:", self.network_api_url_edit)
        network_layout.addRow("API Key:", self.network_api_key_edit)
        network_layout.addRow("模型:", self.network_api_model_combo)
        network_layout.addRow("最大并发数:", self.network_concurrent_spin)
        network_layout.addRow(test_layout)
        
        network_group.setLayout(network_layout)

        operation_group = QGroupBox("操作设置")
        operation_layout = QFormLayout()

        self.operation_combo = QComboBox()
        self.operation_combo.addItem("移动文件", "move")
        self.operation_combo.addItem("复制文件", "copy")
        op_mode = self.settings.get("operation_mode", DEFAULT_OPERATION_MODE)
        op_index = self.operation_combo.findData(op_mode)
        if op_index >= 0:
            self.operation_combo.setCurrentIndex(op_index)
        operation_layout.addRow("操作模式:", self.operation_combo)

        self.time_source_combo = QComboBox()
        self.time_source_combo.addItem("最早时间 (创建/修改/访问)", "earliest")
        self.time_source_combo.addItem("最晚时间 (创建/修改/访问)", "latest")
        self.time_source_combo.addItem("创建时间", "birth")
        self.time_source_combo.addItem("修改时间", "modify")
        self.time_source_combo.addItem("访问时间", "access")
        time_source = self.settings.get("time_source", DEFAULT_TIME_SOURCE)
        ts_index = self.time_source_combo.findData(time_source)
        if ts_index >= 0:
            self.time_source_combo.setCurrentIndex(ts_index)
        operation_layout.addRow("时间来源:", self.time_source_combo)

        self.folder_structure_combo = QComboBox()
        self.folder_structure_combo.addItem("种类/时间 (美食/2022年/1月)", "category_time")
        self.folder_structure_combo.addItem("时间/种类 (2022年/1月/美食)", "time_category")
        folder_structure = self.settings.get("folder_structure", DEFAULT_FOLDER_STRUCTURE)
        fs_index = self.folder_structure_combo.findData(folder_structure)
        if fs_index >= 0:
            self.folder_structure_combo.setCurrentIndex(fs_index)
        operation_layout.addRow("目录结构:", self.folder_structure_combo)

        operation_group.setLayout(operation_layout)

        general_layout.addWidget(api_group)
        general_layout.addWidget(ollama_group)
        general_layout.addWidget(network_group)
        general_layout.addWidget(operation_group)
        general_layout.addStretch()

        media_tab = QWidget()
        media_layout = QVBoxLayout(media_tab)

        image_group = QGroupBox("图片设置")
        image_layout = QVBoxLayout()
        self.process_images_check = QCheckBox("处理图片")
        self.process_images_check.setChecked(self.settings.get("process_images", True))
        image_layout.addWidget(self.process_images_check)
        image_group.setLayout(image_layout)

        video_group = QGroupBox("视频设置")
        video_layout = QFormLayout()
        self.process_videos_check = QCheckBox("处理视频")
        self.process_videos_check.setChecked(self.settings.get("process_videos", True))
        
        self.video_frame_spin = QSpinBox()
        self.video_frame_spin.setMinimum(1)
        self.video_frame_spin.setMaximum(10)
        self.video_frame_spin.setValue(self.settings.get("video_frame_count", DEFAULT_VIDEO_FRAME_COUNT))
        self.video_frame_spin.setSuffix(" 帧")
        
        self.video_frame_mode_combo = QComboBox()
        self.video_frame_mode_combo.addItem("中间帧", "middle")
        self.video_frame_mode_combo.addItem("随机帧", "random")
        self.video_frame_mode_combo.addItem("开头附近", "start")
        self.video_frame_mode_combo.addItem("结尾附近", "end")
        self.video_frame_mode_combo.addItem("首帧", "first")
        self.video_frame_mode_combo.addItem("尾帧", "last")
        frame_mode = self.settings.get("video_frame_mode", DEFAULT_VIDEO_FRAME_MODE)
        fm_index = self.video_frame_mode_combo.findData(frame_mode)
        if fm_index >= 0:
            self.video_frame_mode_combo.setCurrentIndex(fm_index)
        
        video_layout.addRow(self.process_videos_check)
        video_layout.addRow("抽帧数量:", self.video_frame_spin)
        video_layout.addRow("抽帧模式:", self.video_frame_mode_combo)
        video_group.setLayout(video_layout)

        media_layout.addWidget(image_group)
        media_layout.addWidget(video_group)
        media_layout.addStretch()

        categories_tab = QWidget()
        categories_layout = QVBoxLayout(categories_tab)

        categories_group = QGroupBox("分类类别")
        cat_layout = QVBoxLayout()
        self.categories_edit = QTextEdit()
        categories_text = "\n".join(self.settings.get("categories", CATEGORIES))
        self.categories_edit.setPlainText(categories_text)
        self.categories_edit.setPlaceholderText("每行一个类别")
        cat_layout.addWidget(self.categories_edit)
        categories_group.setLayout(cat_layout)

        prompt_group = QGroupBox("提示词 (Prompt)")
        prompt_layout = QVBoxLayout()
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlainText(self.settings.get("prompt", DEFAULT_PROMPT))
        self.prompt_edit.setPlaceholderText("使用 {categories} 表示分类列表的占位符")
        prompt_layout.addWidget(self.prompt_edit)
        prompt_group.setLayout(prompt_layout)

        categories_layout.addWidget(categories_group)
        categories_layout.addWidget(prompt_group)

        tab_widget.addTab(general_tab, "常规")
        tab_widget.addTab(media_tab, "媒体")
        tab_widget.addTab(categories_tab, "分类")

        button_layout = QHBoxLayout()
        self.reset_btn = QPushButton("重置默认")
        self.reset_btn.clicked.connect(self.reset_defaults)
        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.ok_btn)

        layout.addWidget(tab_widget)
        layout.addLayout(button_layout)

        self.populate_models()

    def populate_models(self):
        # Populate Ollama models
        current_model = self.settings.get("ollama_model", DEFAULT_OLLAMA_MODEL)
        available_models = self.settings.get("available_models", DEFAULT_MODELS)
        
        self.model_combo.clear()
        for model in available_models:
            self.model_combo.addItem(model)
        
        index = self.model_combo.findText(current_model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
        else:
            self.model_combo.addItem(current_model)
            self.model_combo.setCurrentText(current_model)
        
        # Populate Network API models
        current_network_model = self.settings.get("network_api_model", DEFAULT_NETWORK_API_MODEL)
        available_network_models = self.settings.get("available_network_models", DEFAULT_NETWORK_API_MODELS)
        
        self.network_api_model_combo.clear()
        for model in available_network_models:
            self.network_api_model_combo.addItem(model)
        
        network_index = self.network_api_model_combo.findText(current_network_model)
        if network_index >= 0:
            self.network_api_model_combo.setCurrentIndex(network_index)
        else:
            self.network_api_model_combo.addItem(current_network_model)
            self.network_api_model_combo.setCurrentText(current_network_model)

    def refresh_models(self):
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "警告", "请先填写 Ollama 服务地址")
            return

        try:
            client = OllamaClient(url=url)
            models = client.get_available_models()
            
            if models:
                self.settings["available_models"] = models
                self.model_combo.clear()
                for model in models:
                    self.model_combo.addItem(model)
                QMessageBox.information(self, "成功", f"成功获取到 {len(models)} 个模型")
            else:
                QMessageBox.warning(self, "警告", "未能获取到模型列表，请检查 Ollama 是否正在运行")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取模型列表失败: {str(e)}")
    
    def test_network_api(self):
        api_url = self.network_api_url_edit.text().strip()
        api_key = self.network_api_key_edit.text().strip()
        api_model = self.network_api_model_combo.currentText().strip()
        
        if not api_url or not api_key or not api_model:
            QMessageBox.warning(self, "警告", "请填写完整的网络 API 设置")
            return
        
        try:
            client = NetworkClient(
                url=api_url,
                api_key=api_key,
                model=api_model
            )
            
            is_available = client.is_available()
            if is_available:
                QMessageBox.information(self, "成功", "网络 API 连接测试成功！")
            else:
                QMessageBox.warning(self, "警告", "网络 API 连接测试失败，请检查设置")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"测试失败: {str(e)}")

    def reset_defaults(self):
        reply = QMessageBox.question(
            self, "确认", "确定要重置为默认设置吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            defaults = get_default_settings()
            
            # API Type
            api_index = self.api_type_combo.findData(defaults["api_type"])
            if api_index >= 0:
                self.api_type_combo.setCurrentIndex(api_index)
            
            # Ollama Settings
            self.url_edit.setText(defaults["ollama_url"])
            self.model_combo.clear()
            for model in defaults["available_models"]:
                self.model_combo.addItem(model)
            self.model_combo.setCurrentText(defaults["ollama_model"])
            self.concurrent_spin.setValue(defaults["max_concurrent"])
            
            # Network API Settings
            self.network_api_url_edit.setText(defaults["network_api_url"])
            self.network_api_key_edit.setText(defaults["network_api_key"])
            self.network_api_model_combo.clear()
            for model in defaults["available_network_models"]:
                self.network_api_model_combo.addItem(model)
            self.network_api_model_combo.setCurrentText(defaults["network_api_model"])
            self.network_concurrent_spin.setValue(defaults["network_api_max_concurrent"])
            
            # Video Settings
            self.video_frame_spin.setValue(defaults["video_frame_count"])
            fm_index = self.video_frame_mode_combo.findData(defaults["video_frame_mode"])
            if fm_index >= 0:
                self.video_frame_mode_combo.setCurrentIndex(fm_index)
            
            # Operation Settings
            op_index = self.operation_combo.findData(defaults["operation_mode"])
            if op_index >= 0:
                self.operation_combo.setCurrentIndex(op_index)
            
            ts_index = self.time_source_combo.findData(defaults["time_source"])
            if ts_index >= 0:
                self.time_source_combo.setCurrentIndex(ts_index)
            
            fs_index = self.folder_structure_combo.findData(defaults["folder_structure"])
            if fs_index >= 0:
                self.folder_structure_combo.setCurrentIndex(fs_index)
            
            # Processing Settings
            self.process_images_check.setChecked(defaults["process_images"])
            self.process_videos_check.setChecked(defaults["process_videos"])
            
            # Categories and Prompt
            self.categories_edit.setPlainText("\n".join(defaults["categories"]))
            self.prompt_edit.setPlainText(defaults["prompt"])

    def get_settings(self):
        categories_text = self.categories_edit.toPlainText()
        categories = [line.strip() for line in categories_text.split("\n") if line.strip()]
        
        if not categories:
            categories = CATEGORIES.copy()

        return {
            "api_type": self.api_type_combo.currentData(),
            "ollama_url": self.url_edit.text().strip(),
            "ollama_model": self.model_combo.currentText().strip(),
            "available_models": self.settings.get("available_models", DEFAULT_MODELS),
            "network_api_url": self.network_api_url_edit.text().strip(),
            "network_api_key": self.network_api_key_edit.text().strip(),
            "network_api_model": self.network_api_model_combo.currentText().strip(),
            "available_network_models": self.settings.get("available_network_models", DEFAULT_NETWORK_API_MODELS),
            "network_api_max_concurrent": self.network_concurrent_spin.value(),
            "categories": categories,
            "prompt": self.prompt_edit.toPlainText(),
            "max_concurrent": self.concurrent_spin.value(),
            "video_frame_count": self.video_frame_spin.value(),
            "video_frame_mode": self.video_frame_mode_combo.currentData(),
            "operation_mode": self.operation_combo.currentData(),
            "time_source": self.time_source_combo.currentData(),
            "folder_structure": self.folder_structure_combo.currentData(),
            "process_images": self.process_images_check.isChecked(),
            "process_videos": self.process_videos_check.isChecked()
        }

    def accept(self):
        new_settings = self.get_settings()
        self.settings = new_settings
        save_settings(new_settings)
        super().accept()
