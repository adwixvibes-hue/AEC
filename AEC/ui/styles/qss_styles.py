"""
أنماط الواجهة
"""

class DarkTheme:
    MAIN_STYLE = """
    QMainWindow, QWidget {
        background-color: #1e1e2e;
        color: #cdd6f4;
        font-family: 'Segoe UI', sans-serif;
        font-size: 12px;
    }
    
    QPushButton {
        background-color: #313244;
        color: #cdd6f4;
        border: 1px solid #45475a;
        border-radius: 5px;
        padding: 8px 16px;
        font-weight: bold;
    }
    
    QPushButton:hover {
        background-color: #45475a;
        border-color: #89b4fa;
    }
    
    QPushButton#primaryButton {
        background-color: #89b4fa;
        color: #1e1e2e;
    }
    
    QLineEdit, QTextEdit, QComboBox {
        background-color: #313244;
        color: #cdd6f4;
        border: 1px solid #45475a;
        border-radius: 5px;
        padding: 8px;
    }
    
    QTableWidget {
        background-color: #1e1e2e;
        border: 1px solid #45475a;
        gridline-color: #313244;
    }
    
    QTableWidget::item {
        padding: 8px;
    }
    
    QHeaderView::section {
        background-color: #313244;
        padding: 8px;
        font-weight: bold;
    }
    
    QTabWidget::pane {
        border: 1px solid #45475a;
        border-radius: 5px;
    }
    
    QTabBar::tab {
        background-color: #313244;
        padding: 10px 20px;
    }
    
    QTabBar::tab:selected {
        background-color: #1e1e2e;
        border-bottom: 3px solid #89b4fa;
    }
    
    QGroupBox {
        border: 2px solid #45475a;
        border-radius: 8px;
        margin-top: 1.5em;
        padding-top: 1.5em;
    }
    
    QGroupBox::title {
        color: #89b4fa;
        left: 15px;
        padding: 0 10px;
    }
    
    QProgressBar {
        background-color: #313244;
        border: 1px solid #45475a;
        border-radius: 5px;
    }
    
    QProgressBar::chunk {
        background-color: #89b4fa;
        border-radius: 5px;
    }
    
    #dashboardCard {
        background-color: #313244;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #45475a;
    }
    
    #titleLabel {
        font-size: 20px;
        font-weight: bold;
        color: #89b4fa;
    }
    
    #valueLabel {
        font-size: 28px;
        font-weight: bold;
    }
    
    #metricLabel {
        font-size: 14px;
        color: #a6adc8;
    }
    """

def get_theme(theme_name: str = 'dark'):
    return DarkTheme.MAIN_STYLE