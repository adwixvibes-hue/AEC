#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
R.AI - نظام إدارة المخاطر الزلزالية للجزائر
Risk Management System for Algerian Seismic Exposure

تم التطوير بواسطة: فريق R.AI
الإصدار: 1.0.0

هذا التطبيق يقوم بتحليل المخاطر الزلزالية لمحفظة التأمين
باستخدام القواعد الجزائرية RPA 99 ونموذج CatBoost للتعلم الآلي
"""

import sys
import os

# إضافة المسارات إلى PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont, QColor

from ui.main_window import MainWindow
from ui.styles import AppStyles


def create_splash_screen():
    """
    إنشاء شاشة البداية
    Create Splash Screen
    """
    # إنشاء صورة للشاشة
    splash_pixmap = QPixmap(500, 300)
    splash_pixmap.fill(QColor('#0a0e27'))
    
    splash = QSplashScreen(splash_pixmap, Qt.WindowStaysOnTopHint)
    
    # إضافة نص على الشاشة
    font = QFont("Segoe UI", 20, QFont.Bold)
    splash.setFont(font)
    
    splash.showMessage(
        "🏢 R.AI\n\n"
        "نظام إدارة المخاطر الزلزالية للجزائر\n"
        "Seismic Risk Management System\n\n"
        "جار التحميل...",
        Qt.AlignCenter,
        QColor('#00ffff')
    )
    
    return splash


def main():
    """
    الدالة الرئيسية للتطبيق
    Main Application Function
    """
    # إنشاء التطبيق
    app = QApplication(sys.argv)
    app.setApplicationName("R.AI")
    app.setApplicationVersion("1.0.0")
    app.setStyle('Fusion')
    
    # تطبيق الأنماط
    app.setStyleSheet(AppStyles.MAIN_STYLE)
    
    # عرض شاشة البداية
    splash = create_splash_screen()
    splash.show()
    app.processEvents()
    
    # إنشاء النافذة الرئيسية
    window = MainWindow()
    
    # إغلاق شاشة البداية وإظهار النافذة
    QTimer.singleShot(2000, lambda: (
        splash.finish(window),
        window.showMaximized()
    ))
    
    # تشغيل التطبيق
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()