"""
نافذة تحسين المحفظة التأمينية
Portfolio Optimization Dialog
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QFont

from core.risk_models import RiskProfile, PortfolioSummary
from core.portfolio_optimizer import PortfolioOptimizer, OptimizationResult


class OptimizationWorker(QThread):
    """
    خيط عمل لتحسين المحفظة
    """
    
    progress_updated = pyqtSignal(int, str)
    optimization_completed = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, profiles, total_budget, use_pulp=True):
        super().__init__()
        self.profiles = profiles
        self.total_budget = total_budget
        self.use_pulp = use_pulp
        self._is_stopped = False
    
    def run(self):
        try:
            optimizer = PortfolioOptimizer()
            
            self.progress_updated.emit(20, "🔄 جاري بناء نموذج التحسين...")
            
            if self.use_pulp:
                result = optimizer.optimize_with_pulp(self.profiles, self.total_budget)
            else:
                result = optimizer.optimize_with_scipy(self.profiles, self.total_budget)
            
            if self._is_stopped:
                return
            
            self.progress_updated.emit(90, "📊 جاري تجهيز النتائج...")
            self.optimization_completed.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def stop(self):
        self._is_stopped = True


class OptimizationDialog(QDialog):
    """
    نافذة تحسين المحفظة
    """
    
    def __init__(self, profiles, summary, parent=None):
        super().__init__(parent)
        
        self.profiles = profiles
        self.summary = summary
        self.optimization_result = None
        self.worker = None
        
        self.setWindowTitle("🎯 تحسين المحفظة التأمينية - R.AI")
        self.setGeometry(200, 100, 1200, 800)
        self.setMinimumSize(1000, 700)
        
        self.init_ui()
        self.apply_styles()
    
    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # العنوان
        title_label = QLabel("🎯 تحسين المحفظة التأمينية - اختيار البوليصات المقترح تقويتها")
        title_label.setObjectName("dialogTitle")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # معلومات المحفظة
        info_frame = self.create_info_frame()
        layout.addWidget(info_frame)
        
        # إعدادات التحسين
        settings_frame = self.create_settings_frame()
        layout.addWidget(settings_frame)
        
        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # علامات تبويب النتائج
        self.result_tabs = QTabWidget()
        layout.addWidget(self.result_tabs)
        
        # تبويب الملخص
        self.summary_tab = QTextEdit()
        self.summary_tab.setReadOnly(True)
        self.summary_tab.setPlaceholderText("سيظهر هنا ملخص نتائج التحسين بعد التشغيل...")
        self.result_tabs.addTab(self.summary_tab, "📊 ملخص النتائج")
        
        # تبويب جدول البوليصات المقترحة
        self.table_tab = QWidget()
        self.init_table_tab()
        self.result_tabs.addTab(self.table_tab, "📋 البوليصات المقترحة")
        
        # تبويب تفاصيل الإنفاق
        self.spending_tab = QTextEdit()
        self.spending_tab.setReadOnly(True)
        self.spending_tab.setPlaceholderText("سيظهر هنا تفصيل الإنفاق حسب الولاية...")
        self.result_tabs.addTab(self.spending_tab, "💰 تفاصيل الإنفاق")
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        
        self.optimize_btn = QPushButton("🚀 بدء التحسين")
        self.optimize_btn.setObjectName("primaryButton")
        self.optimize_btn.clicked.connect(self.start_optimization)
        button_layout.addWidget(self.optimize_btn)
        
        self.stop_btn = QPushButton("⏹️ إيقاف")
        self.stop_btn.setObjectName("dangerButton")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_optimization)
        button_layout.addWidget(self.stop_btn)
        
        button_layout.addStretch()
        
        self.export_btn = QPushButton("📊 تصدير التقرير")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_report)
        button_layout.addWidget(self.export_btn)
        
        self.close_btn = QPushButton("❌ إغلاق")
        self.close_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def create_info_frame(self):
        """إنشاء إطار معلومات المحفظة"""
        frame = QGroupBox("📊 معلومات المحفظة الحالية")
        layout = QHBoxLayout(frame)
        
        info_text = f"""
        <b>عدد البوليصات:</b> {self.summary.total_policies:,}<br>
        <b>إجمالي رأس المال المؤمن:</b> {self.summary.total_sum_insured:,.0f} دج<br>
        <b>الخسارة المتوقعة:</b> {self.summary.expected_loss:,.0f} دج<br>
        <b>VaR 99%:</b> {self.summary.var_99:,.0f} دج<br>
        <b>البوليصات عالية المخاطر:</b> {self.summary.high_risk_count:,}
        """
        
        info_label = QLabel(info_text)
        info_label.setTextFormat(Qt.RichText)
        layout.addWidget(info_label)
        
        return frame
    
    def create_settings_frame(self):
        """إنشاء إطار إعدادات التحسين"""
        frame = QGroupBox("⚙️ إعدادات التحسين")
        layout = QGridLayout(frame)
        
        # ميزانية التقوية
        layout.addWidget(QLabel("💰 الميزانية المتاحة للتقوية (دج):"), 0, 0)
        self.budget_spin = QDoubleSpinBox()
        self.budget_spin.setRange(1_000_000, 10_000_000_000)
        self.budget_spin.setValue(min(100_000_000, self.summary.total_sum_insured * 0.05))
        self.budget_spin.setSingleStep(10_000_000)
        self.budget_spin.setSuffix(" دج")
        self.budget_spin.setLocale(self.budget_spin.locale())
        self.budget_spin.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.budget_spin, 0, 1)
        
        # اقتراح ميزانية
        suggest_btn = QPushButton("💡 اقتراح")
        suggest_btn.clicked.connect(self.suggest_budget)
        layout.addWidget(suggest_btn, 0, 2)
        
        # اختيار المحل
        layout.addWidget(QLabel("🔧 طريقة التحسين:"), 1, 0)
        self.method_combo = QComboBox()
        self.method_combo.addItems(["PuLP (حل صحيح - دقة عالية)", "SciPy (حل استرخائي - سرعة أكبر)"])
        self.method_combo.setCurrentIndex(0)
        layout.addWidget(self.method_combo, 1, 1, 1, 2)
        
        # قيد التركيز الجغرافي
        self.geo_constraint_check = QPushButton("⚙️ قيود التحسين")
        self.geo_constraint_check.setEnabled(False)
        geo_text = QLabel("✅ قيد التركيز الجغرافي مفعل (حد أقصى 30% لكل ولاية)")
        geo_text.setStyleSheet("color: #00ff66; font-size: 11px;")
        layout.addWidget(geo_text, 2, 0, 1, 3)
        
        return frame
    
    def init_table_tab(self):
        """تهيئة تبويب الجدول"""
        layout = QVBoxLayout(self.table_tab)
        
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(9)
        self.result_table.setHorizontalHeaderLabels([
            "الولاية", "البلدية", "رأس المال المؤمن", "درجة المخاطر",
            "المخاطر بعد التقوية", "تكلفة التقوية", "تخفيض الخسارة",
            "نوع المبنى", "المنطقة الزلزالية"
        ])
        
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.result_table)
    
    def suggest_budget(self):
        """اقتراح ميزانية مناسبة"""
        total_insured = self.summary.total_sum_insured
        suggested = total_insured * 0.03  # 3% من إجمالي رأس المال المؤمن
        suggested = min(suggested, total_insured * 0.1)
        suggested = max(suggested, 10_000_000)
        
        self.budget_spin.setValue(suggested)
        
        QMessageBox.information(
            self,
            "💡 اقتراح الميزانية",
            f"الميزانية المقترحة بناءً على حجم المحفظة:\n\n"
            f"• إجمالي رأس المال المؤمن: {total_insured:,.0f} دج\n"
            f"• النسبة المقترحة: 3%\n"
            f"• الميزانية المقترحة: {suggested:,.0f} دج\n\n"
            f"ملاحظة: يمكنك تعديل الميزانية حسب إمكانيات الشركة."
        )
    
    def start_optimization(self):
        """بدء عملية التحسين"""
        total_budget = self.budget_spin.value()
        
        if total_budget <= 0:
            QMessageBox.warning(self, "⚠️ تحذير", "الرجاء إدخال ميزانية صالحة")
            return
        
        # تأكيد للمستخدم
        reply = QMessageBox.question(
            self,
            "تأكيد التحسين",
            f"سيتم بدء تحسين المحفظة بالميزانية: {total_budget:,.0f} دج\n\n"
            f"عدد البوليصات المراد تحليلها: {len(self.profiles):,}\n"
            f"قد يستغرق التحليل عدة ثوانٍ حسب حجم البيانات.\n\n"
            f"هل تريد المتابعة؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # تعطيل الأزرار
        self.optimize_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.export_btn.setEnabled(False)
        
        # إظهار شريط التقدم
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # تفعيل علامات التبويب
        self.summary_tab.clear()
        self.spending_tab.clear()
        self.result_table.setRowCount(0)
        
        # عرض رسالة بدء التحسين
        self.summary_tab.setPlainText("🔄 جاري تحسين المحفظة...\n\n⏳ قد يستغرق التحليل بضع ثوانٍ حسب حجم البيانات.")
        
        # تشغيل خيط التحسين
        use_pulp = self.method_combo.currentIndex() == 0
        self.worker = OptimizationWorker(self.profiles, total_budget, use_pulp)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.optimization_completed.connect(self.on_optimization_completed)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()
    
    def stop_optimization(self):
        """إيقاف عملية التحسين"""
        if self.worker:
            self.worker.stop()
            self.worker.quit()
            self.worker.wait()
        
        self.progress_bar.setVisible(False)
        self.optimize_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.summary_tab.setPlainText("⏹️ تم إيقاف التحسين بناءً على طلب المستخدم.")
    
    def update_progress(self, value, message):
        """تحديث شريط التقدم"""
        self.progress_bar.setValue(value)
        self.summary_tab.setPlainText(f"🔄 {message}\n\n⏳ جاري العمل...")
    
    def on_optimization_completed(self, result):
        """عند اكتمال التحسين"""
        self.optimization_result = result
        self.progress_bar.setVisible(False)
        self.optimize_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        if result.solution_found:
            self.display_results(result)
            self.export_btn.setEnabled(True)
            self.result_tabs.setCurrentIndex(0)
        else:
            self.summary_tab.setPlainText(f"❌ فشل التحسين\n\n{result.optimization_status}")
            QMessageBox.warning(self, "⚠️ تحذير", f"لم يتم إيجاد حل أمثل:\n{result.optimization_status}")
    
    def on_error(self, error_message):
        """معالجة الأخطاء"""
        self.progress_bar.setVisible(False)
        self.optimize_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.summary_tab.setPlainText(f"❌ خطأ في التحسين\n\n{error_message}")
        QMessageBox.critical(self, "❌ خطأ", f"حدث خطأ أثناء التحسين:\n{error_message}")
    
    def display_results(self, result: OptimizationResult):
        """عرض نتائج التحسين"""
        optimizer = PortfolioOptimizer()
        
        # عرض الملخص
        summary_text = optimizer.get_optimization_summary(result)
        self.summary_tab.setPlainText(summary_text)
        
        # عرض تفاصيل الإنفاق حسب الولاية
        spending_text = "💰 تفاصيل الإنفاق حسب الولاية\n"
        spending_text += "═" * 50 + "\n\n"
        
        if result.wilaya_spending:
            for wilaya, spend in sorted(result.wilaya_spending.items(), key=lambda x: x[1], reverse=True):
                count = result.wilaya_retrofit_counts.get(wilaya, 0)
                percentage = (spend / result.total_budget * 100) if result.total_budget > 0 else 0
                spending_text += f"📍 {wilaya}\n"
                spending_text += f"   • الإنفاق: {spend:,.0f} دج ({percentage:.1f}%)\n"
                spending_text += f"   • عدد البوليصات: {count}\n\n"
        else:
            spending_text += "لا توجد بيانات كافية لعرض الإنفاق حسب الولاية.\n"
        
        self.spending_tab.setPlainText(spending_text)
        
        # عرض جدول البوليصات المقترحة
        self.display_retrofit_table(result)
    
    def display_retrofit_table(self, result: OptimizationResult):
        """عرض جدول البوليصات المقترحة"""
        optimizer = PortfolioOptimizer()
        
        self.result_table.setRowCount(len(result.selected_profiles))
        
        for i, profile in enumerate(result.selected_profiles):
            # الولاية
            self.result_table.setItem(i, 0, QTableWidgetItem(profile.wilaya_name))
            
            # البلدية
            self.result_table.setItem(i, 1, QTableWidgetItem(profile.commune_name))
            
            # رأس المال المؤمن
            capital_item = QTableWidgetItem(f"{profile.sum_insured:,.0f}")
            capital_item.setTextAlignment(Qt.AlignRight)
            self.result_table.setItem(i, 2, capital_item)
            
            # درجة المخاطر الأصلية
            risk_item = QTableWidgetItem(f"{profile.risk_score:.3f}")
            if profile.risk_score >= 0.65:
                risk_item.setForeground(QColor('#ff3333'))
            elif profile.risk_score >= 0.35:
                risk_item.setForeground(QColor('#ffcc00'))
            else:
                risk_item.setForeground(QColor('#00ff66'))
            self.result_table.setItem(i, 3, risk_item)
            
            # درجة المخاطر بعد التقوية
            new_score = max(0.05, (profile.risk_score or 0.5) * 0.6)
            new_risk_item = QTableWidgetItem(f"{new_score:.3f}")
            if new_score >= 0.65:
                new_risk_item.setForeground(QColor('#ff3333'))
            elif new_score >= 0.35:
                new_risk_item.setForeground(QColor('#ffcc00'))
            else:
                new_risk_item.setForeground(QColor('#00ff66'))
            self.result_table.setItem(i, 4, new_risk_item)
            
            # تكلفة التقوية
            cost = profile.sum_insured * optimizer.RETROFIT_COST_RATIO
            cost_item = QTableWidgetItem(f"{cost:,.0f}")
            cost_item.setTextAlignment(Qt.AlignRight)
            self.result_table.setItem(i, 5, cost_item)
            
            # تخفيض الخسارة
            loss_reduction = (profile.risk_score or 0.5) * 0.4 * profile.sum_insured * optimizer.RETROFIT_RISK_REDUCTION
            reduction_item = QTableWidgetItem(f"{loss_reduction:,.0f}")
            reduction_item.setTextAlignment(Qt.AlignRight)
            reduction_item.setForeground(QColor('#00ff66'))
            self.result_table.setItem(i, 6, reduction_item)
            
            # نوع المبنى
            self.result_table.setItem(i, 7, QTableWidgetItem(
                profile.structure_type.value if profile.structure_type else "-"
            ))
            
            # المنطقة الزلزالية
            self.result_table.setItem(i, 8, QTableWidgetItem(
                profile.seismic_zone.name if profile.seismic_zone else "-"
            ))
    
    def export_report(self):
        """تصدير تقرير التحسين"""
        if not self.optimization_result:
            QMessageBox.warning(self, "⚠️ تحذير", "لا توجد نتائج لتصديرها")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "حفظ تقرير التحسين",
            "optimization_report.xlsx",
            "Excel Files (*.xlsx)"
        )
        
        if not file_path:
            return
        
        optimizer = PortfolioOptimizer()
        success = optimizer.export_optimization_report(
            self.optimization_result,
            self.profiles,
            file_path
        )
        
        if success:
            QMessageBox.information(
                self,
                "✅ تم التصدير",
                f"تم حفظ تقرير التحسين في:\n{file_path}"
            )
        else:
            QMessageBox.critical(
                self,
                "❌ خطأ",
                "فشل تصدير التقرير. تأكد من أن لديك صلاحيات الكتابة."
            )
    
    def apply_styles(self):
        """تطبيق الأنماط"""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #0a0e27, stop: 1 #1a1f3a);
            }
            
            QLabel#dialogTitle {
                font-size: 22px;
                font-weight: bold;
                color: #00ffff;
                padding: 15px;
            }
            
            QGroupBox {
                color: #00ffff;
                font-weight: bold;
                font-size: 14px;
                border: 1px solid rgba(0, 255, 255, 0.3);
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 15px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
            }
            
            QPushButton {
                background: #2a4a6a;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background: #3a5a7a;
            }
            
            QPushButton#primaryButton {
                background: #0080ff;
            }
            
            QPushButton#primaryButton:hover {
                background: #2090ff;
            }
            
            QPushButton#dangerButton {
                background: #cc0000;
            }
            
            QPushButton#dangerButton:hover {
                background: #dd1111;
            }
            
            QTableWidget {
                background: rgba(20, 25, 50, 0.8);
                color: #c0d0f0;
                border: 1px solid rgba(0, 255, 255, 0.2);
                border-radius: 8px;
                gridline-color: rgba(0, 255, 255, 0.1);
            }
            
            QTableWidget::item:selected {
                background: rgba(0, 255, 255, 0.2);
            }
            
            QHeaderView::section {
                background: #2a3a6a;
                color: #00ffff;
                padding: 8px;
                font-weight: bold;
            }
            
            QTextEdit {
                background: rgba(20, 25, 50, 0.8);
                color: #c0d0f0;
                border: 1px solid rgba(0, 255, 255, 0.2);
                border-radius: 8px;
                font-family: monospace;
                font-size: 12px;
            }
            
            QDoubleSpinBox, QComboBox {
                background: rgba(30, 35, 60, 0.9);
                color: white;
                border: 1px solid rgba(0, 255, 255, 0.3);
                border-radius: 6px;
                padding: 5px;
                font-size: 13px;
            }
            
            QProgressBar {
                background: rgba(20, 25, 50, 0.8);
                border: 1px solid rgba(0, 255, 255, 0.3);
                border-radius: 8px;
                text-align: center;
                color: white;
                height: 25px;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #00bfff, stop: 1 #00ffff);
                border-radius: 7px;
            }
        """)