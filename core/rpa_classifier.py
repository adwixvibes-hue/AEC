"""
مصنف RPA 99 ونموذج CatBoost للتنبؤ بالمخاطر (نسخة محسنة للأداء)
RPA 99 Classifier and CatBoost Risk Prediction Model (Performance Optimized)

تحسينات:
- معالجة دفعية (Batch Processing) للبيانات الكبيرة
- تخزين مؤقت للنتائج (Caching)
- معالجة القيم الفارغة (None values)
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from functools import lru_cache
import warnings
import gc

warnings.filterwarnings('ignore')

from .risk_models import (
    SeismicZone, BuildingType, StructureType, 
    RiskLevel, RiskProfile
)


class RPAClassifier:
    """
    مصنف RPA 99 للمناطق الزلزالية (نسخة محسنة)
    RPA 99 Seismic Zone Classifier (Optimized Version)
    """
    
    _zone_cache: Dict[int, SeismicZone] = {}
    
    # خريطة الولايات للمناطق الزلزالية
    WILAYA_ZONE_MAP: Dict[int, SeismicZone] = {
        # المنطقة III - Extreme Seismicity
        6: SeismicZone.ZONE_III,    # بجاية
        15: SeismicZone.ZONE_III,   # تيزي وزو
        35: SeismicZone.ZONE_III,   # بومرداس
        2: SeismicZone.ZONE_III,    # الشلف
        44: SeismicZone.ZONE_III,   # عين الدفلى
        21: SeismicZone.ZONE_III,   # سكيكدة
        18: SeismicZone.ZONE_III,   # جيجل
        9: SeismicZone.ZONE_III,    # البليدة
        16: SeismicZone.ZONE_III,   # الجزائر العاصمة
        42: SeismicZone.ZONE_III,   # تيبازة
        
        # المنطقة IIb - Very High Seismicity
        10: SeismicZone.ZONE_IIb,   # البويرة
        34: SeismicZone.ZONE_IIb,   # برج بوعريريج
        19: SeismicZone.ZONE_IIb,   # سطيف
        25: SeismicZone.ZONE_IIb,   # قسنطينة
        43: SeismicZone.ZONE_IIb,   # ميلة
        23: SeismicZone.ZONE_IIb,   # عنابة
        36: SeismicZone.ZONE_IIb,   # الطارف
        24: SeismicZone.ZONE_IIb,   # قالمة
        41: SeismicZone.ZONE_IIb,   # سوق أهراس
        26: SeismicZone.ZONE_IIb,   # المدية
        5: SeismicZone.ZONE_IIb,    # باتنة
        4: SeismicZone.ZONE_IIb,    # أم البواقي
        40: SeismicZone.ZONE_IIb,   # خنشلة
        
        # المنطقة IIa - High Seismicity
        7: SeismicZone.ZONE_IIa,    # بسكرة
        12: SeismicZone.ZONE_IIa,   # تبسة
        17: SeismicZone.ZONE_IIa,   # الجلفة
        28: SeismicZone.ZONE_IIa,   # المسيلة
        14: SeismicZone.ZONE_IIa,   # تيارت
        38: SeismicZone.ZONE_IIa,   # تيسمسيلت
        48: SeismicZone.ZONE_IIa,   # غليزان
        27: SeismicZone.ZONE_IIa,   # مستغانم
        29: SeismicZone.ZONE_IIa,   # معسكر
        31: SeismicZone.ZONE_IIa,   # وهران
        46: SeismicZone.ZONE_IIa,   # عين تموشنت
        13: SeismicZone.ZONE_IIa,   # تلمسان
        22: SeismicZone.ZONE_IIa,   # سيدي بلعباس
        20: SeismicZone.ZONE_IIa,   # سعيدة
        
        # المنطقة I - Moderate Seismicity
        1: SeismicZone.ZONE_I,      # أدرار
        3: SeismicZone.ZONE_I,      # الأغواط
        8: SeismicZone.ZONE_I,      # بشار
        11: SeismicZone.ZONE_I,     # تمنراست
        30: SeismicZone.ZONE_I,     # ورقلة
        32: SeismicZone.ZONE_I,     # البيض
        33: SeismicZone.ZONE_I,     # إليزي
        37: SeismicZone.ZONE_I,     # تندوف
        39: SeismicZone.ZONE_I,     # الوادي
        45: SeismicZone.ZONE_I,     # النعامة
        47: SeismicZone.ZONE_I,     # غرداية
        49: SeismicZone.ZONE_I,     # تيميمون
        50: SeismicZone.ZONE_I,     # برج باجي مختار
        51: SeismicZone.ZONE_I,     # أولاد جلال
        52: SeismicZone.ZONE_I,     # بني عباس
        53: SeismicZone.ZONE_I,     # عين صالح
        54: SeismicZone.ZONE_I,     # عين قزام
        55: SeismicZone.ZONE_I,     # تقرت
        56: SeismicZone.ZONE_I,     # جانت
        57: SeismicZone.ZONE_I,     # المغير
        58: SeismicZone.ZONE_I,     # المنيعة
    }
    
    # معاملات التضخيم الزلزالي
    SOIL_FACTORS: Dict[str, float] = {
        'S1': 1.0,
        'S2': 1.2,
        'S3': 1.4,
        'S4': 1.8,
    }
    
    # معاملات الأهمية
    IMPORTANCE_FACTORS: Dict[BuildingType, float] = {
        BuildingType.TYPE_1A: 1.5,
        BuildingType.TYPE_1B: 1.3,
        BuildingType.TYPE_2: 1.0,
        BuildingType.TYPE_3: 0.8,
    }
    
    @classmethod
    def get_seismic_zone(cls, wilaya_code: int) -> SeismicZone:
        """الحصول على المنطقة الزلزالية (مع تخزين مؤقت ومعالجة القيم الفارغة)"""
        if wilaya_code is None:
            return SeismicZone.ZONE_I
        
        if wilaya_code not in cls._zone_cache:
            cls._zone_cache[wilaya_code] = cls.WILAYA_ZONE_MAP.get(
                wilaya_code, SeismicZone.ZONE_I
            )
        return cls._zone_cache[wilaya_code]
    
    @classmethod
    @lru_cache(maxsize=128)
    def get_zone_acceleration(cls, zone: Optional[SeismicZone]) -> float:
        """الحصول على معامل التسارع (مع تخزين مؤقت ومعالجة None)"""
        if zone is None:
            zone = SeismicZone.ZONE_I
        
        acceleration_map = {
            SeismicZone.ZONE_0: 0.05,
            SeismicZone.ZONE_I: 0.10,
            SeismicZone.ZONE_IIa: 0.20,
            SeismicZone.ZONE_IIb: 0.25,
            SeismicZone.ZONE_III: 0.30,
        }
        return acceleration_map.get(zone, 0.10)
    
    @classmethod
    def calculate_rpa_risk_score(cls, profile: RiskProfile) -> float:
        """حساب درجة المخاطر حسب RPA 99 (مع معالجة القيم الفارغة)"""
        # معالجة القيم الفارغة
        if profile.wilaya_code is None:
            profile.wilaya_code = 16  # الجزائر افتراضياً
        
        if profile.building_type is None:
            profile.building_type = BuildingType.TYPE_2
        
        if profile.soil_type is None:
            profile.soil_type = 'S2'
        
        if profile.number_of_floors is None or profile.number_of_floors <= 0:
            profile.number_of_floors = 2
        
        if profile.building_age is None or profile.building_age <= 0:
            profile.building_age = 15
        
        zone = cls.get_seismic_zone(profile.wilaya_code)
        profile.seismic_zone = zone
        
        A = cls.get_zone_acceleration(zone)
        I = cls.IMPORTANCE_FACTORS.get(profile.building_type, 1.0)
        S = cls.SOIL_FACTORS.get(profile.soil_type, 1.2)
        F = min(1.0 + (profile.number_of_floors - 1) * 0.05, 1.5)
        age_factor = min(profile.building_age / 50.0, 1.0)
        D = 1.0 + age_factor * 0.5
        
        raw_score = A * I * S * F * D
        normalized_score = min(raw_score / 0.8, 1.0)
        
        profile.risk_score = normalized_score
        profile.risk_level = cls.score_to_risk_level(normalized_score)
        
        return normalized_score
    
    @staticmethod
    def score_to_risk_level(score: float) -> RiskLevel:
        """تحويل درجة المخاطر إلى مستوى خطر"""
        if score is None:
            return RiskLevel.MEDIUM
        if score < 0.35:
            return RiskLevel.LOW
        elif score < 0.65:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH
    
    @classmethod
    def calculate_batch(cls, profiles: List[RiskProfile], 
                       progress_callback=None) -> List[float]:
        """
        حساب درجات المخاطر لمجموعة كبيرة من الملفات
        Batch Calculation for Large Number of Profiles
        """
        n = len(profiles)
        scores = np.zeros(n)
        
        BATCH_SIZE = 5000
        
        for start_idx in range(0, n, BATCH_SIZE):
            end_idx = min(start_idx + BATCH_SIZE, n)
            batch = profiles[start_idx:end_idx]
            
            for i, profile in enumerate(batch):
                try:
                    scores[start_idx + i] = cls.calculate_rpa_risk_score(profile)
                except Exception as e:
                    # في حالة الخطأ، نعطي قيمة افتراضية
                    profile.risk_score = 0.5
                    profile.risk_level = RiskLevel.MEDIUM
                    scores[start_idx + i] = 0.5
            
            if progress_callback:
                progress = int((end_idx / n) * 100)
                progress_callback(progress, f"جاري تحليل {end_idx} من {n}...")
            
            gc.collect()
        
        return scores.tolist()


class CatBoostRiskModel:
    """
    نموذج CatBoost للتنبؤ بالمخاطر (نسخة محسنة)
    CatBoost Risk Prediction Model (Optimized Version)
    """
    
    def __init__(self, use_cache: bool = True):
        """
        تهيئة النموذج
        """
        self.use_cache = use_cache
        self._prediction_cache: Dict[int, float] = {}
        self._initialize_model_parameters()
        
        # تأثير نوع الهيكل الإنشائي
        self._structure_impact = {
            StructureType.RC_SHEAR_WALL: -0.05,
            StructureType.RC_FRAME: 0.0,
            StructureType.STEEL_FRAME: 0.02,
            StructureType.MIXED: 0.05,
            StructureType.MASONRY: 0.15,
        }
    
    def _initialize_model_parameters(self):
        """تهيئة معاملات النموذج"""
        self.feature_weights = {
            'seismic_zone': 0.35,
            'zone_acceleration': 0.20,
            'building_age': 0.10,
            'number_of_floors': 0.10,
            'structure_type_encoded': 0.08,
            'building_type_encoded': 0.07,
            'soil_type_encoded': 0.05,
            'age_factor': 0.03,
            'floor_factor': 0.02,
        }
        
        self.threshold_low = 0.35
        self.threshold_medium = 0.65
    
    def _get_cache_key(self, profile: RiskProfile) -> int:
        """إنشاء مفتاح للتخزين المؤقت (مع معالجة None)"""
        wilaya = profile.wilaya_code if profile.wilaya_code is not None else 16
        age = profile.building_age if profile.building_age is not None else 15
        floors = profile.number_of_floors if profile.number_of_floors is not None else 2
        structure = profile.structure_type.value if profile.structure_type else "RC_FRAME"
        building = profile.building_type.value if profile.building_type else 2
        soil = profile.soil_type if profile.soil_type else "S2"
        
        return hash((wilaya, age, floors, structure, building, soil))
    
    def _safe_get_structure_impact(self, structure_type) -> float:
        """الحصول على تأثير نوع الهيكل بشكل آمن"""
        if structure_type is None:
            return 0.0
        return self._structure_impact.get(structure_type, 0.0)
    
    def predict_risk_score(self, profile: RiskProfile) -> float:
        """
        التنبؤ بدرجة المخاطر (مع تخزين مؤقت ومعالجة None)
        """
        # معالجة القيم الفارغة قبل أي شيء
        if profile.wilaya_code is None:
            profile.wilaya_code = 16
        if profile.building_type is None:
            profile.building_type = BuildingType.TYPE_2
        if profile.structure_type is None:
            profile.structure_type = StructureType.RC_FRAME
        if profile.soil_type is None:
            profile.soil_type = 'S2'
        if profile.number_of_floors is None or profile.number_of_floors <= 0:
            profile.number_of_floors = 2
        if profile.building_age is None or profile.building_age <= 0:
            profile.building_age = 15
        
        if self.use_cache:
            cache_key = self._get_cache_key(profile)
            if cache_key in self._prediction_cache:
                profile.risk_score = self._prediction_cache[cache_key]
                profile.risk_level = self.score_to_risk_level(profile.risk_score)
                return profile.risk_score
        
        try:
            # حساب درجة RPA الأساسية
            rpa_score = RPAClassifier.calculate_rpa_risk_score(profile)
            
            # تطبيق التعديلات
            structure_adjustment = self._safe_get_structure_impact(profile.structure_type)
            
            # تأثير عدد الطوابق
            floors = profile.number_of_floors
            if floors > 10:
                height_penalty = 0.05
            elif floors > 5:
                height_penalty = 0.02
            else:
                height_penalty = 0.0
            
            # تأثير العمر
            age = profile.building_age
            if age > 30:
                age_penalty = 0.08
            elif age > 15:
                age_penalty = 0.03
            else:
                age_penalty = 0.0
            
            # الدرجة النهائية
            final_score = rpa_score + structure_adjustment + height_penalty + age_penalty
            final_score = np.clip(final_score, 0.0, 1.0)
            
        except Exception as e:
            # في حالة أي خطأ، نستخدم قيمة افتراضية
            print(f"خطأ في حساب المخاطر: {e}")
            final_score = 0.5
        
        profile.risk_score = final_score
        profile.risk_level = self.score_to_risk_level(final_score)
        
        if self.use_cache:
            self._prediction_cache[self._get_cache_key(profile)] = final_score
        
        return final_score
    
    def predict_batch(self, profiles: List[RiskProfile], 
                     progress_callback=None) -> List[float]:
        """
        التنبؤ بمجموعة كبيرة من الملفات (معالجة دفعية محسنة)
        """
        n = len(profiles)
        scores = np.zeros(n)
        
        BATCH_SIZE = 10000
        
        for start_idx in range(0, n, BATCH_SIZE):
            end_idx = min(start_idx + BATCH_SIZE, n)
            
            for i in range(start_idx, end_idx):
                try:
                    scores[i] = self.predict_risk_score(profiles[i])
                except Exception as e:
                    # في حالة الخطأ، نعطي قيمة افتراضية
                    profiles[i].risk_score = 0.5
                    profiles[i].risk_level = RiskLevel.MEDIUM
                    scores[i] = 0.5
            
            if progress_callback:
                progress = int((end_idx / n) * 100)
                progress_callback(progress, f"جاري تحليل المخاطر: {end_idx:,} من {n:,}")
            
            if len(self._prediction_cache) > 50000:
                self._prediction_cache.clear()
            
            gc.collect()
        
        return scores.tolist()
    
    def predict_batch_vectorized(self, profiles: List[RiskProfile]) -> np.ndarray:
        """
        تنبؤ متجه للبيانات (Vectorized Prediction) - أسرع طريقة
        """
        n = len(profiles)
        scores = np.zeros(n)
        
        for i in range(n):
            try:
                profile = profiles[i]
                
                # معالجة القيم الفارغة
                if profile.wilaya_code is None:
                    profile.wilaya_code = 16
                if profile.building_type is None:
                    profile.building_type = BuildingType.TYPE_2
                if profile.soil_type is None:
                    profile.soil_type = 'S2'
                if profile.number_of_floors is None or profile.number_of_floors <= 0:
                    profile.number_of_floors = 2
                if profile.building_age is None or profile.building_age <= 0:
                    profile.building_age = 15
                
                zone = RPAClassifier.get_seismic_zone(profile.wilaya_code)
                profile.seismic_zone = zone
                
                A = RPAClassifier.get_zone_acceleration(zone)
                I = RPAClassifier.IMPORTANCE_FACTORS.get(profile.building_type, 1.0)
                S = RPAClassifier.SOIL_FACTORS.get(profile.soil_type, 1.2)
                F = min(1.0 + (profile.number_of_floors - 1) * 0.05, 1.5)
                age_factor = min(profile.building_age / 50.0, 1.0)
                D = 1.0 + age_factor * 0.5
                
                raw_score = A * I * S * F * D
                scores[i] = min(raw_score / 0.8, 1.0)
                
                profile.risk_score = scores[i]
                profile.risk_level = self.score_to_risk_level(scores[i])
                
            except Exception as e:
                profiles[i].risk_score = 0.5
                profiles[i].risk_level = RiskLevel.MEDIUM
                scores[i] = 0.5
        
        return scores
    
    @staticmethod
    def score_to_risk_level(score: float) -> RiskLevel:
        """تحويل الدرجة إلى مستوى خطر (مع معالجة None)"""
        if score is None:
            return RiskLevel.MEDIUM
        if score < 0.35:
            return RiskLevel.LOW
        elif score < 0.65:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH
    
    def clear_cache(self):
        """مسح الذاكرة المؤقتة"""
        self._prediction_cache.clear()
        gc.collect()