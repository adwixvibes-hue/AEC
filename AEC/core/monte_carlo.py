"""
محاكاة مونت كارلو لحساب الخسائر (نسخة محسنة مع معالجة None)
Monte Carlo Simulation for Loss Calculation (Optimized with None handling)
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field

from .risk_models import RiskProfile, RiskLevel, PortfolioSummary


@dataclass
class SimulationResult:
    """نتائج محاكاة مونت كارلو"""
    loss_samples: np.ndarray = field(default_factory=lambda: np.array([]))
    mean_loss: float = 0.0
    std_loss: float = 0.0
    var_95: float = 0.0
    var_99: float = 0.0
    tvar_95: float = 0.0
    tvar_99: float = 0.0
    max_loss: float = 0.0
    loss_distribution: Dict = field(default_factory=dict)


class MonteCarloSimulator:
    """
    محاكي مونت كارلو للخسائر الزلزالية
    Monte Carlo Simulator for Seismic Losses
    """
    
    def __init__(self, random_seed: int = 42):
        """
        تهيئة المحاكي
        """
        np.random.seed(random_seed)
        
        # معاملات الضرر حسب مستوى الخطر
        self.damage_ratios = {
            RiskLevel.LOW: (0.0, 0.1),
            RiskLevel.MEDIUM: (0.1, 0.3),
            RiskLevel.HIGH: (0.3, 0.8),
        }
        
        # معاملات التضخيم حسب المنطقة الزلزالية
        self.zone_multipliers = {
            0: 0.3,
            1: 0.6,
            2: 0.8,
            3: 1.0,
            4: 1.5,
        }
    
    def _safe_get_zone_value(self, profile: RiskProfile) -> int:
        """الحصول على قيمة المنطقة الزلزالية بشكل آمن"""
        try:
            if profile.seismic_zone is not None:
                return profile.seismic_zone.value
        except:
            pass
        return 1  # ZONE_I كقيمة افتراضية
    
    def _safe_get_risk_level(self, profile: RiskProfile) -> RiskLevel:
        """الحصول على مستوى الخطر بشكل آمن"""
        try:
            if profile.risk_level is not None:
                return profile.risk_level
        except:
            pass
        return RiskLevel.MEDIUM
    
    def _calculate_expected_loss_ratio(self, profile: RiskProfile) -> float:
        """
        حساب نسبة الخسارة المتوقعة (مع معالجة None)
        """
        try:
            risk_score = profile.risk_score if profile.risk_score is not None else 0.5
            base_ratio = risk_score
            
            # تعديل حسب نوع المبنى
            if profile.structure_type is not None:
                if "جدران" in str(profile.structure_type.value) or "SHEAR" in str(profile.structure_type.name):
                    base_ratio *= 0.8
                elif "حجرية" in str(profile.structure_type.value) or "MASONRY" in str(profile.structure_type.name):
                    base_ratio *= 1.3
            
            # تعديل حسب العمر
            age = profile.building_age if profile.building_age is not None else 15
            if age > 30:
                base_ratio *= 1.2
            elif age > 15:
                base_ratio *= 1.1
            
            return np.clip(base_ratio, 0.0, 1.0)
        except:
            return 0.3
    
    def calculate_loss_distribution(
        self,
        profiles: List[RiskProfile],
        n_simulations: int = 10000,
        correlation_factor: float = 0.3
    ) -> SimulationResult:
        """
        حساب توزيع الخسائر باستخدام محاكاة مونت كارلو
        """
        if not profiles:
            return self._empty_result()
        
        n_policies = len(profiles)
        policy_losses = np.zeros((n_simulations, n_policies))
        
        for i, profile in enumerate(profiles):
            try:
                # حساب الخسارة المتوقعة
                expected_loss_ratio = self._calculate_expected_loss_ratio(profile)
                
                # الحصول على مستوى الخطر بشكل آمن
                risk_level = self._safe_get_risk_level(profile)
                
                # الحصول على حدود الضرر
                min_damage, max_damage = self.damage_ratios.get(risk_level, (0.1, 0.3))
                
                # الحصول على معامل المنطقة
                zone_val = self._safe_get_zone_value(profile)
                zone_mult = self.zone_multipliers.get(zone_val, 1.0)
                
                # توليد عينات الخسارة
                alpha = 2.0 + expected_loss_ratio * 5
                beta = 5.0 - expected_loss_ratio * 3
                alpha = max(1.1, alpha)
                beta = max(1.1, beta)
                
                damage_samples = np.random.beta(alpha, beta, n_simulations)
                damage_samples = min_damage + damage_samples * (max_damage - min_damage)
                damage_samples *= zone_mult
                damage_samples = np.clip(damage_samples, 0.0, 1.0)
                
                # حساب الخسارة المالية
                sum_insured = profile.sum_insured if profile.sum_insured is not None else 0
                policy_losses[:, i] = damage_samples * sum_insured
                
            except Exception as e:
                # في حالة الخطأ، نستخدم قيماً افتراضية
                sum_insured = profile.sum_insured if profile.sum_insured is not None else 0
                policy_losses[:, i] = np.random.uniform(0.05, 0.15, n_simulations) * sum_insured
        
        # إضافة ارتباط بين البوليصات
        if correlation_factor > 0 and n_policies > 1:
            try:
                policy_losses = self._add_correlation(policy_losses, correlation_factor)
            except:
                pass
        
        # حساب إجمالي الخسائر
        total_losses = policy_losses.sum(axis=1)
        
        # حساب الإحصائيات
        mean_loss = np.mean(total_losses) if len(total_losses) > 0 else 0
        std_loss = np.std(total_losses) if len(total_losses) > 0 else 0
        var_95 = np.percentile(total_losses, 95) if len(total_losses) > 0 else 0
        var_99 = np.percentile(total_losses, 99) if len(total_losses) > 0 else 0
        
        tvar_95 = total_losses[total_losses >= var_95].mean() if np.any(total_losses >= var_95) else var_95
        tvar_99 = total_losses[total_losses >= var_99].mean() if np.any(total_losses >= var_99) else var_99
        
        max_loss = np.max(total_losses) if len(total_losses) > 0 else 0
        
        return SimulationResult(
            loss_samples=total_losses,
            mean_loss=mean_loss,
            std_loss=std_loss,
            var_95=var_95,
            var_99=var_99,
            tvar_95=tvar_95,
            tvar_99=tvar_99,
            max_loss=max_loss,
            loss_distribution={}
        )
    
    def _add_correlation(self, losses: np.ndarray, correlation: float) -> np.ndarray:
        """إضافة ارتباط بين البوليصات"""
        try:
            n_sim, n_pol = losses.shape
            common_factor = np.random.normal(0, 1, n_sim)
            
            for i in range(n_pol):
                mean_loss = losses[:, i].mean()
                if mean_loss > 0:
                    losses[:, i] = (1 - correlation) * losses[:, i] + correlation * common_factor * mean_loss
            
            return np.clip(losses, 0, None)
        except:
            return losses
    
    def _empty_result(self) -> SimulationResult:
        """نتيجة فارغة"""
        return SimulationResult(
            loss_samples=np.array([]),
            mean_loss=0.0,
            std_loss=0.0,
            var_95=0.0,
            var_99=0.0,
            tvar_95=0.0,
            tvar_99=0.0,
            max_loss=0.0,
            loss_distribution={}
        )
    
    def calculate_portfolio_metrics(
        self,
        profiles: List[RiskProfile],
        n_simulations: int = 10000
    ) -> PortfolioSummary:
        """
        حساب مقاييس المحفظة كاملة
        """
        summary = PortfolioSummary()
        
        if not profiles:
            return summary
        
        try:
            # الإحصائيات الأساسية
            summary.total_policies = len(profiles)
            summary.total_sum_insured = sum(p.sum_insured for p in profiles if p.sum_insured is not None)
            
            # توزيع المخاطر
            for profile in profiles:
                try:
                    risk_level = self._safe_get_risk_level(profile)
                    if risk_level == RiskLevel.LOW:
                        summary.low_risk_count += 1
                    elif risk_level == RiskLevel.MEDIUM:
                        summary.medium_risk_count += 1
                    else:
                        summary.high_risk_count += 1
                except:
                    summary.medium_risk_count += 1
            
            # محاكاة مونت كارلو
            result = self.calculate_loss_distribution(profiles, n_simulations)
            
            summary.var_95 = result.var_95
            summary.var_99 = result.var_99
            summary.tvar_95 = result.tvar_95
            summary.expected_loss = result.mean_loss
            summary.max_probable_loss = result.max_loss
            summary.loss_samples = result.loss_samples
            
            # حساب الأقساط المتوقعة
            for profile in profiles:
                try:
                    risk_score = profile.risk_score if profile.risk_score is not None else 0.5
                    sum_insured = profile.sum_insured if profile.sum_insured is not None else 0
                    expected_loss = risk_score * 0.4 * sum_insured
                    premium = expected_loss * 1.5 * 1.3
                    profile.premium_rate = premium / sum_insured if sum_insured > 0 else 0
                    summary.total_premium += premium
                except:
                    pass
            
            # توزيع التعرض حسب الولاية
            for profile in profiles:
                try:
                    wilaya = profile.wilaya_name if profile.wilaya_name else "غير محدد"
                    sum_insured = profile.sum_insured if profile.sum_insured is not None else 0
                    if wilaya not in summary.wilaya_exposure:
                        summary.wilaya_exposure[wilaya] = 0
                    summary.wilaya_exposure[wilaya] += sum_insured
                except:
                    pass
            
        except Exception as e:
            print(f"خطأ في حساب مقاييس المحفظة: {e}")
        
        return summary