import sys
import json
import time
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, 
    QMessageBox, QProgressBar, QFrame, QSizePolicy
)
from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QPixmap
from PyQt5.QtWidgets import QGraphicsDropShadowEffect

class CircularProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(False)
        self.setFixedSize(200, 200)
        self.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #F0F0F0;
                border-radius: 100px;
            }
            QProgressBar::chunk {
                background-color: #7E57C2;
                border-radius: 100px;
            }
        """)

class FocusApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FocusBuddy")
        self.setGeometry(100, 100, 400, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #F9F9F9;
                color: #333333;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #7E57C2;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 12px 20px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9575CD;
            }
            QPushButton:pressed {
                background-color: #673AB7;
            }
            QLabel {
                font-size: 16px;
            }
            QProgressBar {
                border: 1px solid #E0E0E0;
                border-radius: 10px;
                background-color: #F0F0F0;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #7E57C2;
                border-radius: 10px;
            }
        """)

        # Initialize data
        self.pomodoro_duration = 25 * 60  # 25 minutes
        self.break_duration = 5 * 60
        self.remaining_time = self.pomodoro_duration
        self.is_break = False
        self.timer_active = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        
        self.load_data()
        
        # Create the UI
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Header section
        header_layout = QHBoxLayout()
        self.app_title = QLabel("FocusBuddy")
        self.app_title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        header_layout.addWidget(self.app_title)
        header_layout.addStretch()
        
        # Timer section with circular design
        timer_frame = QFrame()
        timer_frame.setFrameShape(QFrame.StyledPanel)
        timer_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
                border: 1px solid #E0E0E0;
            }
        """)
        # For PyQt5, we need to use a drop shadow effect instead of CSS box-shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 4)
        timer_frame.setGraphicsEffect(shadow)
        timer_layout = QVBoxLayout(timer_frame)
        timer_layout.setAlignment(Qt.AlignCenter)
        
        # Timer type label (Pomodoro/Break)
        self.session_type_label = QLabel("Focus Session" if not self.is_break else "Break Time")
        self.session_type_label.setFont(QFont("Segoe UI", 16))
        self.session_type_label.setAlignment(Qt.AlignCenter)
        timer_layout.addWidget(self.session_type_label)
        
        # Time display
        self.time_label = QLabel(self.format_time(self.remaining_time))
        self.time_label.setFont(QFont("Segoe UI", 40, QFont.Bold))
        self.time_label.setAlignment(Qt.AlignCenter)
        timer_layout.addWidget(self.time_label)
        
        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.start_button = QPushButton("Start")
        self.start_button.setFixedHeight(50)
        self.start_button.clicked.connect(self.toggle_timer)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.setFixedHeight(50)
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
            }
            QPushButton:hover {
                background-color: #BDBDBD;
            }
            QPushButton:pressed {
                background-color: #757575;
            }
        """)
        self.reset_button.clicked.connect(self.reset_timer)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.reset_button)
        
        # Admin button (hidden by default)
        self.admin_button = QPushButton("Admin: Skip Timer")
        self.admin_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                font-size: 12px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #EF5350;
            }
        """)
        self.admin_button.clicked.connect(self.admin_skip_timer)
        self.admin_button.setFixedHeight(40)
        self.admin_button.setVisible(False)  # Hidden by default
        
        # Add admin button toggle
        self.admin_mode = False
        self.admin_toggle_count = 0
        self.app_title.mousePressEvent = self.toggle_admin_mode
        
        timer_layout.addLayout(button_layout)
        timer_layout.addWidget(self.admin_button)
        
        # Stats section
        stats_frame = QFrame()
        stats_frame.setFrameShape(QFrame.StyledPanel)
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
                border: 1px solid #E0E0E0;
            }
        """)
        # For PyQt5, we need to use a drop shadow effect instead of CSS box-shadow
        shadow2 = QGraphicsDropShadowEffect(self)
        shadow2.setBlurRadius(15)
        shadow2.setColor(QColor(0, 0, 0, 30))
        shadow2.setOffset(0, 4)
        stats_frame.setGraphicsEffect(shadow2)
        stats_layout = QVBoxLayout(stats_frame)
        
        stats_header = QLabel("Your Progress")
        stats_header.setFont(QFont("Segoe UI", 16, QFont.Bold))
        stats_layout.addWidget(stats_header)
        
        # Level and XP
        level_xp_layout = QHBoxLayout()
        
        level_layout = QVBoxLayout()
        level_title = QLabel("Level")
        level_title.setStyleSheet("color: #9E9E9E; font-size: 14px;")
        self.level_label = QLabel(str(self.data['level']))
        self.level_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.level_label.setStyleSheet("color: #7E57C2;")
        level_layout.addWidget(level_title)
        level_layout.addWidget(self.level_label)
        level_xp_layout.addLayout(level_layout)
        
        xp_layout = QVBoxLayout()
        xp_title = QLabel("XP")
        xp_title.setStyleSheet("color: #9E9E9E; font-size: 14px;")
        self.xp_label = QLabel(f"{self.data['xp'] % 100}/100")
        self.xp_label.setFont(QFont("Segoe UI", 16))
        xp_layout.addWidget(xp_title)
        xp_layout.addWidget(self.xp_label)
        level_xp_layout.addLayout(xp_layout)
        
        stats_layout.addLayout(level_xp_layout)
        
        # XP Progress bar
        self.xp_bar = QProgressBar()
        self.xp_bar.setFixedHeight(15)
        self.xp_bar.setValue(self.data['xp'] % 100)
        stats_layout.addWidget(self.xp_bar)
        
        # Streak information
        streak_layout = QHBoxLayout()
        streak_icon_label = QLabel("🔥")
        streak_icon_label.setFont(QFont("Segoe UI", 20))
        
        streak_info = QVBoxLayout()
        streak_title = QLabel("Current Streak")
        streak_title.setStyleSheet("color: #9E9E9E; font-size: 14px;")
        self.streak_label = QLabel(f"{self.data['streak']} days")
        self.streak_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        
        streak_info.addWidget(streak_title)
        streak_info.addWidget(self.streak_label)
        
        streak_layout.addWidget(streak_icon_label)
        streak_layout.addLayout(streak_info)
        streak_layout.addStretch()
        
        stats_layout.addLayout(streak_layout)
        
        # Add all sections to main layout
        main_layout.addLayout(header_layout)
        main_layout.addWidget(timer_frame)
        main_layout.addWidget(stats_frame)
        main_layout.addStretch()
        
        self.setLayout(main_layout)

    def format_time(self, seconds):
        m, s = divmod(seconds, 60)
        return f"{int(m):02}:{int(s):02}"

    def toggle_timer(self):
        if self.timer_active:
            self.timer.stop()
            self.timer_active = False
            self.start_button.setText("Resume")
        else:
            self.timer.start(1000)
            self.timer_active = True
            self.start_button.setText("Pause")

    def reset_timer(self):
        self.timer.stop()
        self.timer_active = False
        self.remaining_time = self.pomodoro_duration if not self.is_break else self.break_duration
        self.time_label.setText(self.format_time(self.remaining_time))
        self.start_button.setText("Start")

    def update_timer(self):
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.time_label.setText(self.format_time(self.remaining_time))
        else:
            self.timer.stop()
            self.timer_active = False
            if not self.is_break:
                self.complete_session()
                self.remaining_time = self.break_duration
                self.is_break = True
                self.session_type_label.setText("Break Time")
                QMessageBox.information(self, "Break Time", "Great job! Take a 5-minute break!")
            else:
                self.remaining_time = self.pomodoro_duration
                self.is_break = False
                self.session_type_label.setText("Focus Session")
                QMessageBox.information(self, "Back to Work", "Break's over. Ready for the next focus session?")
            self.time_label.setText(self.format_time(self.remaining_time))
            self.start_button.setText("Start")

    def complete_session(self):
        # Add XP and check for level up
        self.data['xp'] += 25
        if self.data['xp'] >= self.data['level'] * 100:
            self.data['level'] += 1
            QMessageBox.information(self, "Level Up!", f"Congratulations! You reached level {self.data['level']}!")

        # Update streak
        today = datetime.today().date()
        try:
            last_day = datetime.strptime(self.data['last_session'], "%Y-%m-%d").date()
            if today == last_day + timedelta(days=1):
                self.data['streak'] += 1
                if self.data['streak'] % 5 == 0:  # Milestone every 5 days
                    QMessageBox.information(self, "Streak Milestone!", 
                                           f"Amazing! You've maintained your focus for {self.data['streak']} days in a row!")
            elif today != last_day:
                self.data['streak'] = 1
        except ValueError:
            # Handle case where last_session is not a valid date
            self.data['streak'] = 1
            
        self.data['last_session'] = str(today)

        self.save_data()
        self.refresh_ui()

    def refresh_ui(self):
        self.streak_label.setText(f"{self.data['streak']} days")
        self.level_label.setText(str(self.data['level']))
        self.xp_label.setText(f"{self.data['xp'] % 100}/100")
        self.xp_bar.setValue(self.data['xp'] % 100)

    def load_data(self):
        try:
            with open("focus_data.json", "r") as f:
                self.data = json.load(f)
        except:
            self.data = {
                "xp": 0,
                "level": 1,
                "streak": 0,
                "last_session": str(datetime.today().date())
            }

    def admin_skip_timer(self):
        """Admin function to skip the timer for testing streak functionality"""
        self.remaining_time = 0
        self.update_timer()
        
    def toggle_admin_mode(self, event):
        """Secret way to toggle admin mode by clicking the app title 5 times"""
        self.admin_toggle_count += 1
        if self.admin_toggle_count >= 5:
            self.admin_mode = not self.admin_mode
            self.admin_button.setVisible(self.admin_mode)
            self.admin_toggle_count = 0
            
            if self.admin_mode:
                QMessageBox.information(self, "Admin Mode", "Admin mode activated")
            else:
                QMessageBox.information(self, "Admin Mode", "Admin mode deactivated")
            
    def save_data(self):
        with open("focus_data.json", "w") as f:
            json.dump(self.data, f)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FocusApp()
    window.show()
    sys.exit(app.exec_())