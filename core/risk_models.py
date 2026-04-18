"""
نماذج المخاطر وهياكل البيانات (نسخة محسنة)
Risk Models and Data Structures (Optimized Version)
"""

from dataclasses import dataclass, field
from enum import IntEnum, Enum
from typing import List, Optional, Dict, Any
import numpy as np


class SeismicZone(IntEnum):
    """مناطق الزلازل حسب RPA 99"""
    ZONE_0 = 0
    ZONE_I = 1
    ZONE_IIa = 2
    ZONE_IIb = 3
    ZONE_III = 4


class BuildingType(IntEnum):
    """أنواع المباني حسب تصنيف RPA 99"""
    TYPE_1A = 1
    TYPE_1B = 2
    TYPE_2 = 3
    TYPE_3 = 4


class RiskLevel(IntEnum):
    """مستويات المخاطر"""
    LOW = 0
    MEDIUM = 1
    HIGH = 2


class StructureType(Enum):
    """أنواع الهياكل الإنشائية"""
    RC_FRAME = "إطار خرساني مسلح"
    RC_SHEAR_WALL = "جدران قص خرسانية"
    STEEL_FRAME = "إطار فولاذي"
    MASONRY = "مباني حجرية/طوب"
    MIXED = "نظام مختلط"


@dataclass
class RiskProfile:
    """
    ملف المخاطر - يحتوي على جميع المعلومات اللازمة لتقييم المخاطر
    """
    wilaya_code: int = 16
    wilaya_name: str = "الجزائر"
    commune_name: str = "غير محدد"
    building_age: int = 15
    number_of_floors: int = 2
    structure_type: Optional[StructureType] = None
    building_type: Optional[BuildingType] = None
    sum_insured: float = 0.0
    construction_year: Optional[int] = None
    soil_type: str = "S2"
    
    seismic_zone: Optional[SeismicZone] = None
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.MEDIUM
    premium_rate: float = 0.0
    
    def __post_init__(self):
        """حساب القيم المشتقة بعد إنشاء الكائن"""
        if self.wilaya_code is None:
            self.wilaya_code = 16
        if self.wilaya_name is None:
            self.wilaya_name = "الجزائر"
        if self.commune_name is None:
            self.commune_name = "غير محدد"
        if self.building_age is None or self.building_age <= 0:
            self.building_age = 15
        if self.number_of_floors is None or self.number_of_floors <= 0:
            self.number_of_floors = 2
        if self.structure_type is None:
            self.structure_type = StructureType.RC_FRAME
        if self.building_type is None:
            self.building_type = BuildingType.TYPE_2
        if self.soil_type is None:
            self.soil_type = "S2"
        if self.construction_year is None:
            self.construction_year = 2024 - self.building_age
        if self.risk_level is None:
            self.risk_level = RiskLevel.MEDIUM
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل الكائن إلى قاموس"""
        return {
            'wilaya_code': self.wilaya_code,
            'wilaya_name': self.wilaya_name,
            'commune_name': self.commune_name,
            'building_age': self.building_age,
            'number_of_floors': self.number_of_floors,
            'structure_type': self.structure_type.value if self.structure_type else "RC_FRAME",
            'building_type': self.building_type.value if self.building_type else 2,
            'sum_insured': self.sum_insured,
            'seismic_zone': self.seismic_zone.name if self.seismic_zone else "ZONE_I",
            'risk_score': self.risk_score,
            'risk_level': self.risk_level.value if self.risk_level else 1,
            'premium_rate': self.premium_rate
        }


@dataclass
class PortfolioSummary:
    """
    ملخص المحفظة التأمينية
    """
    total_policies: int = 0
    total_sum_insured: float = 0.0
    total_premium: float = 0.0
    
    low_risk_count: int = 0
    medium_risk_count: int = 0
    high_risk_count: int = 0
    
    var_95: float = 0.0
    var_99: float = 0.0
    tvar_95: float = 0.0
    expected_loss: float = 0.0
    max_probable_loss: float = 0.0
    
    wilaya_exposure: Dict[str, float] = field(default_factory=dict)
    loss_samples: np.ndarray = field(default_factory=lambda: np.array([]))
    
    def calculate_average_risk(self) -> float:
        """حساب متوسط درجة المخاطر"""
        total = self.low_risk_count + self.medium_risk_count + self.high_risk_count
        if total == 0:
            return 0.0
        weighted_sum = (self.low_risk_count * 0.2 + 
                       self.medium_risk_count * 0.5 + 
                       self.high_risk_count * 0.8)
        return weighted_sum / total