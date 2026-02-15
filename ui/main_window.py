import os
import time
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QProgressBar,
    QTextEdit, QFileDialog, QGroupBox, QSplitter,
    QMessageBox, QCheckBox, QComboBox, QDialog
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image
from typing import Optional
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui.worker import MediaProcessorWorker
from ui.settings_dialog import SettingsDialog
from core.ollama_client import OllamaClient
from core.database import Database
from config import load_settings, save_settings


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker: Optional[MediaProcessorWorker] = None
        self.settings = load_settings()
        self.init_ui()
        self.check_ollama_status()
        
        # 计时器相关变量
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer_display)
        self._start_time = None
        self._paused_time = 0
        self._paused_start = None
        self._is_paused = False

    def init_ui(self):
        self.setWindowTitle("AI 图片/视频整理工具 (网络版)")
        self.setMinimumSize(1000, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        path_group = QGroupBox("路径设置")
        path_layout = QVBoxLayout()

        source_layout = QHBoxLayout()
        self.source_path_edit = QLineEdit()
        self.source_path_edit.setPlaceholderText("选择要整理的文件夹...")
        source_browse_btn = QPushButton("浏览...")
        source_browse_btn.clicked.connect(self.browse_source_dir)
        source_layout.addWidget(QLabel("源目录:"))
        source_layout.addWidget(self.source_path_edit)
        source_layout.addWidget(source_browse_btn)

        target_layout = QHBoxLayout()
        self.target_path_edit = QLineEdit()
        self.target_path_edit.setPlaceholderText("选择目标文件夹...")
        target_browse_btn = QPushButton("浏览...")
        target_browse_btn.clicked.connect(self.browse_target_dir)
        target_layout.addWidget(QLabel("目标目录:"))
        target_layout.addWidget(self.target_path_edit)
        target_layout.addWidget(target_browse_btn)

        self.recursive_checkbox = QCheckBox("递归遍历子文件夹")
        self.recursive_checkbox.setChecked(True)

        path_layout.addLayout(source_layout)
        path_layout.addLayout(target_layout)
        path_layout.addWidget(self.recursive_checkbox)
        path_group.setLayout(path_layout)

        control_group = QGroupBox("控制")
        control_layout = QHBoxLayout()

        self.start_btn = QPushButton("开始")
        self.start_btn.clicked.connect(self.start_processing)
        self.pause_btn = QPushButton("暂停")
        self.pause_btn.clicked.connect(self.pause_processing)
        self.pause_btn.setEnabled(False)
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_processing)
        self.stop_btn.setEnabled(False)
        self.clear_history_btn = QPushButton("清除历史")
        self.clear_history_btn.clicked.connect(self.clear_history)
        self.settings_btn = QPushButton("设置")
        self.settings_btn.clicked.connect(self.open_settings)

        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.pause_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.clear_history_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.settings_btn)
        control_group.setLayout(control_layout)

        progress_group = QGroupBox("进度")
        progress_layout = QVBoxLayout()
        
        progress_info_layout = QHBoxLayout()
        self.progress_label = QLabel("就绪")
        self.time_label = QLabel("耗时: 00:00")
        self.time_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        progress_info_layout.addWidget(self.progress_label)
        progress_info_layout.addStretch()
        progress_info_layout.addWidget(self.time_label)
        
        self.progress_bar = QProgressBar()
        progress_layout.addLayout(progress_info_layout)
        progress_layout.addWidget(self.progress_bar)
        progress_group.setLayout(progress_layout)

        splitter = QSplitter(Qt.Horizontal)

        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout()
        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(300, 300)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("border: 1px solid #ccc; background-color: #f5f5f5;")
        self.preview_label.setText("暂无预览")
        preview_layout.addWidget(self.preview_label)
        preview_group.setLayout(preview_layout)

        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)

        splitter.addWidget(preview_group)
        splitter.addWidget(log_group)
        splitter.setSizes([400, 600])

        main_layout.addWidget(path_group)
        main_layout.addWidget(control_group)
        main_layout.addWidget(progress_group)
        main_layout.addWidget(splitter, 1)

    def browse_source_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择源目录")
        if dir_path:
            self.source_path_edit.setText(dir_path)
            if not self.target_path_edit.text():
                self.target_path_edit.setText(dir_path)

    def browse_target_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择目标目录")
        if dir_path:
            self.target_path_edit.setText(dir_path)

    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.settings = dialog.get_settings()
            self.append_log("设置已更新")

    def check_ollama_status(self):
        try:
            client = OllamaClient(
                url=self.settings.get("ollama_url"),
                model=self.settings.get("ollama_model")
            )
            if client.is_available():
                self.append_log("✓ Ollama 服务连接正常")
            else:
                self.append_log("✗ 无法连接到 Ollama 服务，请确保 Ollama 正在运行")
        except Exception as e:
            self.append_log(f"✗ 检查 Ollama 状态时出错: {str(e)}")

    def append_log(self, message: str):
        self.log_text.append(message)

    def update_preview(self, pil_image: Image.Image):
        if pil_image:
            img = pil_image.convert("RGB")
            w, h = img.size
            if max(w, h) > 400:
                if w > h:
                    new_w = 400
                    new_h = int(h * (400 / w))
                else:
                    new_h = 400
                    new_w = int(w * (400 / h))
                try:
                    resample_method = Image.Resampling.LANCZOS
                except AttributeError:
                    resample_method = Image.LANCZOS
                img = img.resize((new_w, new_h), resample_method)
            
            qimage = QImage(
                img.tobytes(),
                img.width,
                img.height,
                img.width * 3,
                QImage.Format_RGB888
            )
            pixmap = QPixmap.fromImage(qimage)
            self.preview_label.setPixmap(pixmap)
        else:
            self.preview_label.setText("预览失败")

    def update_timer_display(self):
        if self._start_time and not self._is_paused:
            elapsed = time.time() - self._start_time - self._paused_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            if hours > 0:
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                time_str = f"{minutes:02d}:{seconds:02d}"
            self.time_label.setText(f"耗时: {time_str}")

    def update_time(self, time_str: str):
        self.time_label.setText(f"耗时: {time_str}")

    def update_progress(self, current: int, total: int):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"{current}/{total}")

    def on_file_processed(self, result: dict):
        pass

    def on_finished(self):
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("暂停")
        self.stop_btn.setEnabled(False)
        self.worker = None
        # 停止计时器
        self.timer.stop()
        self._start_time = None
        self._is_paused = False
        # 重置预览
        self.preview_label.setText("暂无预览")
        self.append_log("处理已结束")

    def on_error(self, error_msg: str):
        QMessageBox.critical(self, "错误", f"发生错误: {error_msg}")

    def start_processing(self):
        source_dir = self.source_path_edit.text().strip()
        target_dir = self.target_path_edit.text().strip()

        if not source_dir or not os.path.isdir(source_dir):
            QMessageBox.warning(self, "警告", "请选择有效的源目录")
            return

        if not target_dir:
            target_dir = source_dir

        recursive = self.recursive_checkbox.isChecked()
        
        # 重置并启动计时器
        self._start_time = time.time()
        self._paused_time = 0
        self._paused_start = None
        self._is_paused = False
        self.timer.start(500)
        self.time_label.setText("耗时: 00:00")

        self.worker = MediaProcessorWorker(
            source_dir, 
            target_dir, 
            recursive,
            self.settings
        )
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.file_processed.connect(self.on_file_processed)
        self.worker.log_message.connect(self.append_log)
        self.worker.preview_image.connect(self.update_preview)
        self.worker.finished.connect(self.on_finished)
        self.worker.error_occurred.connect(self.on_error)

        self.worker.start()

        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)

    def pause_processing(self):
        if self.worker:
            if self.pause_btn.text() == "暂停":
                self.worker.pause()
                self.pause_btn.setText("继续")
                # 暂停计时器
                self._is_paused = True
                self._paused_start = time.time()
            else:
                self.worker.resume()
                self.pause_btn.setText("暂停")
                # 恢复计时器
                if self._paused_start:
                    self._paused_time += time.time() - self._paused_start
                    self._paused_start = None
                self._is_paused = False

    def stop_processing(self):
        if self.worker:
            self.worker.stop()
        # 停止计时器
        self.timer.stop()
        self._start_time = None
        self._is_paused = False

    def clear_history(self):
        reply = QMessageBox.question(
            self, "确认", 
            "确定要清除所有已处理文件的历史记录吗？\n\n这将允许您重新处理之前处理过的文件。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 停止当前正在运行的Worker
                if self.worker:
                    self.worker.stop()
                    self.worker.wait()
                    self.worker = None
                
                # 停止计时器
                self.timer.stop()
                self._start_time = None
                self._is_paused = False
                
                # 清除数据库记录
                db = Database()
                db.clear_all()
                
                # 重置界面元素
                self.time_label.setText("耗时: 00:00")
                self.progress_label.setText("就绪")
                self.progress_bar.setValue(0)
                self.preview_label.setText("暂无预览")
                self.append_log("✓ 已清除所有历史记录")
                QMessageBox.information(self, "成功", "历史记录已清除！\n现在可以重新处理文件了。")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清除历史记录失败: {str(e)}")
