"""
رسوم Matplotlib البيانية لتحليل المخاطر (نسخة محسنة)
Matplotlib Charts for Risk Analytics (Optimized)
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
from typing import List, Dict

from core.risk_models import RiskProfile, PortfolioSummary, RiskLevel


class RiskCharts:
    """
    منشئ الرسوم البيانية للمخاطر
    """
    
    COLORS = {
        'background': '#1a1f3a',
        'grid': '#2a2f4a',
        'text': '#c0d0f0',
        'title': '#00ffff',
        'low_risk': '#00ff66',
        'medium_risk': '#ffcc00',
        'high_risk': '#ff3333',
        'bar': '#3a6a9a',
    }
    
    @classmethod
    def create_risk_distribution_chart(cls, profiles: List[RiskProfile]) -> FigureCanvas:
        """إنشاء رسم توزيع المخاطر"""
        fig = Figure(figsize=(10, 6), facecolor=cls.COLORS['background'])
        ax = fig.add_subplot(111)
        ax.set_facecolor(cls.COLORS['background'])
        
        # جمع البيانات مع معالجة None
        risk_scores = []
        for p in profiles:
            try:
                score = p.risk_score if p.risk_score is not None else 0.5
                risk_scores.append(score)
            except:
                risk_scores.append(0.5)
        
        if not risk_scores:
            risk_scores = [0.5]
        
        # رسم الهيستوغرام
        n, bins, patches = ax.hist(
            risk_scores,
            bins=30,
            alpha=0.8,
            color=cls.COLORS['bar'],
            edgecolor='white',
            linewidth=0.5
        )
        
        # تلوين الأعمدة
        for i, patch in enumerate(patches):
            if i < len(bins) - 1:
                bin_center = (bins[i] + bins[i + 1]) / 2
                if bin_center < 0.35:
                    patch.set_facecolor(cls.COLORS['low_risk'])
                elif bin_center < 0.65:
                    patch.set_facecolor(cls.COLORS['medium_risk'])
                else:
                    patch.set_facecolor(cls.COLORS['high_risk'])
        
        ax.set_xlabel('درجة المخاطر', color=cls.COLORS['text'], fontsize=12, fontweight='bold')
        ax.set_ylabel('عدد البوليصات', color=cls.COLORS['text'], fontsize=12, fontweight='bold')
        ax.set_title('توزيع درجات المخاطر', color=cls.COLORS['title'], fontsize=14, fontweight='bold')
        
        ax.axvline(x=0.35, color='yellow', linestyle='--', alpha=0.7, linewidth=2)
        ax.axvline(x=0.65, color='red', linestyle='--', alpha=0.7, linewidth=2)
        
        ax.tick_params(colors=cls.COLORS['text'])
        for spine in ax.spines.values():
            spine.set_color(cls.COLORS['grid'])
        ax.grid(True, alpha=0.2, color=cls.COLORS['grid'])
        
        fig.tight_layout()
        return FigureCanvas(fig)
    
    @classmethod
    def create_pie_chart(cls, summary: PortfolioSummary) -> FigureCanvas:
        """إنشاء رسم دائري"""
        fig = Figure(figsize=(8, 6), facecolor=cls.COLORS['background'])
        ax = fig.add_subplot(111)
        
        labels = ['خطر منخفض', 'خطر متوسط', 'خطر مرتفع']
        sizes = [
            summary.low_risk_count if summary.low_risk_count is not None else 0,
            summary.medium_risk_count if summary.medium_risk_count is not None else 0,
            summary.high_risk_count if summary.high_risk_count is not None else 0
        ]
        colors = [cls.COLORS['low_risk'], cls.COLORS['medium_risk'], cls.COLORS['high_risk']]
        
        # إزالة القيم الصفرية
        non_zero_labels = []
        non_zero_sizes = []
        non_zero_colors = []
        for i, size in enumerate(sizes):
            if size > 0:
                non_zero_labels.append(labels[i])
                non_zero_sizes.append(size)
                non_zero_colors.append(colors[i])
        
        if non_zero_sizes:
            wedges, texts, autotexts = ax.pie(
                non_zero_sizes,
                labels=non_zero_labels,
                colors=non_zero_colors,
                autopct='%1.1f%%',
                startangle=90,
                textprops={'color': cls.COLORS['text'], 'fontsize': 11, 'fontweight': 'bold'}
            )
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
        
        ax.set_title('توزيع مستويات المخاطر', color=cls.COLORS['title'], fontsize=14, fontweight='bold', pad=20)
        fig.tight_layout()
        
        return FigureCanvas(fig)
    
    @classmethod
    def create_loss_distribution_chart(cls, loss_samples: np.ndarray, var_95: float, var_99: float) -> FigureCanvas:
        """إنشاء رسم توزيع الخسائر"""
        fig = Figure(figsize=(10, 6), facecolor=cls.COLORS['background'])
        ax = fig.add_subplot(111)
        ax.set_facecolor(cls.COLORS['background'])
        
        if loss_samples is not None and len(loss_samples) > 0:
            n, bins, patches = ax.hist(
                loss_samples,
                bins=50,
                alpha=0.7,
                color=cls.COLORS['bar'],
                edgecolor='white',
                linewidth=0.3,
                density=True
            )
            
            if var_95 is not None and var_95 > 0:
                ax.axvline(x=var_95, color='orange', linestyle='--', alpha=0.8, linewidth=2)
                y_max = ax.get_ylim()[1]
                ax.text(var_95, y_max * 0.85, f'VaR 95%: {var_95:,.0f} دج', 
                       color='orange', ha='right', fontweight='bold')
            
            if var_99 is not None and var_99 > 0:
                ax.axvline(x=var_99, color='red', linestyle='--', alpha=0.8, linewidth=2)
        
        ax.set_xlabel('الخسارة (دج)', color=cls.COLORS['text'], fontsize=12, fontweight='bold')
        ax.set_ylabel('الكثافة الاحتمالية', color=cls.COLORS['text'], fontsize=12, fontweight='bold')
        ax.set_title('توزيع الخسائر - محاكاة مونت كارلو', color=cls.COLORS['title'], fontsize=14, fontweight='bold')
        
        ax.tick_params(colors=cls.COLORS['text'])
        for spine in ax.spines.values():
            spine.set_color(cls.COLORS['grid'])
        ax.grid(True, alpha=0.2, color=cls.COLORS['grid'])
        
        fig.tight_layout()
        return FigureCanvas(fig)
    
    @classmethod
    def create_wilaya_exposure_chart(cls, wilaya_exposure: Dict[str, float]) -> FigureCanvas:
        """إنشاء رسم التعرض حسب الولاية"""
        fig = Figure(figsize=(12, 6), facecolor=cls.COLORS['background'])
        ax = fig.add_subplot(111)
        ax.set_facecolor(cls.COLORS['background'])
        
        if wilaya_exposure:
            sorted_data = sorted(wilaya_exposure.items(), key=lambda x: x[1], reverse=True)[:10]
            
            names = [item[0] for item in sorted_data]
            values = [item[1] for item in sorted_data]
            
            bars = ax.barh(range(len(names)), values, color=cls.COLORS['bar'], alpha=0.8)
            
            for i, (name, value) in enumerate(zip(names, values)):
                ax.text(value, i, f' {value:,.0f} دج', va='center', color=cls.COLORS['text'], fontweight='bold')
            
            ax.set_yticks(range(len(names)))
            ax.set_yticklabels(names)
        
        ax.set_xlabel('إجمالي رأس المال المؤمن (دج)', color=cls.COLORS['text'], fontsize=12, fontweight='bold')
        ax.set_ylabel('الولاية', color=cls.COLORS['text'], fontsize=12, fontweight='bold')
        ax.set_title('أعلى 10 ولايات من حيث التعرض التأميني', color=cls.COLORS['title'], fontsize=14, fontweight='bold')
        
        ax.tick_params(colors=cls.COLORS['text'])
        for spine in ax.spines.values():
            spine.set_color(cls.COLORS['grid'])
        ax.grid(True, alpha=0.2, color=cls.COLORS['grid'], axis='x')
        
        fig.tight_layout()
        return FigureCanvas(fig)