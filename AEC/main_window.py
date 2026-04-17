"""
النافذة الرئيسية
"""

import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
from datetime import datetime

from risk_analyzer import RiskAnalyzer
from ml_classifier import RiskClassifier
from monte_carlo import MonteCarloSimulator
from ui.styles.qss_styles import get_theme
from constants import Colors, WILAYA_COORDINATES


class MainWindow(QMainWindow):
    """النافذة الرئيسية"""
    
    def __init__(self):
        super().__init__()
        
        # تهيئة المحللات
        self.risk_analyzer = RiskAnalyzer()
        self.risk_classifier = RiskClassifier()
        self.monte_carlo = MonteCarloSimulator()
        
        # تهيئة البيانات
        self.risk_analyzer.initialize_algeria_data()
        
        # تحميل ملفات CSV
        data_files = ["Insurancedata2023.csv", "Insurancedata2024.csv", "Insurancedata2025.csv"]
        existing = [f for f in data_files if os.path.exists(f)]
        
        if existing:
            self.risk_analyzer.load_csv_files(existing)
        else:
            print("⚠️ لا توجد ملفات بيانات، سيتم إنشاء بيانات تجريبية")
            self.generate_sample_data()
        
        # إعداد الواجهة
        self.setWindowTitle("نظام إدارة مخاطر التأمين - الجزائر")
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet(get_theme('dark'))
        
        self.setup_ui()
        self.update_dashboard()
    
    def generate_sample_data(self):
        """توليد بيانات تجريبية"""
        wilayas = list(self.risk_analyzer.regions_data.keys())
        for i in range(1000):
            wilaya = np.random.choice(wilayas)
            value = np.random.uniform(100000, 5000000)
            premium = value * 0.005
            from data_models import InsurancePolicy
            policy = InsurancePolicy(
                policy_id=f"SAMPLE-{i:05d}",
                wilaya=wilaya,
                insured_value=value,
                premium=premium,
                building_type=np.random.choice(['mixed', 'reinforced_concrete', 'masonry'])
            )
            self.risk_analyzer.add_policy(policy)
        self.risk_analyzer.calculate_portfolio_metrics()
    
    def setup_ui(self):
        """إعداد الواجهة"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # الهيدر
        header = QHBoxLayout()
        title = QLabel("🏢 نظام إدارة مخاطر التأمين الذكي")
        title.setObjectName("titleLabel")
        header.addWidget(title)
        header.addStretch()
        
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.clicked.connect(self.update_dashboard)
        header.addWidget(refresh_btn)
        
        export_btn = QPushButton("📊 تصدير")
        export_btn.clicked.connect(self.export_report)
        header.addWidget(export_btn)
        
        layout.addLayout(header)
        
        # خط فاصل
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        layout.addWidget(line)
        
        # التبويبات
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_dashboard_tab(), "📈 لوحة التحكم")
        self.tabs.addTab(self.create_portfolio_tab(), "💼 المحفظة")
        self.tabs.addTab(self.create_risk_tab(), "🤖 تصنيف المخاطر")
        self.tabs.addTab(self.create_simulation_tab(), "💰 محاكاة مونتي كارلو")
        self.tabs.addTab(self.create_map_tab(), "🗺️ الخريطة")
        
        layout.addWidget(self.tabs)
        
        # شريط الحالة
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("جاهز")
        self.status_bar.addWidget(self.status_label)
    
    def create_dashboard_tab(self):
        """تبويب لوحة التحكم"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # المؤشرات
        row1 = QHBoxLayout()
        metrics = [
            ("📊 إجمالي المحفظة", f"{self.risk_analyzer.portfolio_summary.total_insured_value:,.0f} دج"),
            ("📄 عدد الوثائق", f"{self.risk_analyzer.portfolio_summary.total_policies:,}"),
            ("⚠️ متوسط الخطورة", f"{self.risk_analyzer.portfolio_summary.average_risk_score:.2f}"),
            ("🎯 تركيز المخاطر", f"{self.risk_analyzer.get_high_risk_concentration_ratio():.1f}%")
        ]
        
        for title, value in metrics:
            card = self.create_card(title, value)
            row1.addWidget(card)
        layout.addLayout(row1)
        
        # الرسوم البيانية
        row2 = QHBoxLayout()
        
        # توزيع المخاطر
        fig1 = Figure(figsize=(5, 4), facecolor='#313244')
        canvas1 = FigureCanvas(fig1)
        ax1 = fig1.add_subplot(111)
        ax1.set_facecolor('#313244')
        
        dist = self.risk_analyzer.get_risk_distribution()
        categories = list(dist.keys())
        values = [dist[c] / 1e6 for c in categories]
        colors = ['#f44336', '#ff9800', '#4caf50']
        
        ax1.bar(categories, values, color=colors)
        ax1.set_ylabel('مليون دج', color='white')
        ax1.tick_params(colors='white')
        ax1.set_title('توزيع المخاطر', color='white')
        
        row2.addWidget(canvas1)
        
        # التركيز الجغرافي
        fig2 = Figure(figsize=(5, 4), facecolor='#313244')
        canvas2 = FigureCanvas(fig2)
        ax2 = fig2.add_subplot(111)
        ax2.set_facecolor('#313244')
        
        df = self.risk_analyzer.calculate_concentration_risk()
        if not df.empty:
            top5 = df.head(5)
            ax2.barh(top5['المنطقة'], top5['مؤشر المخاطر المركب'], color='#89b4fa')
            ax2.set_xlabel('مؤشر المخاطر', color='white')
            ax2.tick_params(colors='white')
            ax2.set_title('أعلى 5 مناطق خطورة', color='white')
        
        row2.addWidget(canvas2)
        layout.addLayout(row2)
        
        # جدول المناطق الخطرة
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(['المنطقة', 'القيمة المؤمنة', 'درجة الخطورة', 'نسبة التركيز'])
        
        if not df.empty:
            high_risk = df[df['فئة المخاطر'] == 'أحمر'].head(10)
            table.setRowCount(len(high_risk))
            for i, (_, row) in enumerate(high_risk.iterrows()):
                table.setItem(i, 0, QTableWidgetItem(row['المنطقة']))
                table.setItem(i, 1, QTableWidgetItem(f"{row['القيمة المؤمنة']:,.0f}"))
                table.setItem(i, 2, QTableWidgetItem(f"{row['درجة الخطورة المعدلة']:.2f}"))
                table.setItem(i, 3, QTableWidgetItem(f"{row['نسبة التركيز']:.1f}%"))
        
        layout.addWidget(table)
        return widget
    
    def create_card(self, title, value):
        """إنشاء بطاقة"""
        card = QWidget()
        card.setObjectName("dashboardCard")
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setObjectName("metricLabel")
        value_label = QLabel(value)
        value_label.setObjectName("valueLabel")
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        return card
    
    def create_portfolio_tab(self):
        """تبويب المحفظة"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # فلتر
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("تصفية حسب الولاية:"))
        
        self.wilaya_combo = QComboBox()
        self.wilaya_combo.addItem("الكل")
        self.wilaya_combo.addItems(sorted(self.risk_analyzer.regions_data.keys()))
        self.wilaya_combo.currentTextChanged.connect(self.filter_portfolio)
        filter_layout.addWidget(self.wilaya_combo)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # الجدول
        self.portfolio_table = QTableWidget()
        self.portfolio_table.setColumnCount(5)
        self.portfolio_table.setHorizontalHeaderLabels(['رقم الوثيقة', 'الولاية', 'القيمة المؤمنة', 'القسط', 'نوع المبنى'])
        layout.addWidget(self.portfolio_table)
        
        self.update_portfolio_table()
        return widget
    
    def update_portfolio_table(self):
        """تحديث جدول المحفظة"""
        policies = self.risk_analyzer.policies[:100]
        self.portfolio_table.setRowCount(len(policies))
        
        for i, p in enumerate(policies):
            self.portfolio_table.setItem(i, 0, QTableWidgetItem(p.policy_id))
            self.portfolio_table.setItem(i, 1, QTableWidgetItem(p.wilaya))
            self.portfolio_table.setItem(i, 2, QTableWidgetItem(f"{p.insured_value:,.0f}"))
            self.portfolio_table.setItem(i, 3, QTableWidgetItem(f"{p.premium:,.0f}"))
            self.portfolio_table.setItem(i, 4, QTableWidgetItem(p.building_type))
    
    def filter_portfolio(self):
        """تصفية المحفظة"""
        wilaya = self.wilaya_combo.currentText()
        if wilaya == "الكل":
            self.update_portfolio_table()
        else:
            filtered = [p for p in self.risk_analyzer.policies if p.wilaya == wilaya][:100]
            self.portfolio_table.setRowCount(len(filtered))
            for i, p in enumerate(filtered):
                self.portfolio_table.setItem(i, 0, QTableWidgetItem(p.policy_id))
                self.portfolio_table.setItem(i, 1, QTableWidgetItem(p.wilaya))
                self.portfolio_table.setItem(i, 2, QTableWidgetItem(f"{p.insured_value:,.0f}"))
                self.portfolio_table.setItem(i, 3, QTableWidgetItem(f"{p.premium:,.0f}"))
                self.portfolio_table.setItem(i, 4, QTableWidgetItem(p.building_type))
    
    def create_risk_tab(self):
        """تبويب تصنيف المخاطر"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # تدريب النموذج
        group1 = QGroupBox("تدريب النموذج")
        g1_layout = QVBoxLayout()
        
        self.train_btn = QPushButton("🚀 تدريب النموذج")
        self.train_btn.setObjectName("primaryButton")
        self.train_btn.clicked.connect(self.train_model)
        g1_layout.addWidget(self.train_btn)
        
        self.train_progress = QProgressBar()
        self.train_progress.setVisible(False)
        g1_layout.addWidget(self.train_progress)
        
        group1.setLayout(g1_layout)
        layout.addWidget(group1)
        
        # النتائج
        group2 = QGroupBox("نتائج التصنيف")
        g2_layout = QVBoxLayout()
        
        self.accuracy_label = QLabel("الدقة: --")
        g2_layout.addWidget(self.accuracy_label)
        
        classify_btn = QPushButton("🔍 تصنيف المحفظة")
        classify_btn.clicked.connect(self.classify_portfolio)
        g2_layout.addWidget(classify_btn)
        
        group2.setLayout(g2_layout)
        layout.addWidget(group2)
        
        layout.addStretch()
        return widget
    
    def train_model(self):
        """تدريب النموذج"""
        self.train_btn.setEnabled(False)
        self.train_progress.setVisible(True)
        self.train_progress.setRange(0, 0)
        self.status_label.setText("جاري تدريب النموذج...")
        
        # تشغيل في thread
        self.train_thread = QThread()
        self.train_worker = TrainWorker(self.risk_classifier, self.risk_analyzer.policies, self.risk_analyzer.regions_data)
        self.train_worker.moveToThread(self.train_thread)
        self.train_thread.started.connect(self.train_worker.run)
        self.train_worker.finished.connect(self.on_train_finished)
        self.train_worker.finished.connect(self.train_thread.quit)
        self.train_worker.finished.connect(self.train_worker.deleteLater)
        self.train_thread.finished.connect(self.train_thread.deleteLater)
        self.train_thread.start()
    
    def on_train_finished(self, results):
        """اكتمل التدريب"""
        self.train_progress.setVisible(False)
        self.train_btn.setEnabled(True)
        
        if results and results.get('accuracy', 0) > 0:
            self.accuracy_label.setText(f"الدقة: {results['accuracy']:.2%}")
            self.status_label.setText(f"اكتمل التدريب - الدقة: {results['accuracy']:.2%}")
            QMessageBox.information(self, "تم", f"تم تدريب النموذج بنجاح!\nالدقة: {results['accuracy']:.2%}")
        else:
            self.status_label.setText("فشل التدريب")
            QMessageBox.warning(self, "خطأ", "فشل تدريب النموذج")
    
    def classify_portfolio(self):
        """تصنيف المحفظة"""
        if not self.risk_classifier.is_trained:
            QMessageBox.warning(self, "تنبيه", "الرجاء تدريب النموذج أولاً")
            return
        
        self.status_label.setText("جاري التصنيف...")
        results = self.risk_classifier.predict(self.risk_analyzer.policies, self.risk_analyzer.regions_data)
        
        if not results.empty:
            summary = results['risk_category'].value_counts()
            text = "ملخص التصنيف:\n\n"
            for cat, count in summary.items():
                text += f"• {cat}: {count:,} وثيقة ({count/len(results)*100:.1f}%)\n"
            QMessageBox.information(self, "نتائج التصنيف", text)
        
        self.status_label.setText("اكتمل التصنيف")
    
    def create_simulation_tab(self):
        """تبويب المحاكاة"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # لوحة التحكم
        control = QWidget()
        control.setMaximumWidth(350)
        c_layout = QVBoxLayout(control)
        
        # اختيار المنطقة
        self.sim_region = QComboBox()
        regions = [r for r in self.risk_analyzer.regions_data.keys() 
                  if self.risk_analyzer.regions_data[r].total_insured_value > 0]
        self.sim_region.addItems(regions)
        c_layout.addWidget(QLabel("المنطقة:"))
        c_layout.addWidget(self.sim_region)
        
        # عدد المحاولات
        self.sim_count = QSpinBox()
        self.sim_count.setRange(1000, 50000)
        self.sim_count.setValue(10000)
        c_layout.addWidget(QLabel("عدد المحاكاة:"))
        c_layout.addWidget(self.sim_count)
        
        # نسبة الاحتفاظ
        self.sim_retention = QDoubleSpinBox()
        self.sim_retention.setRange(10, 50)
        self.sim_retention.setValue(30)
        self.sim_retention.setSuffix(" %")
        c_layout.addWidget(QLabel("نسبة الاحتفاظ:"))
        c_layout.addWidget(self.sim_retention)
        
        # معلومات المنطقة
        self.region_info = QTextEdit()
        self.region_info.setReadOnly(True)
        self.region_info.setMaximumHeight(150)
        c_layout.addWidget(QLabel("معلومات المنطقة:"))
        c_layout.addWidget(self.region_info)
        
        # زر التشغيل
        run_btn = QPushButton("🎲 تشغيل المحاكاة")
        run_btn.setObjectName("primaryButton")
        run_btn.clicked.connect(self.run_simulation)
        c_layout.addWidget(run_btn)
        
        c_layout.addStretch()
        layout.addWidget(control)
        
        # النتائج
        self.sim_results = QTextEdit()
        self.sim_results.setReadOnly(True)
        self.sim_results.setFont(QFont("Courier", 10))
        layout.addWidget(self.sim_results)
        
        # تحديث المعلومات عند تغيير المنطقة
        self.sim_region.currentTextChanged.connect(self.update_region_info)
        self.update_region_info(self.sim_region.currentText())
        
        return widget
    
    def update_region_info(self, region_name):
        """تحديث معلومات المنطقة"""
        if region_name and region_name in self.risk_analyzer.regions_data:
            r = self.risk_analyzer.regions_data[region_name]
            text = f"""
