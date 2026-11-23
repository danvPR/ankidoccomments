from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QPushButton, QDialogButtonBox, QColorDialog, QLabel,
    QGroupBox, QColor, QIntValidator, QMessageBox
)
from aqt.utils import tooltip


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AnkiDocComments Settings")
        self.setMinimumWidth(400)
        addon_package = __package__.split(".")[0] if __package__ else "AnkiDocComments"
        self.config = mw.addonManager.getConfig(addon_package) or {}
        self.addon_package = addon_package
        self.color_buttons = {}
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Language
        self.language_combo = QComboBox()
        self.language_combo.addItem("Tiếng Việt", "vi")
        self.language_combo.addItem("English", "en")
        self.language_combo.setCurrentIndex(1)
        layout.addWidget(QLabel("Language / Ngôn ngữ:"))
        layout.addWidget(self.language_combo)

        # Trigger mode
        self.trigger_combo = QComboBox()
        self.trigger_combo.addItems(["hover", "click"])
        layout.addWidget(QLabel("Trigger Mode:"))
        layout.addWidget(self.trigger_combo)

        # Colors group
        colors_group = QGroupBox("Highlight Colors")
        colors_layout = QFormLayout(colors_group)

        color_fields = [
            ("highlight_light", "Highlight (Light)"),
            ("highlight_dark", "Highlight (Dark)"),
            ("resolved_light", "Resolved (Light)"),
            ("resolved_dark", "Resolved (Dark)"),
        ]

        for key, label in color_fields:
            btn = QPushButton()
            btn.setFixedSize(60, 24)
            btn.clicked.connect(lambda checked, k=key: self.pick_color(k))
            self.color_buttons[key] = btn
            colors_layout.addRow(label + ":", btn)

        layout.addWidget(colors_group)

        # Sidebar width
        self.sidebar_width_edit = QLineEdit()
        self.sidebar_width_edit.setPlaceholderText("320")
        self.sidebar_width_edit.setValidator(QIntValidator(100, 1200, self.sidebar_width_edit))
        layout.addWidget(QLabel("Sidebar Width (px):"))
        layout.addWidget(self.sidebar_width_edit)

        # Timestamp format
        self.timestamp_edit = QLineEdit()
        self.timestamp_edit.setPlaceholderText("YYYY-MM-DD HH:mm")
        layout.addWidget(QLabel("Timestamp Format:"))
        layout.addWidget(self.timestamp_edit)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.save_config)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_config(self):
        language = self.config.get("language", "en")
        index = self.language_combo.findData(language)
        self.language_combo.setCurrentIndex(index if index >= 0 else 1)
        self.trigger_combo.setCurrentText(self.config.get("trigger_mode", "hover"))

        colors = self.config.get("highlight_colors", {})
        self.color_buttons["highlight_light"].setStyleSheet(f"background-color: {colors.get('light', '#fff0b3')};")
        self.color_buttons["highlight_dark"].setStyleSheet(f"background-color: {colors.get('dark', '#4a421b')};")
        self.color_buttons["resolved_light"].setStyleSheet(f"background-color: {colors.get('resolved_light', '#e0e0e0')};")
        self.color_buttons["resolved_dark"].setStyleSheet(f"background-color: {colors.get('resolved_dark', '#3a3a3a')};")

        self.sidebar_width_edit.setText(str(self.config.get("sidebar_width", 320)))
        self.timestamp_edit.setText(self.config.get("timestamp_format", "YYYY-MM-DD HH:mm"))

    def pick_color(self, key):
        btn = self.color_buttons[key]
        current_color = btn.styleSheet().split("background-color: ")[-1].rstrip(";}")
        color = QColorDialog.getColor(QColor(current_color), self, f"Select {key} Color")
        if color.isValid():
            btn.setStyleSheet(f"background-color: {color.name()};")

    def save_config(self):
        colors = {
            "light": self.color_buttons["highlight_light"].styleSheet().split("background-color: ")[-1].rstrip(";}"),
            "dark": self.color_buttons["highlight_dark"].styleSheet().split("background-color: ")[-1].rstrip(";}"),
            "resolved_light": self.color_buttons["resolved_light"].styleSheet().split("background-color: ")[-1].rstrip(";}"),
            "resolved_dark": self.color_buttons["resolved_dark"].styleSheet().split("background-color: ")[-1].rstrip(";}"),
        }

        try:
            sidebar_width = int(self.sidebar_width_edit.text() or 320)
        except ValueError:
            QMessageBox.warning(self, "Invalid sidebar width", "Sidebar width must be a number from 100 to 1200.")
            return
        if not 100 <= sidebar_width <= 1200:
            QMessageBox.warning(self, "Invalid sidebar width", "Sidebar width must be a number from 100 to 1200.")
            return

        config = dict(self.config)
        config.update({
            "language": self.language_combo.currentData(),
            "trigger_mode": self.trigger_combo.currentText(),
            "highlight_colors": colors,
            "sidebar_width": sidebar_width,
            "timestamp_format": self.timestamp_edit.text() or "YYYY-MM-DD HH:mm",
        })

        mw.addonManager.writeConfig(self.addon_package, config)
        tooltip("Settings saved.")
        self.accept()