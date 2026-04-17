"""
نماذج البيانات للنظام - Smart Insurance Risk Management
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np
import pandas as pd

@dataclass
class InsurancePolicy:
    """نموذج بوليصة التأمين"""
    policy_id: str
    wilaya: str
    insured_value: float
    premium: float
    building_type: str = "Standard"
    construction_year: int = 2015
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    number_of_floors: int = 1
    start_date: datetime = field(default_factory=datetime.now)
    end_date: datetime = field(default_factory=datetime.now)
    year: int = 2023  # سنة البوليصة
    
    def calculate_age(self) -> int:
        """حساب عمر المبنى"""
        return datetime.now().year - self.construction_year

@dataclass
class RegionRisk:
    """نموذج مخاطر المنطقة (الولاية)"""
    wilaya_name: str
    wilaya_code: int
    seismic_zone: str
    base_risk_score: float
    total_insured_value: float = 0.0
    policy_count: int = 0
    premium_volume: float = 0.0
    historical_earthquakes: int = 0
    adjusted_risk_score: float = 0.0
    
    def calculate_concentration(self, total_portfolio: float) -> float:
        """حساب نسبة التركيز المالي في هذه الولاية"""
        if total_portfolio > 0:
            return (self.total_insured_value / total_portfolio) * 100
        return 0.0
    
    def get_risk_category(self) -> str:
        """تحديد فئة المخاطر بناءً على الكود الجزائري RPA"""
        if self.adjusted_risk_score >= 0.7:
            return "أحمر"
        elif self.adjusted_risk_score >= 0.4:
            return "برتقالي"
        return "أخضر"

@dataclass
class PortfolioSummary:
    """ملخص شامل للمحفظة التأمينية"""
    total_policies: int = 0
    total_insured_value: float = 0.0
    total_premium: float = 0.0
    average_risk_score: float = 0.0
    regions_count: int = 0
    high_risk_exposure: float = 0.0
    medium_risk_exposure: float = 0.0
    low_risk_exposure: float = 0.0
    
    def to_dataframe(self) -> pd.DataFrame:
        """تحويل الملخص إلى جدول لعرضه في الواجهة"""
        return pd.DataFrame([{
            'إجمالي الوثائق': f"{self.total_policies:,}",
            'إجمالي القيمة المؤمنة': f"{self.total_insured_value:,.2f} دج",
            'إجمالي الأقساط': f"{self.total_premium:,.2f} دج",
            'متوسط درجة الخطورة': f"{self.average_risk_score:.2f}",
            'عدد الولايات النشطة': self.regions_count
        }])

@dataclass
class SimulationResult:
    """نتائج محاكاة مونتي كارلو للخسائر المتوقعة"""
    simulation_id: str
    timestamp: datetime
    region_name: str
    portfolio_value: float
    n_simulations: int
    mean_loss: float = 0.0
    std_loss: float = 0.0
    var_95: float = 0.0
    var_99: float = 0.0
    tvar_99: float = 0.0
    max_loss: float = 0.0
    company_retention_ratio: float = 0.30
    mean_company_loss: float = 0.0
    var_99_company: float = 0.0
    max_company_loss: float = 0.0
    loss_distribution: np.ndarray = field(default_factory=lambda: np.array([]))
    
    def calculate_probability_of_ruin(self, capital: float) -> float:
        """حساب احتمالية أن تتجاوز الخسائر رأس المال المتوفر"""
        if len(self.loss_distribution) > 0:
            return np.mean(self.loss_distribution > capital)
        return 0.0

    def get_summary_dict(self) -> Dict:
        """تنسيق النتائج للعرض في جداول الواجهة"""
        return {
            'متوسط الخسارة المتوقعة': f"{self.mean_loss:,.0f} دج",
            'أقصى خسارة محتملة (VaR 99%)': f"{self.var_99:,.0f} دج",
            'حصة الشركة من الخسارة': f"{self.mean_company_loss:,.0f} دج",
            'الحالة': 'خطرة' if self.var_99 > (self.portfolio_value * 0.1) else 'آمنة'
        }