<b>المنطقة:</b> {region_name}<br>
<b>المنطقة الزلزالية:</b> {r.seismic_zone}<br>
<b>درجة الخطورة:</b> {r.adjusted_risk_score:.2f}<br>
<b>فئة المخاطر:</b> {r.get_risk_category()}<br>
<b>عدد الوثائق:</b> {r.policy_count:,}<br>
<b>القيمة المؤمنة:</b> {r.total_insured_value:,.0f} دج
"""
            self.region_info.setHtml(text)
    
    def run_simulation(self):
        """تشغيل المحاكاة"""
        region = self.sim_region.currentText()
        n = self.sim_count.value()
        retention = self.sim_retention.value() / 100
        
        self.status_label.setText(f"جاري المحاكاة ({n:,} مرة)...")
        
        r = self.risk_analyzer.regions_data[region]
        value = r.total_insured_value if r.total_insured_value > 0 else 100000000
        
        self.monte_carlo.retention_ratio = retention
        result = self.monte_carlo.run_simulation(value, r.adjusted_risk_score, n, region)
        
        report = f"""
{'='*60}
محاكاة مونتي كارلو - {region}
{'='*60}

📊 الخسائر الإجمالية:
• المتوسط: {result.mean_loss:,.0f} دج
• الانحراف: {result.std_loss:,.0f} دج
• VaR 95%: {result.var_95:,.0f} دج
• VaR 99%: {result.var_99:,.0f} دج
• TVaR 99%: {result.tvar_99:,.0f} دج
• الحد الأقصى: {result.max_loss:,.0f} دج

