from __future__ import annotations

APP_STYLESHEET = """
QMainWindow, QWidget {
  background: #0F172A;
  color: #F9FAFB;
  font-family: Segoe UI, Arial, sans-serif;
  font-size: 13px;
}
QListWidget {
  background: #111827;
  border: 0;
  padding: 10px;
}
QListWidget::item {
  padding: 12px;
  border-radius: 6px;
  color: #D1D5DB;
}
QListWidget::item:selected {
  background: #2563EB;
  color: white;
}
QFrame#Card, QGroupBox {
  background: #1F2937;
  border: 1px solid #374151;
  border-radius: 8px;
}
QGroupBox {
  margin-top: 18px;
  padding: 14px;
}
QGroupBox::title {
  subcontrol-origin: margin;
  left: 12px;
  padding: 0 4px;
  color: #F9FAFB;
  font-weight: 600;
}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
  background: #111827;
  border: 1px solid #374151;
  border-radius: 6px;
  padding: 8px;
  color: #F9FAFB;
}
QPushButton {
  background: #2563EB;
  border: 0;
  border-radius: 6px;
  color: white;
  padding: 9px 14px;
  font-weight: 600;
}
QPushButton:hover {
  background: #1D4ED8;
}
QPushButton:disabled {
  background: #374151;
  color: #9CA3AF;
}
QLabel#Muted {
  color: #9CA3AF;
}
QLabel#Title {
  font-size: 24px;
  font-weight: 700;
}
QProgressBar {
  background: #111827;
  border: 1px solid #374151;
  border-radius: 5px;
  height: 12px;
}
QProgressBar::chunk {
  background: #16A34A;
  border-radius: 5px;
}
"""
