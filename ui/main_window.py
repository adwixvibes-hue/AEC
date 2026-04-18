"""
النافذة الرئيسية للتطبيق (نسخة محسنة للأداء)
Main Application Window (Performance Optimized)

تحسينات:
- دعم إيقاف العمليات الطويلة
- عرض حالة أفضل للعمليات
- معالجة البيانات الكبيرة بكفاءة
- إضافة تحسين المحفظة باستخدام البرمجة الخطية
"""

import sys
import os
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QStatusBar, QFileDialog, QMessageBox,
    QSplitter, QFrame, QGridLayout, QGroupBox, QComboBox, QCheckBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWebEngineWidgets import QWebEngineView

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from core.risk_models import RiskProfile, PortfolioSummary, RiskLevel
from core.rpa_classifier import CatBoostRiskModel, RPAClassifier
from core.monte_carlo import MonteCarloSimulator
from ui.styles import AppStyles
from ui.workers import DataLoaderWorker, RiskAnalysisWorker, MapGeneratorWorker
from visualization.charts import RiskCharts


class MainWindow(QMainWindow):
    """
    النافذة الرئيسية للتطبيق (نسخة محسنة)
    Main Application Window (Optimized Version)
    """
    
    def __init__(self):
        super().__init__()
        
        # البيانات
        self.profiles: list = []
        self.summary: PortfolioSummary = PortfolioSummary()
        self.model = CatBoostRiskModel(use_cache=True)
        self.simulator = MonteCarloSimulator()
        
        # العمال (Workers)
        self.loader_worker = None
        self.analysis_worker = None
        self.map_worker = None
        
        # مسارات الملفات
        self.data_file_path = ""
        self.map_file_path = os.path.abspath("risk_map.html")
        
        # إعدادات
        self.use_vectorized = True  # استخدام المعالجة المتجهة للسرعة
        
        # تهيئة الواجهة
        self.init_ui()
        
        # تطبيق الأنماط
        self.apply_styles()
    
    def init_ui(self):
        """
        تهيئة واجهة المستخدم
        """
        # إعدادات النافذة
        self.setWindowTitle("R.AI - نظام إدارة المخاطر الزلزالية للجزائر | v2.0 محسن للأداء")
        self.setGeometry(100, 100, 1400, 900)
        
        # إنشاء الويدجت المركزي
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # شريط العنوان
        self.create_header(main_layout)
        
        # شريط الأدوات
        self.create_toolbar(main_layout)
        
        # التبويبات
        self.create_tabs(main_layout)
        
        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setObjectName("progressBar")
        main_layout.addWidget(self.progress_bar)
        
        # شريط الحالة
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("🚀 جاهز للعمل - قم بتحميل ملف البيانات للبدء")
    
    def create_header(self, parent_layout):
        """
        إنشاء ترويسة التطبيق
        """
        header_frame = QFrame()
        header_frame.setObjectName("infoCard")
        header_layout = QHBoxLayout(header_frame)
        
        # العنوان الرئيسي
        title_label = QLabel("🏢 R.AI - نظام إدارة المخاطر الزلزالية")
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)
        
        # شعار محسن للأداء
        perf_label = QLabel("⚡ محسن للأداء | يدعم 30,000+ بوليصة")
        perf_label.setStyleSheet("color: #00ff66; font-size: 12px; padding: 5px;")
        header_layout.addWidget(perf_label)
        
        header_layout.addStretch()
        
        # إحصائيات سريعة
        stats_frame = QFrame()
        stats_frame.setObjectName("statsCard")
        stats_layout = QHBoxLayout(stats_frame)
        
        self.policies_count_label = QLabel("0")
        self.policies_count_label.setObjectName("statsValue")
        stats_layout.addWidget(QLabel("عدد البوليصات:"))
        stats_layout.addWidget(self.policies_count_label)
        
        stats_layout.addSpacing(20)
        
        self.total_insured_label = QLabel("0 دج")
        self.total_insured_label.setObjectName("statsValue")
        stats_layout.addWidget(QLabel("إجمالي التأمين:"))
        stats_layout.addWidget(self.total_insured_label)
        
        stats_layout.addSpacing(20)
        
        self.avg_risk_label = QLabel("0.000")
        self.avg_risk_label.setObjectName("statsValue")
        stats_layout.addWidget(QLabel("متوسط المخاطر:"))
        stats_layout.addWidget(self.avg_risk_label)
        
        header_layout.addWidget(stats_frame)
        
        parent_layout.addWidget(header_frame)
    
    def create_toolbar(self, parent_layout):
        """
        إنشاء شريط الأدوات (مع إضافة زر التحسين)
        """
        toolbar_frame = QFrame()
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # زر تحميل البيانات
        self.load_btn = QPushButton("📂 تحميل البيانات")
        self.load_btn.setObjectName("primaryButton")
        self.load_btn.clicked.connect(self.load_data_file)
        toolbar_layout.addWidget(self.load_btn)
        
        # زر تحليل المخاطر
        self.analyze_btn = QPushButton("🔍 تحليل المخاطر")
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.clicked.connect(self.run_risk_analysis)
        toolbar_layout.addWidget(self.analyze_btn)
        
        # زر تحسين المحفظة (جديد)
        self.optimize_btn = QPushButton("🎯 تحسين المحفظة")
        self.optimize_btn.setEnabled(False)
        self.optimize_btn.setToolTip("تحسين المحفظة باستخدام البرمجة الخطية - اختيار البوليصات المقترح تقويتها")
        self.optimize_btn.clicked.connect(self.open_optimization)
        toolbar_layout.addWidget(self.optimize_btn)
        
        # زر إنشاء الخريطة
        self.map_btn = QPushButton("🗺️ إنشاء الخريطة")
        self.map_btn.setEnabled(False)
        self.map_btn.clicked.connect(self.generate_map)
        toolbar_layout.addWidget(self.map_btn)
        
        # زر تصدير التقرير
        self.export_btn = QPushButton("📊 تصدير التقرير")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_report)
        toolbar_layout.addWidget(self.export_btn)
        
        # زر إيقاف
        self.stop_btn = QPushButton("⏹️ إيقاف")
        self.stop_btn.setObjectName("dangerButton")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_current_operation)
        toolbar_layout.addWidget(self.stop_btn)
        
        toolbar_layout.addStretch()
        
        # خيارات متقدمة
        toolbar_layout.addWidget(QLabel("المعالجة السريعة:"))
        self.vectorized_checkbox = QCheckBox()
        self.vectorized_checkbox.setChecked(True)
        self.vectorized_checkbox.setToolTip("استخدام المعالجة المتجهة للسرعة (موصى به للبيانات الكبيرة)")
        toolbar_layout.addWidget(self.vectorized_checkbox)
        
        toolbar_layout.addSpacing(20)
        
        # قائمة اختيار المحاكاة
        toolbar_layout.addWidget(QLabel("عدد المحاكاة:"))
        self.simulation_combo = QComboBox()
        self.simulation_combo.addItems(["1000", "2000", "3000", "5000"])
        self.simulation_combo.setCurrentText("2000")
        self.simulation_combo.setToolTip("عدد محاكاة مونت كارلو (قيمة أقل = أسرع)")
        toolbar_layout.addWidget(self.simulation_combo)
        
        parent_layout.addWidget(toolbar_frame)
    
    def create_tabs(self, parent_layout):
        """
        إنشاء التبويبات
        """
        self.tab_widget = QTabWidget()
        
        # التبويب 1: الخريطة العالمية
        self.map_tab = QWidget()
        self.create_map_tab()
        self.tab_widget.addTab(self.map_tab, "🗺️ الخريطة العالمية")
        
        # التبويب 2: تحليلات المخاطر
        self.analytics_tab = QWidget()
        self.create_analytics_tab()
        self.tab_widget.addTab(self.analytics_tab, "📈 تحليلات المخاطر")
        
        # التبويب 3: جدول المحفظة
        self.portfolio_tab = QWidget()
        self.create_portfolio_tab()
        self.tab_widget.addTab(self.portfolio_tab, "📋 جدول المحفظة")
        
        parent_layout.addWidget(self.tab_widget)
    
    def create_map_tab(self):
        """
        إنشاء تبويب الخريطة
        """
        layout = QVBoxLayout(self.map_tab)
        
        # عارض الويب للخريطة
        self.web_view = QWebEngineView()
        
        # رسالة افتراضية
        default_html = """
        <html>
        <head>
            <style>
                body {
                    background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
                .message {
                    text-align: center;
                    color: #ffffff;
                    padding: 40px;
                    background: rgba(0, 255, 255, 0.1);
                    border-radius: 20px;
                    border: 1px solid rgba(0, 255, 255, 0.3);
                    max-width: 600px;
                }
                h1 {
                    color: #00ffff;
                    font-size: 32px;
                    margin-bottom: 20px;
                }
                p {
                    color: #a0b0d0;
                    font-size: 16px;
                    line-height: 1.6;
                }
                .icon {
                    font-size: 64px;
                    margin-bottom: 20px;
                }
                .note {
                    color: #00ff66;
                    font-size: 14px;
                    margin-top: 30px;
                    padding: 15px;
                    background: rgba(0, 255, 100, 0.1);
                    border-radius: 10px;
                }
            </style>
        </head>
        <body>
            <div class="message">
                <div class="icon">🗺️</div>
                <h1>خريطة المخاطر الزلزالية</h1>
                <p>قم بتحميل البيانات وتشغيل تحليل المخاطر</p>
                <p>ثم اضغط على "إنشاء الخريطة" لعرض النتائج</p>
                <div class="note">
                    ⚡ النظام محسن لمعالجة حتى 30,000 بوليصة<br>
                    🎯 سيتم استخدام عينة ممثلة للخريطة للبيانات الكبيرة
                </div>
            </div>
        </body>
        </html>
        """
        self.web_view.setHtml(default_html)
        
        layout.addWidget(self.web_view)
    
    def create_analytics_tab(self):
        """
        إنشاء تبويب التحليلات
        """
        layout = QVBoxLayout(self.analytics_tab)
        
        # تقسيم أفقي
        splitter = QSplitter(Qt.Horizontal)
        
        # الجزء الأيسر
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        risk_group = QGroupBox("توزيع درجات المخاطر")
        risk_layout = QVBoxLayout(risk_group)
        self.risk_dist_container = QWidget()
        self.risk_dist_layout = QVBoxLayout(self.risk_dist_container)
        risk_layout.addWidget(self.risk_dist_container)
        left_layout.addWidget(risk_group)
        
        pie_group = QGroupBox("توزيع مستويات المخاطر")
        pie_layout = QVBoxLayout(pie_group)
        self.pie_chart_container = QWidget()
        self.pie_chart_layout = QVBoxLayout(self.pie_chart_container)
        pie_layout.addWidget(self.pie_chart_container)
        left_layout.addWidget(pie_group)
        
        splitter.addWidget(left_widget)
        
        # الجزء الأيمن
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        loss_group = QGroupBox("توزيع الخسائر (مونت كارلو)")
        loss_layout = QVBoxLayout(loss_group)
        self.loss_dist_container = QWidget()
        self.loss_dist_layout = QVBoxLayout(self.loss_dist_container)
        loss_layout.addWidget(self.loss_dist_container)
        right_layout.addWidget(loss_group)
        
        exposure_group = QGroupBox("التعرض التأميني حسب الولاية")
        exposure_layout = QVBoxLayout(exposure_group)
        self.exposure_chart_container = QWidget()
        self.exposure_chart_layout = QVBoxLayout(self.exposure_chart_container)
        exposure_layout.addWidget(self.exposure_chart_container)
        right_layout.addWidget(exposure_group)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([600, 600])
        
        layout.addWidget(splitter)
        
        self.show_analytics_placeholder()
    
    def create_portfolio_tab(self):
        """
        إنشاء تبويب المحفظة
        """
        layout = QVBoxLayout(self.portfolio_tab)
        
        title_label = QLabel("أعلى المناطق من حيث المخاطر")
        title_label.setObjectName("subtitleLabel")
        layout.addWidget(title_label)
        
        self.portfolio_table = QTableWidget()
        self.portfolio_table.setColumnCount(8)
        self.portfolio_table.setHorizontalHeaderLabels([
            "الولاية", "البلدية", "المنطقة الزلزالية",
            "رأس المال المؤمن", "درجة المخاطر", "مستوى الخطر",
            "نوع المبنى", "عمر المبنى"
        ])
        
        header = self.portfolio_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.portfolio_table)
        
        # إحصائيات إضافية
        stats_frame = QFrame()
        stats_frame.setObjectName("statsCard")
        stats_layout = QGridLayout(stats_frame)
        
        stats_layout.addWidget(QLabel("📊 إحصائيات المحفظة:"), 0, 0, 1, 4)
        
        stats_layout.addWidget(QLabel("VaR 95%:"), 1, 0)
        self.var95_label = QLabel("-")
        stats_layout.addWidget(self.var95_label, 1, 1)
        
        stats_layout.addWidget(QLabel("VaR 99%:"), 1, 2)
        self.var99_label = QLabel("-")
        stats_layout.addWidget(self.var99_label, 1, 3)
        
        stats_layout.addWidget(QLabel("TVaR 95%:"), 2, 0)
        self.tvar95_label = QLabel("-")
        stats_layout.addWidget(self.tvar95_label, 2, 1)
        
        stats_layout.addWidget(QLabel("الخسارة المتوقعة:"), 2, 2)
        self.expected_loss_label = QLabel("-")
        stats_layout.addWidget(self.expected_loss_label, 2, 3)
        
        stats_layout.addWidget(QLabel("أقصى خسارة محتملة:"), 3, 0)
        self.max_loss_label = QLabel("-")
        stats_layout.addWidget(self.max_loss_label, 3, 1)
        
        layout.addWidget(stats_frame)
    
    def show_analytics_placeholder(self):
        """
        عرض رسالة افتراضية في تبويب التحليلات
        """
        placeholder = QLabel(
            "📈 قم بتحميل البيانات وتشغيل تحليل المخاطر لعرض الرسوم البيانية\n\n"
            "سيظهر هنا:\n"
            "• توزيع درجات المخاطر\n"
            "• توزيع مستويات المخاطر\n"
            "• توزيع الخسائر (مونت كارلو)\n"
            "• التعرض التأميني حسب الولاية\n\n"
            "⚡ النظام محسن لمعالجة حتى 30,000 بوليصة"
        )
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("""
            color: #a0b0d0;
            font-size: 15px;
            padding: 50px;
            line-height: 1.8;
        """)
        
        self.risk_dist_layout.addWidget(placeholder)
    
    def apply_styles(self):
        """
        تطبيق أنماط QSS
        """
        self.setStyleSheet(AppStyles.MAIN_STYLE)
    
    # ==================== وظائف التحكم ====================
    
    def set_buttons_enabled(self, enabled: bool):
        """
        تفعيل/تعطيل الأزرار
        """
        self.load_btn.setEnabled(enabled)
        self.analyze_btn.setEnabled(enabled and len(self.profiles) > 0)
        self.optimize_btn.setEnabled(enabled and len(self.profiles) > 0 and self.summary.total_policies > 0)
        self.map_btn.setEnabled(enabled and len(self.profiles) > 0)
        self.export_btn.setEnabled(enabled and self.summary.total_policies > 0)
    
    def stop_current_operation(self):
        """
        إيقاف العملية الحالية
        """
        if self.loader_worker and self.loader_worker.isRunning():
            self.loader_worker.stop()
            self.status_bar.showMessage("⏹️ جاري إيقاف التحميل...")
            self.stop_btn.setEnabled(False)
        elif self.analysis_worker and self.analysis_worker.isRunning():
            self.analysis_worker.stop()
            self.status_bar.showMessage("⏹️ جاري إيقاف التحليل...")
            self.stop_btn.setEnabled(False)
        elif self.map_worker and self.map_worker.isRunning():
            self.map_worker.stop()
            self.status_bar.showMessage("⏹️ جاري إيقاف إنشاء الخريطة...")
            self.stop_btn.setEnabled(False)
    
    # ==================== وظائف تحميل البيانات ====================
    
    def load_data_file(self):
        """
        تحميل ملف البيانات
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "اختر ملف البيانات",
            "",
            "Excel Files (*.xlsx *.xls);;CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        self.data_file_path = file_path
        self.status_bar.showMessage("📂 جاري تحميل البيانات...")
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.set_buttons_enabled(False)
        self.stop_btn.setEnabled(True)
        
        self.loader_worker = DataLoaderWorker(file_path)
        self.loader_worker.progress_updated.connect(self.update_progress)
        self.loader_worker.data_loaded.connect(self.on_data_loaded)
        self.loader_worker.error_occurred.connect(self.on_error)
        self.loader_worker.finished.connect(lambda: self.stop_btn.setEnabled(False))
        self.loader_worker.start()
    
    def on_data_loaded(self, profiles: list):
        """
        عند اكتمال تحميل البيانات
        """
        self.profiles = profiles
        self.status_bar.showMessage(f"✅ تم تحميل {len(profiles):,} بوليصة")
        
        total_insured = sum(p.sum_insured for p in profiles)
        self.policies_count_label.setText(f"{len(profiles):,}")
        self.total_insured_label.setText(f"{total_insured:,.0f} دج")
        
        self.progress_bar.setVisible(False)
        self.set_buttons_enabled(True)
        
        QMessageBox.information(
            self,
            "✅ تم التحميل",
            f"تم تحميل {len(profiles):,} بوليصة بنجاح.\n"
            f"إجمالي رأس المال المؤمن: {total_insured:,.0f} دج"
        )
    
    # ==================== وظائف تحليل المخاطر ====================
    
    def run_risk_analysis(self):
        """
        تشغيل تحليل المخاطر
        """
        if not self.profiles:
            QMessageBox.warning(self, "⚠️ تحذير", "لا توجد بيانات للتحليل")
            return
        
        n_profiles = len(self.profiles)
        
        # تأكيد للمستخدم إذا كانت البيانات كبيرة
        if n_profiles > 20000:
            reply = QMessageBox.question(
                self,
                "⚠️ بيانات كبيرة",
                f"عدد البوليصات كبير ({n_profiles:,}).\n"
                f"قد يستغرق التحليل بعض الوقت.\n\n"
                f"هل تريد المتابعة؟",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.No:
                return
        
        self.status_bar.showMessage(f"🔍 جاري تحليل {n_profiles:,} بوليصة...")
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.set_buttons_enabled(False)
        self.stop_btn.setEnabled(True)
        
        use_vectorized = self.vectorized_checkbox.isChecked()
        
        self.analysis_worker = RiskAnalysisWorker(self.profiles, use_vectorized)
        self.analysis_worker.progress_updated.connect(self.update_progress)
        self.analysis_worker.analysis_completed.connect(self.on_analysis_completed)
        self.analysis_worker.error_occurred.connect(self.on_error)
        self.analysis_worker.finished.connect(lambda: self.stop_btn.setEnabled(False))
        self.analysis_worker.start()
    
    def on_analysis_completed(self, profiles: list, summary: PortfolioSummary):
        """
        عند اكتمال تحليل المخاطر
        """
        self.profiles = profiles
        self.summary = summary
        
        total_insured = summary.total_sum_insured
        avg_risk = summary.calculate_average_risk()
        
        self.policies_count_label.setText(f"{summary.total_policies:,}")
        self.total_insured_label.setText(f"{total_insured:,.0f} دج")
        self.avg_risk_label.setText(f"{avg_risk:.3f}")
        
        self.update_portfolio_table()
        
        self.var95_label.setText(f"{summary.var_95:,.0f} دج")
        self.var99_label.setText(f"{summary.var_99:,.0f} دج")
        self.tvar95_label.setText(f"{summary.tvar_95:,.0f} دج")
        self.expected_loss_label.setText(f"{summary.expected_loss:,.0f} دج")
        self.max_loss_label.setText(f"{summary.max_probable_loss:,.0f} دج")
        
        self.update_charts()
        
        self.progress_bar.setVisible(False)
        self.set_buttons_enabled(True)
        
        # إحصائيات سريعة
        high_risk_pct = (summary.high_risk_count / summary.total_policies * 100) if summary.total_policies > 0 else 0
        self.status_bar.showMessage(
            f"✅ اكتمل التحليل | خطر مرتفع: {summary.high_risk_count:,} ({high_risk_pct:.1f}%) | "
            f"متوسط المخاطر: {avg_risk:.3f}"
        )
        
        self.tab_widget.setCurrentIndex(1)
    
    # ==================== وظائف تحسين المحفظة ====================
    
    def open_optimization(self):
        """
        فتح نافذة تحسين المحفظة
        """
        if not self.profiles or self.summary.total_policies == 0:
            QMessageBox.warning(self, "⚠️ تحذير", "الرجاء تحليل المخاطر أولاً")
            return
        
        # استيراد النافذة هنا لتجنب مشاكل الاستيراد الدائرية
        from ui.optimization_dialog import OptimizationDialog
        
        dialog = OptimizationDialog(self.profiles, self.summary, self)
        dialog.exec_()
    
    # ==================== وظائف الخريطة ====================
    
    def generate_map(self):
        """
        إنشاء الخريطة
        """
        if not self.profiles:
            QMessageBox.warning(self, "⚠️ تحذير", "لا توجد بيانات لإنشاء الخريطة")
            return
        
        self.status_bar.showMessage("🗺️ جاري إنشاء الخريطة...")
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.set_buttons_enabled(False)
        self.stop_btn.setEnabled(True)
        
        self.map_worker = MapGeneratorWorker(self.profiles, self.map_file_path)
        self.map_worker.progress_updated.connect(self.update_progress)
        self.map_worker.map_generated.connect(self.on_map_generated)
        self.map_worker.error_occurred.connect(self.on_error)
        self.map_worker.finished.connect(lambda: self.stop_btn.setEnabled(False))
        self.map_worker.start()
    
    def on_map_generated(self, map_path: str):
        """
        عند اكتمال إنشاء الخريطة
        """
        from PyQt5.QtCore import QUrl
        
        # تحويل المسار إلى QUrl بشكل صحيح
        url = QUrl.fromLocalFile(map_path)
        self.web_view.load(url)
        
        self.progress_bar.setVisible(False)
        self.set_buttons_enabled(True)
        
        self.status_bar.showMessage("✅ تم إنشاء الخريطة بنجاح")
        
        self.tab_widget.setCurrentIndex(0)
    
    # ==================== وظائف التصدير ====================
    
    def export_report(self):
        """
        تصدير التقرير
        """
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "حفظ التقرير",
            "risk_report.xlsx",
            "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            import pandas as pd
            
            data = []
            for p in self.profiles:
                data.append({
                    'الولاية': p.wilaya_name,
                    'البلدية': p.commune_name,
                    'رأس المال المؤمن': p.sum_insured,
                    'درجة المخاطر': p.risk_score,
                    'مستوى الخطر': p.risk_level.name if p.risk_level else '-',
                    'المنطقة الزلزالية': p.seismic_zone.name if p.seismic_zone else '-',
                    'عمر المبنى': p.building_age,
                    'عدد الطوابق': p.number_of_floors,
                    'نوع الهيكل': p.structure_type.value if p.structure_type else '-',
                })
            
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False, sheet_name='تحليل المخاطر')
            
            QMessageBox.information(self, "✅ تم التصدير", f"تم حفظ التقرير في:\n{file_path}")
            self.status_bar.showMessage(f"✅ تم تصدير التقرير: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "❌ خطأ", f"فشل تصدير التقرير: {str(e)}")
    
    # ==================== وظائف مساعدة ====================
    
    def update_portfolio_table(self):
        """
        تحديث جدول المحفظة
        """
        sorted_profiles = sorted(self.profiles, key=lambda x: x.risk_score, reverse=True)
        top_n = sorted_profiles[:10]  # عرض أعلى 10
        
        self.portfolio_table.setRowCount(len(top_n))
        
        for i, profile in enumerate(top_n):
            self.portfolio_table.setItem(i, 0, QTableWidgetItem(profile.wilaya_name))
            self.portfolio_table.setItem(i, 1, QTableWidgetItem(profile.commune_name))
            self.portfolio_table.setItem(i, 2, QTableWidgetItem(
                profile.seismic_zone.name if profile.seismic_zone else "-"
            ))
            self.portfolio_table.setItem(i, 3, QTableWidgetItem(f"{profile.sum_insured:,.0f}"))
            self.portfolio_table.setItem(i, 4, QTableWidgetItem(f"{profile.risk_score:.3f}"))
            
            risk_item = QTableWidgetItem(profile.risk_level.name if profile.risk_level else "-")
            if profile.risk_level == RiskLevel.LOW:
                risk_item.setForeground(QColor('#00ff66'))
            elif profile.risk_level == RiskLevel.MEDIUM:
                risk_item.setForeground(QColor('#ffcc00'))
            else:
                risk_item.setForeground(QColor('#ff3333'))
            self.portfolio_table.setItem(i, 5, risk_item)
            
            self.portfolio_table.setItem(i, 6, QTableWidgetItem(
                profile.structure_type.value if profile.structure_type else "-"
            ))
            self.portfolio_table.setItem(i, 7, QTableWidgetItem(str(profile.building_age)))
    
    def update_charts(self):
        """
        تحديث الرسوم البيانية
        """
        self.clear_layout(self.risk_dist_layout)
        self.clear_layout(self.pie_chart_layout)
        self.clear_layout(self.loss_dist_layout)
        self.clear_layout(self.exposure_chart_layout)
        
        if self.profiles:
            risk_chart = RiskCharts.create_risk_distribution_chart(self.profiles)
            self.risk_dist_layout.addWidget(risk_chart)
            
            pie_chart = RiskCharts.create_pie_chart(self.summary)
            self.pie_chart_layout.addWidget(pie_chart)
            
            if hasattr(self.summary, 'loss_samples') and len(self.summary.loss_samples) > 0:
                loss_chart = RiskCharts.create_loss_distribution_chart(
                    self.summary.loss_samples,
                    self.summary.var_95,
                    self.summary.var_99
                )
                self.loss_dist_layout.addWidget(loss_chart)
            
            if self.summary.wilaya_exposure:
                exposure_chart = RiskCharts.create_wilaya_exposure_chart(
                    self.summary.wilaya_exposure
                )
                self.exposure_chart_layout.addWidget(exposure_chart)
    
    def clear_layout(self, layout):
        """
        مسح التخطيط
        """
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
    
    def update_progress(self, value: int, message: str):
        """
        تحديث شريط التقدم
        """
        self.progress_bar.setValue(value)
        self.status_bar.showMessage(message)
    
    def on_error(self, error_message: str):
        """
        معالجة الأخطاء
        """
        self.progress_bar.setVisible(False)
        self.set_buttons_enabled(True)
        self.stop_btn.setEnabled(False)
        
        QMessageBox.critical(self, "❌ خطأ", error_message)
        self.status_bar.showMessage(f"❌ خطأ: {error_message}")
    
    def closeEvent(self, event):
        """
        حدث إغلاق النافذة
        """
        # إيقاف جميع العمليات
        if self.loader_worker and self.loader_worker.isRunning():
            self.loader_worker.stop()
            self.loader_worker.wait(1000)
        if self.analysis_worker and self.analysis_worker.isRunning():
            self.analysis_worker.stop()
            self.analysis_worker.wait(1000)
        if self.map_worker and self.map_worker.isRunning():
            self.map_worker.stop()
            self.map_worker.wait(1000)
        
        # تنظيف الملفات المؤقتة
        if os.path.exists(self.map_file_path):
            try:
                os.remove(self.map_file_path)
            except:
                pass
        
        event.accept()