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
    CATEGORIES, DEFAULT_PROMPT, DEFAULT_VIDEO_PROMPT, DEFAULT_MAX_CONCURRENT,
    DEFAULT_VIDEO_FRAME_COUNT, DEFAULT_OPERATION_MODE,
    DEFAULT_TIME_SOURCE, DEFAULT_FOLDER_STRUCTURE,
    DEFAULT_VIDEO_FRAME_MODE,
    DEFAULT_API_TYPE, DEFAULT_NETWORK_API_URL, DEFAULT_NETWORK_API_KEY,
    DEFAULT_NETWORK_API_MODEL, DEFAULT_NETWORK_API_MAX_CONCURRENT,
    DEFAULT_NETWORK_API_MODELS,
    DEFAULT_RENAME_ENABLED, DEFAULT_RENAME_PROMPT, DEFAULT_VIDEO_RENAME_PROMPT,
    DEFAULT_RENAME_INCLUDE_ORIGINAL_NAME, DEFAULT_RENAME_DATE_TYPE,
    DEFAULT_RENAME_DATE_FORMAT,
    DEFAULT_RETRY_ENABLED, DEFAULT_RETRY_COUNT, DEFAULT_RETRY_DELAY,
    DEFAULT_REQUEST_TIMEOUT, DEFAULT_ERROR_EXPORT_ENABLED, DEFAULT_ERROR_EXPORT_FOLDER
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

        #1. API设置页
        api_tab = self.create_api_tab()
        
        # 2. 图片AI设置页
        image_ai_tab = self.create_image_ai_tab()
        
        # 3. 视频AI设置页
        video_ai_tab = self.create_video_ai_tab()
        
        # 4. 操作和高级设置页
        operation_advanced_tab = self.create_operation_advanced_tab()
        
        tab_widget.addTab(api_tab, "API设置")
        tab_widget.addTab(image_ai_tab, "图片AI设置")
        tab_widget.addTab(video_ai_tab, "视频AI设置")
        tab_widget.addTab(operation_advanced_tab, "操作和高级设置")

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
        self.update_ai_previews()

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
        
        # Network API models are populated through the text area now

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
        
        # 从模型列表中获取第一个模型作为测试模型
        models_text = self.network_api_models_text.toPlainText()
        models = [line.strip() for line in models_text.split("\n") if line.strip()]
        api_model = models[0] if models else ""
        
        if not api_url or not api_key or not api_model:
            QMessageBox.warning(self, "警告", "请填写完整的网络 API 设置")
            return
        
        try:
            client = NetworkClient(
                url=api_url,
                api_key=api_key,
                model=api_model,
                models=models
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
            self.network_api_models_text.setPlainText("\n".join(defaults["available_network_models"]))
            self.network_api_round_robin_check.setChecked(defaults.get("network_api_round_robin", True))
            self.network_concurrent_spin.setValue(defaults["network_api_max_concurrent"])
            self.network_model_max_concurrent_spin.setValue(defaults.get("network_api_model_max_concurrent", 2))
            
            # Network Retry Settings
            self.retry_enabled_check.setChecked(defaults["retry_enabled"])
            self.retry_count_spin.setValue(defaults["retry_count"])
            self.retry_delay_spin.setValue(defaults["retry_delay"])
            self.request_timeout_spin.setValue(defaults["request_timeout"])
            self.error_export_check.setChecked(defaults["error_export_enabled"])
            self.error_export_folder_edit.setText(defaults["error_export_folder"])
            
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
            
            # AI Enable Settings
            self.image_ai_enabled_check.setChecked(defaults.get("image_ai_enabled", True))
            self.video_ai_enabled_check.setChecked(defaults.get("video_ai_enabled", True))
            
            # Image AI Settings
            image_categories = defaults.get("image_categories", defaults.get("categories", CATEGORIES))
            self.image_categories_edit.setPlainText("\n".join(image_categories))
            self.image_prompt_edit.setPlainText(defaults.get("image_prompt", defaults.get("prompt", DEFAULT_PROMPT)))
            
            # Image Rename Settings
            self.image_rename_enabled_check.setChecked(defaults.get("image_rename_enabled", defaults.get("rename_enabled", DEFAULT_RENAME_ENABLED)))
            self.image_rename_prompt_edit.setPlainText(defaults.get("image_rename_prompt", defaults.get("rename_prompt", DEFAULT_RENAME_PROMPT)))
            self.image_rename_include_original_check.setChecked(defaults.get("image_rename_include_original_name", defaults.get("rename_include_original_name", DEFAULT_RENAME_INCLUDE_ORIGINAL_NAME)))
            date_index = self.image_rename_date_combo.findData(defaults.get("image_rename_date_type", defaults.get("rename_date_type", DEFAULT_RENAME_DATE_TYPE)))
            if date_index >= 0:
                self.image_rename_date_combo.setCurrentIndex(date_index)
            self.image_rename_date_format_edit.setText(defaults.get("image_rename_date_format", defaults.get("rename_date_format", DEFAULT_RENAME_DATE_FORMAT)))

            # Video AI Settings
            video_categories = defaults.get("video_categories", defaults.get("categories", CATEGORIES))
            self.video_categories_edit.setPlainText("\n".join(video_categories))
            self.video_prompt_edit.setPlainText(defaults.get("video_prompt", DEFAULT_VIDEO_PROMPT))
            
            # Video Rename Settings
            self.video_rename_enabled_check.setChecked(defaults.get("video_rename_enabled", defaults.get("rename_enabled", DEFAULT_RENAME_ENABLED)))
            self.video_rename_prompt_edit.setPlainText(defaults.get("video_rename_prompt", DEFAULT_VIDEO_RENAME_PROMPT))
            self.video_rename_include_original_check.setChecked(defaults.get("video_rename_include_original_name", defaults.get("rename_include_original_name", DEFAULT_RENAME_INCLUDE_ORIGINAL_NAME)))
            date_index = self.video_rename_date_combo.findData(defaults.get("video_rename_date_type", defaults.get("rename_date_type", DEFAULT_RENAME_DATE_TYPE)))
            if date_index >= 0:
                self.video_rename_date_combo.setCurrentIndex(date_index)
            self.video_rename_date_format_edit.setText(defaults.get("video_rename_date_format", defaults.get("rename_date_format", DEFAULT_RENAME_DATE_FORMAT)))

    def get_settings(self):
        # 图片AI设置
        image_categories_text = self.image_categories_edit.toPlainText()
        image_categories = [line.strip() for line in image_categories_text.split("\n") if line.strip()]
        if not image_categories:
            image_categories = CATEGORIES.copy()

        # 视频AI设置
        video_categories_text = self.video_categories_edit.toPlainText()
        video_categories = [line.strip() for line in video_categories_text.split("\n") if line.strip()]
        if not video_categories:
            video_categories = CATEGORIES.copy()

        # 改进模型列表解析，支持换行、空格、逗号等多种分隔符
        models_text = self.network_api_models_text.toPlainText()
        # 替换所有可能的分隔符为换行符
        models_text = models_text.replace(',', '\n').replace(';', '\n').replace('\t', '\n')
        # 按换行符分割并清理
        models = [line.strip() for line in models_text.split("\n") if line.strip()]
        
        return {
            "api_type": self.api_type_combo.currentData(),
            "ollama_url": self.url_edit.text().strip(),
            "ollama_model": self.model_combo.currentText().strip(),
            "available_models": self.settings.get("available_models", DEFAULT_MODELS),
            "network_api_url": self.network_api_url_edit.text().strip(),
            "network_api_key": self.network_api_key_edit.text().strip(),
            "network_api_model": models[0] if models else "",
            "available_network_models": models,
            "network_api_round_robin": self.network_api_round_robin_check.isChecked(),
            "network_api_max_concurrent": self.network_concurrent_spin.value(),
            "network_api_model_max_concurrent": self.network_model_max_concurrent_spin.value(),
            # 图片AI设置
            "image_categories": image_categories,
            "image_prompt": self.image_prompt_edit.toPlainText(),
            "image_rename_enabled": self.image_rename_enabled_check.isChecked(),
            "image_rename_prompt": self.image_rename_prompt_edit.toPlainText(),
            "image_rename_include_original_name": self.image_rename_include_original_check.isChecked(),
            "image_rename_date_type": self.image_rename_date_combo.currentData(),
            "image_rename_date_format": self.image_rename_date_format_edit.text().strip(),
            "image_structured_output_prompt": self.image_structured_output_edit.toPlainText().strip(),
            # 视频AI设置
            "video_categories": video_categories,
            "video_prompt": self.video_prompt_edit.toPlainText(),
            "video_rename_enabled": self.video_rename_enabled_check.isChecked(),
            "video_rename_prompt": self.video_rename_prompt_edit.toPlainText(),
            "video_rename_include_original_name": self.video_rename_include_original_check.isChecked(),
            "video_rename_date_type": self.video_rename_date_combo.currentData(),
            "video_rename_date_format": self.video_rename_date_format_edit.text().strip(),
            "video_structured_output_prompt": self.video_structured_output_edit.toPlainText().strip(),
            # 兼容旧设置（使用图片AI的设置作为默认值）
            "categories": image_categories,
            "prompt": self.image_prompt_edit.toPlainText(),
            "rename_enabled": self.image_rename_enabled_check.isChecked(),
            "rename_prompt": self.image_rename_prompt_edit.toPlainText(),
            "rename_include_original_name": self.image_rename_include_original_check.isChecked(),
            "rename_date_type": self.image_rename_date_combo.currentData(),
            "rename_date_format": self.image_rename_date_format_edit.text().strip(),
            # 其他设置
            "max_concurrent": self.concurrent_spin.value(),
            "video_frame_count": self.video_frame_spin.value(),
            "video_frame_mode": self.video_frame_mode_combo.currentData(),
            "operation_mode": self.operation_combo.currentData(),
            "time_source": self.time_source_combo.currentData(),
            "folder_structure": self.folder_structure_combo.currentData(),
            "process_images": self.process_images_check.isChecked(),
            "process_videos": self.process_videos_check.isChecked(),
            # AI enable settings
            "image_ai_enabled": self.image_ai_enabled_check.isChecked(),
            "video_ai_enabled": self.video_ai_enabled_check.isChecked(),
            # Network retry settings
            "retry_enabled": self.retry_enabled_check.isChecked(),
            "retry_count": self.retry_count_spin.value(),
            "retry_delay": self.retry_delay_spin.value(),
            "request_timeout": self.request_timeout_spin.value(),
            "error_export_enabled": self.error_export_check.isChecked(),
            "error_export_folder": self.error_export_folder_edit.text().strip()
        }

    def accept(self):
        new_settings = self.get_settings()
        self.settings = new_settings
        save_settings(new_settings)
        super().accept()

    def create_api_tab(self):
        """创建API设置页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # API Type Selection
        api_group = QGroupBox("API 类型")
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
        self.network_api_key_edit.setEchoMode(QLineEdit.Normal)
        
        self.test_api_btn = QPushButton("测试连接")
        self.test_api_btn.clicked.connect(self.test_network_api)
        
        test_layout = QHBoxLayout()
        test_layout.addWidget(self.test_api_btn)
        
        self.network_concurrent_spin = QSpinBox()
        self.network_concurrent_spin.setMinimum(1)
        self.network_concurrent_spin.setMaximum(20)
        self.network_concurrent_spin.setValue(self.settings.get("network_api_max_concurrent", DEFAULT_NETWORK_API_MAX_CONCURRENT))
        
        self.network_model_max_concurrent_spin = QSpinBox()
        self.network_model_max_concurrent_spin.setMinimum(1)
        self.network_model_max_concurrent_spin.setMaximum(5)
        self.network_model_max_concurrent_spin.setValue(self.settings.get("network_api_model_max_concurrent", 2))
        
        self.network_api_models_text = QTextEdit()
        available_network_models = self.settings.get("available_network_models", DEFAULT_NETWORK_API_MODELS)
        self.network_api_models_text.setPlainText("\n".join(available_network_models))
        self.network_api_models_text.setPlaceholderText("Qwen/Qwen3-VL-8B-Instruct\nPro/zai-org/GLM-4.7\ndeepseek-ai/DeepSeek-V3.2\ngemini-3-pro-low")
        
        self.network_api_round_robin_check = QCheckBox("启用模型轮询")
        self.network_api_round_robin_check.setChecked(self.settings.get("network_api_round_robin", True))
        
        network_layout.addRow("API URL:", self.network_api_url_edit)
        network_layout.addRow("API Key:", self.network_api_key_edit)
        network_layout.addRow("模型列表（一行一个）:", self.network_api_models_text)
        network_layout.addRow(self.network_api_round_robin_check)
        network_layout.addRow("全局最大并发数:", self.network_concurrent_spin)
        network_layout.addRow("每个模型最大并发数:", self.network_model_max_concurrent_spin)
        network_layout.addRow(test_layout)
        
        network_group.setLayout(network_layout)

        layout.addWidget(api_group)
        layout.addWidget(ollama_group)
        layout.addWidget(network_group)
        layout.addStretch()
        
        return tab

    def create_image_ai_tab(self):
        """创建图片AI设置页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 图片AI功能启用设置
        image_ai_enable_group = QGroupBox("图片AI功能")
        image_ai_enable_layout = QVBoxLayout()
        self.image_ai_enabled_check = QCheckBox("启用图片AI功能")
        self.image_ai_enabled_check.setChecked(self.settings.get("image_ai_enabled", True))
        image_ai_enable_layout.addWidget(self.image_ai_enabled_check)
        image_ai_enable_group.setLayout(image_ai_enable_layout)
        layout.addWidget(image_ai_enable_group)

        # 图片处理设置
        image_process_group = QGroupBox("图片处理设置")
        image_process_layout = QVBoxLayout()
        self.process_images_check = QCheckBox("处理图片")
        self.process_images_check.setChecked(self.settings.get("process_images", True))
        image_process_layout.addWidget(self.process_images_check)
        image_process_group.setLayout(image_process_layout)
        layout.addWidget(image_process_group)

        # 分类类别
        categories_group = QGroupBox("分类类别")
        cat_layout = QVBoxLayout()
        self.image_categories_edit = QTextEdit()
        categories_text = "\n".join(self.settings.get("categories", CATEGORIES))
        self.image_categories_edit.setPlainText(categories_text)
        self.image_categories_edit.setPlaceholderText("每行一个类别")
        self.image_categories_edit.textChanged.connect(self.update_image_ai_preview)
        cat_layout.addWidget(self.image_categories_edit)
        categories_group.setLayout(cat_layout)
        layout.addWidget(categories_group)

        # 重命名开关
        rename_group = QGroupBox("重命名功能")
        rename_layout = QVBoxLayout()
        self.image_rename_enabled_check = QCheckBox("启用文件重命名功能")
        self.image_rename_enabled_check.setChecked(self.settings.get("rename_enabled", DEFAULT_RENAME_ENABLED))
        self.image_rename_enabled_check.stateChanged.connect(self.update_image_ai_preview)
        rename_layout.addWidget(self.image_rename_enabled_check)
        rename_group.setLayout(rename_layout)
        layout.addWidget(rename_group)

        # 分类提示词
        classification_prompt_group = QGroupBox("分类提示词")
        classification_prompt_layout = QVBoxLayout()
        self.image_prompt_edit = QTextEdit()
        self.image_prompt_edit.setPlainText(self.settings.get("prompt", DEFAULT_PROMPT))
        self.image_prompt_edit.setPlaceholderText("使用 {categories} 表示分类列表的占位符")
        self.image_prompt_edit.textChanged.connect(self.update_image_ai_preview)
        classification_prompt_layout.addWidget(self.image_prompt_edit)
        classification_prompt_group.setLayout(classification_prompt_layout)
        layout.addWidget(classification_prompt_group)

        # 重命名提示词
        rename_prompt_group = QGroupBox("重命名提示词")
        rename_prompt_layout = QVBoxLayout()
        self.image_rename_prompt_edit = QTextEdit()
        self.image_rename_prompt_edit.setPlainText(self.settings.get("rename_prompt", DEFAULT_RENAME_PROMPT))
        self.image_rename_prompt_edit.setPlaceholderText("为文件生成简短描述的提示词")
        self.image_rename_prompt_edit.textChanged.connect(self.update_image_ai_preview)
        rename_prompt_layout.addWidget(self.image_rename_prompt_edit)
        rename_prompt_group.setLayout(rename_prompt_layout)
        layout.addWidget(rename_prompt_group)

        # 文件名选项
        filename_options_group = QGroupBox("文件名选项")
        filename_options_layout = QFormLayout()

        self.image_rename_include_original_check = QCheckBox("包含原始文件名")
        self.image_rename_include_original_check.setChecked(self.settings.get("rename_include_original_name", DEFAULT_RENAME_INCLUDE_ORIGINAL_NAME))
        self.image_rename_include_original_check.stateChanged.connect(self.update_image_ai_preview)
        filename_options_layout.addRow(self.image_rename_include_original_check)

        self.image_rename_date_combo = QComboBox()
        self.image_rename_date_combo.addItem("不包含日期", "none")
        self.image_rename_date_combo.addItem("创建日期", "create")
        self.image_rename_date_combo.addItem("修改日期", "modify")
        self.image_rename_date_combo.addItem("访问日期", "access")
        date_type = self.settings.get("rename_date_type", DEFAULT_RENAME_DATE_TYPE)
        date_index = self.image_rename_date_combo.findData(date_type)
        if date_index >= 0:
            self.image_rename_date_combo.setCurrentIndex(date_index)
        self.image_rename_date_combo.currentIndexChanged.connect(self.update_image_ai_preview)
        filename_options_layout.addRow("日期类型:", self.image_rename_date_combo)

        self.image_rename_date_format_edit = QLineEdit(self.settings.get("rename_date_format", DEFAULT_RENAME_DATE_FORMAT))
        self.image_rename_date_format_edit.setPlaceholderText("例如: %Y%m%d")
        self.image_rename_date_format_edit.textChanged.connect(self.update_image_ai_preview)
        filename_options_layout.addRow("日期格式:", self.image_rename_date_format_edit)

        filename_options_group.setLayout(filename_options_layout)
        layout.addWidget(filename_options_group)
        
        # 图片AI预览
        preview_group = QGroupBox("完整提示词预览")
        preview_layout = QVBoxLayout()
        self.image_ai_preview_text = QTextEdit()
        self.image_ai_preview_text.setReadOnly(True)
        self.image_ai_preview_text.setPlaceholderText("显示最终发送给AI的完整提示词...")
        preview_layout.addWidget(self.image_ai_preview_text)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        layout.addStretch()
        
        return tab


    def update_ai_previews(self):
        """更新所有AI提示词预览"""
        self.update_image_ai_preview()
        self.update_video_ai_preview()

    def update_image_ai_preview(self):
        """更新图片AI提示词预览"""
        try:
            categories = [line.strip() for line in self.image_categories_edit.toPlainText().split("\n") if line.strip()]
            if not categories:
                categories = CATEGORIES.copy()
            categories_str = "、".join(categories)
            
            text1 = self.image_prompt_edit.toPlainText().replace("{categories}", categories_str)
            text3 = self.image_rename_prompt_edit.toPlainText()
            custom_structured_output = self.image_structured_output_edit.toPlainText().strip()
            
            parts = [text1]
            if self.image_rename_enabled_check.isChecked():
                parts.append(text3)
            if custom_structured_output:
                parts.append(custom_structured_output)
            else:
                if self.image_rename_enabled_check.isChecked():
                    structured_output = """- 只返回JSON格式，格式如下：{"category": "类别名称", "description": "简短描述"}
- 类别必须且只能从指定列表中选择。
- 描述要简洁明了，突出图片核心内容。
- 不要包含任何其他文字或标点符号。
- 不要使用markdown代码块格式（不要使用```标记）。
- 直接返回纯JSON文本，不要任何格式化。"""
                else:
                    structured_output = """- 只返回JSON格式，格式如下：{"category": "类别名称"}
- 类别必须且只能从指定列表中选择。
- 不要包含任何其他文字或标点符号。
- 不要使用markdown代码块格式（不要使用```标记）。
- 直接返回纯JSON文本，不要任何格式化。"""
                parts.append(structured_output)
            
            full_prompt = "\n\n".join(parts)
            self.image_ai_preview_text.setPlainText(full_prompt)
        except Exception:
            pass

    def update_video_ai_preview(self):
        """更新视频AI提示词预览"""
        try:
            categories = [line.strip() for line in self.video_categories_edit.toPlainText().split("\n") if line.strip()]
            if not categories:
                categories = CATEGORIES.copy()
            categories_str = "、".join(categories)
            
            text1 = self.video_prompt_edit.toPlainText().replace("{categories}", categories_str)
            text3 = self.video_rename_prompt_edit.toPlainText()
            custom_structured_output = self.video_structured_output_edit.toPlainText().strip()
            
            parts = [text1]
            if self.video_rename_enabled_check.isChecked():
                parts.append(text3)
            if custom_structured_output:
                parts.append(custom_structured_output)
            else:
                if self.video_rename_enabled_check.isChecked():
                    structured_output = """- 只返回JSON格式，格式如下：{"category": "类别名称", "description": "简短描述"}
- 类别必须且只能从指定列表中选择。
- 描述要简洁明了，突出视频核心主题。
- 不要包含任何其他文字或标点符号。
- 不要使用markdown代码块格式（不要使用```标记）。
- 直接返回纯JSON文本，不要任何格式化。"""
                else:
                    structured_output = """- 只返回JSON格式，格式如下：{"category": "类别名称"}
- 类别必须且只能从指定列表中选择。
- 不要包含任何其他文字或标点符号。
- 不要使用markdown代码块格式（不要使用```标记）。
- 直接返回纯JSON文本，不要任何格式化。"""
                parts.append(structured_output)
            
            full_prompt = "\n\n".join(parts)
            self.video_ai_preview_text.setPlainText(full_prompt)
        except Exception:
            pass

    def create_video_ai_tab(self):
        """创建视频AI设置页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 视频AI功能启用设置
        video_ai_enable_group = QGroupBox("视频AI功能")
        video_ai_enable_layout = QVBoxLayout()
        self.video_ai_enabled_check = QCheckBox("启用视频AI功能")
        self.video_ai_enabled_check.setChecked(self.settings.get("video_ai_enabled", True))
        video_ai_enable_layout.addWidget(self.video_ai_enabled_check)
        video_ai_enable_group.setLayout(video_ai_enable_layout)
        layout.addWidget(video_ai_enable_group)

        # 视频处理设置
        video_process_group = QGroupBox("视频处理设置")
        video_process_layout = QVBoxLayout()
        self.process_videos_check = QCheckBox("处理视频")
        self.process_videos_check.setChecked(self.settings.get("process_videos", True))
        video_process_layout.addWidget(self.process_videos_check)
        
        video_frame_layout = QFormLayout()
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
        
        video_frame_layout.addRow("抽帧数量:", self.video_frame_spin)
        video_frame_layout.addRow("抽帧模式:", self.video_frame_mode_combo)
        video_process_layout.addLayout(video_frame_layout)
        video_process_group.setLayout(video_process_layout)
        layout.addWidget(video_process_group)

        # 分类类别
        categories_group = QGroupBox("分类类别")
        cat_layout = QVBoxLayout()
        self.video_categories_edit = QTextEdit()
        categories_text = "\n".join(self.settings.get("categories", CATEGORIES))
        self.video_categories_edit.setPlainText(categories_text)
        self.video_categories_edit.setPlaceholderText("每行一个类别")
        self.video_categories_edit.textChanged.connect(self.update_video_ai_preview)
        cat_layout.addWidget(self.video_categories_edit)
        categories_group.setLayout(cat_layout)
        layout.addWidget(categories_group)

        # 重命名开关
        rename_group = QGroupBox("重命名功能")
        rename_layout = QVBoxLayout()
        self.video_rename_enabled_check = QCheckBox("启用文件重命名功能")
        self.video_rename_enabled_check.setChecked(self.settings.get("rename_enabled", DEFAULT_RENAME_ENABLED))
        self.video_rename_enabled_check.stateChanged.connect(self.update_video_ai_preview)
        rename_layout.addWidget(self.video_rename_enabled_check)
        rename_group.setLayout(rename_layout)
        layout.addWidget(rename_group)

        # 分类提示词
        classification_prompt_group = QGroupBox("分类提示词")
        classification_prompt_layout = QVBoxLayout()
        self.video_prompt_edit = QTextEdit()
        self.video_prompt_edit.setPlainText(self.settings.get("video_prompt", DEFAULT_VIDEO_PROMPT))
        self.video_prompt_edit.setPlaceholderText("使用 {categories} 表示分类列表的占位符")
        self.video_prompt_edit.textChanged.connect(self.update_video_ai_preview)
        classification_prompt_layout.addWidget(self.video_prompt_edit)
        classification_prompt_group.setLayout(classification_prompt_layout)
        layout.addWidget(classification_prompt_group)

        # 重命名提示词
        rename_prompt_group = QGroupBox("重命名提示词")
        rename_prompt_layout = QVBoxLayout()
        self.video_rename_prompt_edit = QTextEdit()
        self.video_rename_prompt_edit.setPlainText(self.settings.get("video_rename_prompt", DEFAULT_VIDEO_RENAME_PROMPT))
        self.video_rename_prompt_edit.setPlaceholderText("为文件生成简短描述的提示词")
        self.video_rename_prompt_edit.textChanged.connect(self.update_video_ai_preview)
        rename_prompt_layout.addWidget(self.video_rename_prompt_edit)
        rename_prompt_group.setLayout(rename_prompt_layout)
        layout.addWidget(rename_prompt_group)

        # 文件名选项
        filename_options_group = QGroupBox("文件名选项")
        filename_options_layout = QFormLayout()

        self.video_rename_include_original_check = QCheckBox("包含原始文件名")
        self.video_rename_include_original_check.setChecked(self.settings.get("rename_include_original_name", DEFAULT_RENAME_INCLUDE_ORIGINAL_NAME))
        self.video_rename_include_original_check.stateChanged.connect(self.update_video_ai_preview)
        filename_options_layout.addRow(self.video_rename_include_original_check)

        self.video_rename_date_combo = QComboBox()
        self.video_rename_date_combo.addItem("不包含日期", "none")
        self.video_rename_date_combo.addItem("创建日期", "create")
        self.video_rename_date_combo.addItem("修改日期", "modify")
        self.video_rename_date_combo.addItem("访问日期", "access")
        date_type = self.settings.get("rename_date_type", DEFAULT_RENAME_DATE_TYPE)
        date_index = self.video_rename_date_combo.findData(date_type)
        if date_index >= 0:
            self.video_rename_date_combo.setCurrentIndex(date_index)
        self.video_rename_date_combo.currentIndexChanged.connect(self.update_video_ai_preview)
        filename_options_layout.addRow("日期类型:", self.video_rename_date_combo)

        self.video_rename_date_format_edit = QLineEdit(self.settings.get("rename_date_format", DEFAULT_RENAME_DATE_FORMAT))
        self.video_rename_date_format_edit.setPlaceholderText("例如: %Y%m%d")
        self.video_rename_date_format_edit.textChanged.connect(self.update_video_ai_preview)
        filename_options_layout.addRow("日期格式:", self.video_rename_date_format_edit)

        filename_options_group.setLayout(filename_options_layout)
        layout.addWidget(filename_options_group)
        
        # 视频AI预览
        preview_group = QGroupBox("完整提示词预览")
        preview_layout = QVBoxLayout()
        self.video_ai_preview_text = QTextEdit()
        self.video_ai_preview_text.setReadOnly(True)
        self.video_ai_preview_text.setPlaceholderText("显示最终发送给AI的完整提示词...")
        preview_layout.addWidget(self.video_ai_preview_text)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        layout.addStretch()
        
        return tab


    def create_operation_advanced_tab(self):
        """创建操作和高级设置页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 操作设置
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
        layout.addWidget(operation_group)

        # 网络重试设置
        retry_group = QGroupBox("网络重试设置")
        retry_layout = QFormLayout()
        
        self.retry_enabled_check = QCheckBox("启用网络错误重试")
        self.retry_enabled_check.setChecked(self.settings.get("retry_enabled", DEFAULT_RETRY_ENABLED))
        retry_layout.addRow(self.retry_enabled_check)
        
        self.retry_count_spin = QSpinBox()
        self.retry_count_spin.setMinimum(1)
        self.retry_count_spin.setMaximum(10)
        self.retry_count_spin.setValue(self.settings.get("retry_count", DEFAULT_RETRY_COUNT))
        retry_layout.addRow("重试次数:", self.retry_count_spin)
        
        self.retry_delay_spin = QSpinBox()
        self.retry_delay_spin.setMinimum(1)
        self.retry_delay_spin.setMaximum(30)
        self.retry_delay_spin.setSuffix(" 秒")
        self.retry_delay_spin.setValue(self.settings.get("retry_delay", DEFAULT_RETRY_DELAY))
        retry_layout.addRow("重试延迟:", self.retry_delay_spin)
        
        self.request_timeout_spin = QSpinBox()
        self.request_timeout_spin.setMinimum(30)
        self.request_timeout_spin.setMaximum(600)
        self.request_timeout_spin.setSuffix(" 秒")
        self.request_timeout_spin.setValue(self.settings.get("request_timeout", DEFAULT_REQUEST_TIMEOUT))
        retry_layout.addRow("请求超时:", self.request_timeout_spin)
        
        # 结构化输出提示词
        structured_output_group = QGroupBox("结构化输出提示词")
        structured_output_layout = QVBoxLayout()
        
        # 图片结构化输出提示词
        image_structured_label = QLabel("图片结构化输出提示词:")
        structured_output_layout.addWidget(image_structured_label)
        self.image_structured_output_edit = QTextEdit()
        self.image_structured_output_edit.setPlainText(self.settings.get("image_structured_output_prompt", ""))
        self.image_structured_output_edit.setPlaceholderText("格式化输出的约束条件（不建议修改）")
        self.image_structured_output_edit.setMaximumHeight(100)
        self.image_structured_output_edit.textChanged.connect(self.update_image_ai_preview)
        structured_output_layout.addWidget(self.image_structured_output_edit)
        
        # 视频结构化输出提示词
        video_structured_label = QLabel("视频结构化输出提示词:")
        structured_output_layout.addWidget(video_structured_label)
        self.video_structured_output_edit = QTextEdit()
        self.video_structured_output_edit.setPlainText(self.settings.get("video_structured_output_prompt", ""))
        self.video_structured_output_edit.setPlaceholderText("格式化输出的约束条件（不建议修改）")
        self.video_structured_output_edit.setMaximumHeight(100)
        self.video_structured_output_edit.textChanged.connect(self.update_video_ai_preview)
        structured_output_layout.addWidget(self.video_structured_output_edit)
        
        structured_output_group.setLayout(structured_output_layout)
        layout.addWidget(structured_output_group)
        
        retry_group.setLayout(retry_layout)
        layout.addWidget(retry_group)
        
        # 错误文件导出
        error_group = QGroupBox("错误文件导出")
        error_layout = QFormLayout()
        
        self.error_export_check = QCheckBox("启用错误文件导出")
        self.error_export_check.setChecked(self.settings.get("error_export_enabled", DEFAULT_ERROR_EXPORT_ENABLED))
        error_layout.addRow(self.error_export_check)
        
        self.error_export_folder_edit = QLineEdit(self.settings.get("error_export_folder", DEFAULT_ERROR_EXPORT_FOLDER))
        error_layout.addRow("错误文件目录:", self.error_export_folder_edit)
        
        error_group.setLayout(error_layout)
        layout.addWidget(error_group)
        layout.addStretch()
        
        return tab
