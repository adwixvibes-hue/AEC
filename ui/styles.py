"""
أنماط QSS الاحترافية للواجهة
Professional QSS Styles for UI

تصميم عصري داكن مع تأثير Glassmorphism
"""

class AppStyles:
    """
    مجمع الأنماط للتطبيق
    Style Container for the Application
    """
    
    # النمط الرئيسي - Main Style
    MAIN_STYLE = """
    /* النمط الرئيسي للتطبيق - Main Application Style */
    
    QMainWindow {
        background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
            stop: 0 #0a0e27, stop: 1 #1a1f3a);
    }
    
    /* ترويسة النافذة - Window Title Bar */
    QMenuBar {
        background: rgba(20, 25, 50, 0.95);
        color: #ffffff;
        border-bottom: 1px solid rgba(0, 255, 255, 0.3);
        padding: 5px;
        font-size: 13px;
        font-weight: bold;
    }
    
    QMenuBar::item {
        background: transparent;
        padding: 8px 15px;
        border-radius: 5px;
    }
    
    QMenuBar::item:selected {
        background: rgba(0, 255, 255, 0.2);
        border: 1px solid rgba(0, 255, 255, 0.5);
    }
    
    QMenu {
        background: rgba(20, 25, 50, 0.98);
        color: #ffffff;
        border: 1px solid rgba(0, 255, 255, 0.3);
        border-radius: 8px;
        padding: 5px;
    }
    
    QMenu::item {
        padding: 8px 25px;
        border-radius: 4px;
    }
    
    QMenu::item:selected {
        background: rgba(0, 255, 255, 0.2);
    }
    
    /* تبويبات - Tabs */
    QTabWidget::pane {
        background: rgba(20, 25, 50, 0.7);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 10px;
        margin: 5px;
    }
    
    QTabBar::tab {
        background: rgba(30, 35, 60, 0.8);
        color: #a0b0d0;
        padding: 12px 25px;
        margin-right: 3px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-size: 14px;
        font-weight: bold;
        border: 1px solid transparent;
    }
    
    QTabBar::tab:selected {
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 #2a3a6a, stop: 1 #1a2a4a);
        color: #00ffff;
        border: 1px solid rgba(0, 255, 255, 0.5);
        border-bottom: none;
    }
    
    QTabBar::tab:hover:!selected {
        background: rgba(0, 255, 255, 0.1);
        color: #d0d0ff;
    }
    
    /* أزرار - Buttons */
    QPushButton {
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 #2a4a6a, stop: 1 #1a3a5a);
        color: #ffffff;
        border: 1px solid rgba(0, 255, 255, 0.3);
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 13px;
        font-weight: bold;
        min-width: 100px;
    }
    
    QPushButton:hover {
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 #3a5a7a, stop: 1 #2a4a6a);
        border: 1px solid rgba(0, 255, 255, 0.6);
    }
    
    QPushButton:pressed {
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 #1a3a5a, stop: 1 #0a2a4a);
    }
    
    QPushButton:disabled {
        background: #2a2a3a;
        color: #6a6a7a;
        border: 1px solid #3a3a4a;
    }
    
    /* زر أساسي - Primary Button */
    QPushButton#primaryButton {
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 #00bfff, stop: 1 #0080ff);
        border: 1px solid rgba(0, 255, 255, 0.8);
        color: #ffffff;
    }
    
    QPushButton#primaryButton:hover {
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 #20cfff, stop: 1 #1090ff);
    }
    
    /* زر خطر - Danger Button */
    QPushButton#dangerButton {
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 #ff4444, stop: 1 #cc0000);
        border: 1px solid rgba(255, 100, 100, 0.8);
    }
    
    QPushButton#dangerButton:hover {
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 #ff5555, stop: 1 #dd1111);
    }
    
    /* جداول - Tables */
    QTableWidget {
        background: rgba(20, 25, 50, 0.8);
        color: #e0e0ff;
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 10px;
        gridline-color: rgba(0, 255, 255, 0.1);
        font-size: 12px;
    }
    
    QTableWidget::item {
        padding: 8px;
        border-bottom: 1px solid rgba(0, 255, 255, 0.1);
    }
    
    QTableWidget::item:selected {
        background: rgba(0, 255, 255, 0.2);
        color: #ffffff;
    }
    
    QHeaderView::section {
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 #2a3a6a, stop: 1 #1a2a4a);
        color: #00ffff;
        padding: 10px;
        border: none;
        border-right: 1px solid rgba(0, 255, 255, 0.2);
        border-bottom: 1px solid rgba(0, 255, 255, 0.4);
        font-weight: bold;
        font-size: 12px;
    }
    
    /* تسميات - Labels */
    QLabel {
        color: #c0d0f0;
        font-size: 13px;
    }
    
    QLabel#titleLabel {
        color: #00ffff;
        font-size: 24px;
        font-weight: bold;
        padding: 15px;
    }
    
    QLabel#subtitleLabel {
        color: #a0b0d0;
        font-size: 16px;
        padding: 5px 15px;
    }
    
    QLabel#statsLabel {
        color: #ffffff;
        font-size: 18px;
        font-weight: bold;
        padding: 5px;
    }
    
    QLabel#statsValue {
        color: #00ffff;
        font-size: 20px;
        font-weight: bold;
        padding: 5px;
    }
    
    /* مجموعات - Group Boxes */
    QGroupBox {
        color: #00ffff;
        font-weight: bold;
        font-size: 14px;
        border: 1px solid rgba(0, 255, 255, 0.3);
        border-radius: 10px;
        margin-top: 15px;
        padding-top: 15px;
        background: rgba(20, 25, 50, 0.5);
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 15px;
        padding: 0 10px;
        background: transparent;
    }
    
    /* صناديق الاختيار - Checkboxes */
    QCheckBox {
        color: #c0d0f0;
        spacing: 8px;
        font-size: 13px;
    }
    
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 2px solid rgba(0, 255, 255, 0.5);
        background: transparent;
    }
    
    QCheckBox::indicator:checked {
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 #00bfff, stop: 1 #0080ff);
        border: 2px solid #00ffff;
    }
    
    /* قوائم منسدلة - Combo Boxes */
    QComboBox {
        background: rgba(30, 35, 60, 0.9);
        color: #ffffff;
        border: 1px solid rgba(0, 255, 255, 0.3);
        border-radius: 6px;
        padding: 8px;
        min-width: 150px;
        font-size: 13px;
    }
    
    QComboBox::drop-down {
        border: none;
        width: 25px;
    }
    
    QComboBox::down-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 8px solid rgba(0, 255, 255, 0.7);
        margin-right: 5px;
    }
    
    QComboBox QAbstractItemView {
        background: rgba(20, 25, 50, 0.98);
        color: #ffffff;
        border: 1px solid rgba(0, 255, 255, 0.3);
        border-radius: 6px;
        selection-background-color: rgba(0, 255, 255, 0.2);
    }
    
    /* حقول الإدخال - Input Fields */
    QLineEdit, QSpinBox, QDoubleSpinBox {
        background: rgba(30, 35, 60, 0.9);
        color: #ffffff;
        border: 1px solid rgba(0, 255, 255, 0.3);
        border-radius: 6px;
        padding: 8px;
        font-size: 13px;
    }
    
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
        border: 2px solid #00ffff;
    }
    
    /* أشرطة التقدم - Progress Bars */
    QProgressBar {
        background: rgba(20, 25, 50, 0.8);
        border: 1px solid rgba(0, 255, 255, 0.3);
        border-radius: 8px;
        text-align: center;
        color: #ffffff;
        font-weight: bold;
        height: 20px;
    }
    
    QProgressBar::chunk {
        background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
            stop: 0 #00bfff, stop: 1 #00ffff);
        border-radius: 7px;
    }
    
    /* شريط التمرير - Scroll Bars */
    QScrollBar:vertical {
        background: transparent;
        width: 12px;
        border-radius: 6px;
    }
    
    QScrollBar::handle:vertical {
        background: rgba(0, 255, 255, 0.3);
        border-radius: 6px;
        min-height: 30px;
    }
    
    QScrollBar::handle:vertical:hover {
        background: rgba(0, 255, 255, 0.5);
    }
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0;
    }
    
    QScrollBar:horizontal {
        background: transparent;
        height: 12px;
        border-radius: 6px;
    }
    
    QScrollBar::handle:horizontal {
        background: rgba(0, 255, 255, 0.3);
        border-radius: 6px;
        min-width: 30px;
    }
    
    QScrollBar::handle:horizontal:hover {
        background: rgba(0, 255, 255, 0.5);
    }
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0;
    }
    
    /* شريط الحالة - Status Bar */
    QStatusBar {
        background: rgba(20, 25, 50, 0.95);
        color: #a0b0d0;
        border-top: 1px solid rgba(0, 255, 255, 0.2);
        font-size: 12px;
    }
    
    /* نوافذ منبثقة - Tooltips */
    QToolTip {
        background: rgba(20, 25, 50, 0.98);
        color: #ffffff;
        border: 1px solid rgba(0, 255, 255, 0.5);
        border-radius: 6px;
        padding: 5px 10px;
        font-size: 12px;
    }
    
    /* بطاقات المعلومات - Info Cards */
    QFrame#infoCard {
        background: rgba(30, 35, 60, 0.7);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 15px;
        padding: 15px;
    }
    
    QFrame#statsCard {
        background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
            stop: 0 rgba(0, 100, 150, 0.3), stop: 1 rgba(0, 50, 100, 0.3));
        border: 1px solid rgba(0, 255, 255, 0.3);
        border-radius: 12px;
        padding: 10px;
    }
    """
    
    # نمط مستوى الخطر المنخفض - Low Risk Style
    LOW_RISK_STYLE = """
        background: rgba(0, 255, 100, 0.15);
        color: #00ff66;
        border: 1px solid rgba(0, 255, 100, 0.5);
        border-radius: 4px;
        padding: 4px 8px;
        font-weight: bold;
    """
    
    # نمط مستوى الخطر المتوسط - Medium Risk Style
    MEDIUM_RISK_STYLE = """
        background: rgba(255, 200, 0, 0.15);
        color: #ffcc00;
        border: 1px solid rgba(255, 200, 0, 0.5);
        border-radius: 4px;
        padding: 4px 8px;
        font-weight: bold;
    """
    
    # نمط مستوى الخطر المرتفع - High Risk Style
    HIGH_RISK_STYLE = """
        background: rgba(255, 50, 50, 0.15);
        color: #ff3333;
        border: 1px solid rgba(255, 50, 50, 0.5);
        border-radius: 4px;
        padding: 4px 8px;
        font-weight: bold;
    """