💰 حصة الشركة ({retention*100:.0f}%):
• المتوسط: {result.mean_company_loss:,.0f} دج
• VaR 99%: {result.var_99_company:,.0f} دج

📈 المخاطر:
• احتمالية الخسارة > 20%: {np.mean(result.loss_distribution > value * 0.2):.2%}

{'='*60}
"""
        self.sim_results.setText(report)
        self.status_label.setText("اكتملت المحاكاة")
    
    def create_map_tab(self):
        """تبويب الخريطة"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        fig = Figure(figsize=(10, 8), facecolor='#1e1e2e')
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.set_facecolor('#1e1e2e')
        
        df = self.risk_analyzer.calculate_concentration_risk()
        colors = {'أحمر': '#f44336', 'برتقالي': '#ff9800', 'أخضر': '#4caf50'}
        
        for _, row in df.iterrows():
            if row['المنطقة'] in WILAYA_COORDINATES:
                lat, lon = WILAYA_COORDINATES[row['المنطقة']]
                color = colors.get(row['فئة المخاطر'], '#89b4fa')
                size = 100 + row['مؤشر المخاطر المركب'] * 200
                ax.scatter(lon, lat, s=size, c=color, alpha=0.7, edgecolors='white')
                ax.annotate(row['المنطقة'], (lon, lat), color='white', fontsize=8, ha='center')
        
        ax.set_xlim(-2, 10)
        ax.set_ylim(18, 38)
        ax.set_title('خريطة المخاطر في الجزائر', color='white', fontsize=14)
        ax.tick_params(colors='white')
        ax.set_xlabel('خط الطول', color='white')
        ax.set_ylabel('خط العرض', color='white')
        
        layout.addWidget(canvas)
        return widget
    
    def update_dashboard(self):
        """تحديث لوحة التحكم"""
        self.status_label.setText("جاري التحديث...")
        self.risk_analyzer.calculate_portfolio_metrics()
        
        # إعادة بناء التبويبات
        current_tab = self.tabs.currentIndex()
        self.tabs.clear()
        self.tabs.addTab(self.create_dashboard_tab(), "📈 لوحة التحكم")
        self.tabs.addTab(self.create_portfolio_tab(), "💼 المحفظة")
        self.tabs.addTab(self.create_risk_tab(), "🤖 تصنيف المخاطر")
        self.tabs.addTab(self.create_simulation_tab(), "💰 محاكاة مونتي كارلو")
        self.tabs.addTab(self.create_map_tab(), "🗺️ الخريطة")
        self.tabs.setCurrentIndex(min(current_tab, 4))
        
        self.status_label.setText("تم التحديث")
    
    def export_report(self):
        """تصدير التقرير"""
        filename, _ = QFileDialog.getSaveFileName(self, "حفظ التقرير", "", "Text Files (*.txt)")
        if filename:
            report = self.risk_analyzer.generate_risk_report()
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            QMessageBox.information(self, "تم", "تم حفظ التقرير")


class TrainWorker(QObject):
    """عامل تدريب النموذج"""
    finished = pyqtSignal(dict)
    
    def __init__(self, classifier, policies, regions):
        super().__init__()
        self.classifier = classifier
        self.policies = policies
        self.regions = regions
    
    def run(self):
        result = self.classifier.train(self.policies, self.regions)
        self.finished.emit(result)