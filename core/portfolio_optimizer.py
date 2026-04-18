"""
محسن محفظة المخاطر التأمينية - Portfolio Risk Mitigation Optimizer
(نسخة مصححة - إصلاح مشاكل VaR والتكلفة)
"""

import numpy as np
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import copy

from core.risk_models import RiskProfile, RiskLevel, PortfolioSummary
from core.monte_carlo import MonteCarloSimulator, SimulationResult


@dataclass
class OptimizationResult:
    """نتائج تحسين المحفظة"""
    selected_profiles: List[RiskProfile] = field(default_factory=list)
    retrofit_decisions: Dict[int, bool] = field(default_factory=dict)
    
    original_var_99: float = 0.0
    original_expected_loss: float = 0.0
    original_high_risk_count: int = 0
    
    optimized_var_99: float = 0.0
    optimized_expected_loss: float = 0.0
    optimized_high_risk_count: int = 0
    
    total_retrofit_cost: float = 0.0
    total_budget: float = 0.0
    budget_utilization: float = 0.0
    loss_reduction: float = 0.0
    var_reduction: float = 0.0
    risk_reduction_pct: float = 0.0
    
    wilaya_spending: Dict[str, float] = field(default_factory=dict)
    wilaya_retrofit_counts: Dict[str, int] = field(default_factory=dict)
    
    optimization_status: str = ""
    solution_found: bool = False
    execution_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'original_var_99': self.original_var_99,
            'original_expected_loss': self.original_expected_loss,
            'optimized_var_99': self.optimized_var_99,
            'optimized_expected_loss': self.optimized_expected_loss,
            'total_retrofit_cost': self.total_retrofit_cost,
            'total_budget': self.total_budget,
            'budget_utilization': self.budget_utilization,
            'loss_reduction': self.loss_reduction,
            'var_reduction': self.var_reduction,
            'risk_reduction_pct': self.risk_reduction_pct,
            'high_risk_reduction': self.original_high_risk_count - self.optimized_high_risk_count,
            'optimization_status': self.optimization_status,
            'solution_found': self.solution_found
        }


class PortfolioOptimizer:
    """
    محسن محفظة المخاطر - نسخة مصححة
    Portfolio Risk Optimizer - Corrected Version
    """
    
    # معاملات التحسين المعدلة
    RETROFIT_RISK_REDUCTION = 0.40      # تخفيض المخاطر بنسبة 40%
    RETROFIT_COST_RATIO = 0.08          # تكلفة التقوية = 8% من رأس المال المؤمن (بـ MDA)
    MAX_WILAYA_BUDGET_RATIO = 0.30      # حد أقصى 30% من الميزانية لولاية واحدة
    MIN_RETROFIT_BENEFIT_RATIO = 0.15   # الحد الأدنى لنسبة الفائدة (15%)
    
    def __init__(self, random_seed: int = 42):
        np.random.seed(random_seed)
        self.simulator = MonteCarloSimulator(random_seed)
    
    def _calculate_expected_loss_for_profile(self, profile: RiskProfile) -> float:
        """
        حساب الخسارة المتوقعة لبوليصة فردية (بـ MDA)
        
        الخسارة المتوقعة = درجة المخاطر × نسبة الخسارة المتوقعة × رأس المال المؤمن
        """
        if profile.sum_insured is None or profile.sum_insured <= 0:
            return 0.0
        
        risk_score = profile.risk_score if profile.risk_score is not None else 0.5
        
        # نسبة الخسارة المتوقعة = 40% من درجة المخاطر
        expected_loss_ratio = risk_score * 0.4
        return expected_loss_ratio * profile.sum_insured
    
    def _calculate_optimized_risk_score(self, profile: RiskProfile, retrofit: bool) -> float:
        """حساب درجة المخاطر بعد التقوية"""
        original_score = profile.risk_score if profile.risk_score is not None else 0.5
        
        if retrofit:
            new_score = original_score * (1 - self.RETROFIT_RISK_REDUCTION)
            return max(0.05, new_score)
        return original_score
    
    def _calculate_retrofit_cost(self, profile: RiskProfile) -> float:
        """
        حساب تكلفة تقوية المبنى (بـ MDA)
        
        المعادلة: 8% من رأس المال المؤمن (مع حد أدنى وأقصى)
        """
        sum_insured = profile.sum_insured if profile.sum_insured is not None else 0
        
        # التكلفة = 8% من رأس المال المؤمن
        cost = sum_insured * self.RETROFIT_COST_RATIO
        
        # تحديد الحدود (بـ MDA)
        min_cost = 0.5   # 500,000 دج كحد أدنى
        max_cost = 50.0  # 50 مليون دج كحد أقصى
        
        return max(min_cost, min(cost, max_cost))
    
    def _calculate_retrofit_benefit(self, profile: RiskProfile) -> float:
        """
        حساب الفائدة المتوقعة من التقوية
        
        الفائدة = تخفيض الخسارة المتوقعة - تكلفة التقوية
        """
        original_loss = self._calculate_expected_loss_for_profile(profile)
        
        # إنشاء نسخة معدلة لحساب الخسارة بعد التقوية
        temp_profile = copy.copy(profile)
        temp_profile.risk_score = self._calculate_optimized_risk_score(profile, True)
        optimized_loss = self._calculate_expected_loss_for_profile(temp_profile)
        
        loss_reduction = original_loss - optimized_loss
        cost = self._calculate_retrofit_cost(profile)
        
        return loss_reduction - cost
    
    def _is_retrofit_worthwhile(self, profile: RiskProfile) -> bool:
        """
        التحقق مما إذا كانت تقوية المبنى مجدية اقتصادياً
        
        Returns:
            True إذا كانت الفائدة > الحد الأدنى للفائدة
        """
        benefit = self._calculate_retrofit_benefit(profile)
        cost = self._calculate_retrofit_cost(profile)
        
        if cost <= 0:
            return False
        
        benefit_ratio = benefit / cost
        return benefit_ratio > self.MIN_RETROFIT_BENEFIT_RATIO
    
    def _group_by_wilaya(self, profiles: List[RiskProfile]) -> Dict[str, List[int]]:
        """تجميع البوليصات حسب الولاية"""
        wilaya_groups = defaultdict(list)
        for idx, profile in enumerate(profiles):
            wilaya = profile.wilaya_name if profile.wilaya_name else "غير محدد"
            wilaya_groups[wilaya].append(idx)
        return dict(wilaya_groups)
    
    def _create_optimized_profiles(
        self, 
        profiles: List[RiskProfile], 
        decisions: List[bool]
    ) -> List[RiskProfile]:
        """إنشاء نسخ محسنة من ملفات المخاطر بعد التقوية"""
        optimized_profiles = []
        
        for i, profile in enumerate(profiles):
            new_profile = copy.copy(profile)
            
            if decisions[i]:
                new_profile.risk_score = self._calculate_optimized_risk_score(profile, True)
                
                if new_profile.risk_score < 0.35:
                    new_profile.risk_level = RiskLevel.LOW
                elif new_profile.risk_score < 0.65:
                    new_profile.risk_level = RiskLevel.MEDIUM
                else:
                    new_profile.risk_level = RiskLevel.HIGH
            else:
                new_profile.risk_score = profile.risk_score or 0.5
            
            optimized_profiles.append(new_profile)
        
        return optimized_profiles
    
    def _calculate_portfolio_metrics(
        self, 
        profiles: List[RiskProfile], 
        n_simulations: int = 2000
    ) -> Tuple[float, float, int]:
        """
        حساب مقاييس المحفظة (الخسارة المتوقعة، VaR، عدد البوليصات عالية الخطر)
        
        Returns:
            tuple: (expected_loss, var_99, high_risk_count)
        """
        if not profiles:
            return 0.0, 0.0, 0
        
        # حساب الخسارة المتوقعة
        expected_loss = sum(self._calculate_expected_loss_for_profile(p) for p in profiles)
        
        # حساب عدد البوليصات عالية الخطر
        high_risk_count = sum(1 for p in profiles if (p.risk_score or 0.5) >= 0.65)
        
        # حساب VaR باستخدام مونت كارلو
        try:
            sim_result = self.simulator.calculate_loss_distribution(profiles, n_simulations)
            var_99 = sim_result.var_99 if sim_result.var_99 is not None else 0.0
        except Exception as e:
            print(f"⚠️ خطأ في حساب VaR: {e}")
            var_99 = 0.0
        
        return expected_loss, var_99, high_risk_count
    
    def optimize_with_pulp(
        self,
        profiles: List[RiskProfile],
        total_budget: float,
        verbose: bool = False
    ) -> OptimizationResult:
        """
        تحسين المحفظة باستخدام PuLP (حل صحيح)
        Portfolio Optimization using PuLP (Integer Solution)
        """
        import time
        start_time = time.time()
        
        result = OptimizationResult()
        result.total_budget = total_budget
        
        if not profiles:
            result.optimization_status = "لا توجد بيانات"
            result.solution_found = False
            return result
        
        try:
            import pulp
            
            n = len(profiles)
            
            # حساب البيانات لكل بوليصة
            retrofit_costs = []
            original_losses = []
            optimized_losses = []
            worthwhile_indices = []
            
            for i, p in enumerate(profiles):
                cost = self._calculate_retrofit_cost(p)
                original_loss = self._calculate_expected_loss_for_profile(p)
                
                # حساب الخسارة بعد التقوية
                temp_score = self._calculate_optimized_risk_score(p, True)
                optimized_loss = temp_score * 0.4 * (p.sum_insured or 0)
                
                retrofit_costs.append(cost)
                original_losses.append(original_loss)
                optimized_losses.append(optimized_loss)
                
                # تسجيل البوليصات التي يمكن تقويتها (التكلفة <= الميزانية)
                if cost <= total_budget:
                    worthwhile_indices.append(i)
            
            if not worthwhile_indices:
                result.optimization_status = "لا توجد بوليصة يمكن تقويتها ضمن الميزانية المتاحة"
                result.solution_found = False
                result.original_expected_loss, result.original_var_99, result.original_high_risk_count = \
                    self._calculate_portfolio_metrics(profiles)
                return result
            
            # إنشاء نموذج التحسين
            prob = pulp.LpProblem("Portfolio_Risk_Mitigation", pulp.LpMinimize)
            
            # متغيرات القرار (فقط للبوليصات المجدية)
            x = {}
            for i in worthwhile_indices:
                x[i] = pulp.LpVariable(f"x_{i}", cat=pulp.LpBinary)
            
            # دالة الهدف: تقليل إجمالي الخسارة
            objective = pulp.lpSum(
                optimized_losses[i] * x.get(i, 0) + original_losses[i] * (1 - x.get(i, 0))
                for i in range(n)
            )
            prob += objective, "Total_Expected_Loss"
            
            # قيد الميزانية
            prob += pulp.lpSum(
                retrofit_costs[i] * x.get(i, 0) for i in worthwhile_indices
            ) <= total_budget, "Budget_Constraint"
            
            # قيد التركيز الجغرافي
            wilaya_groups = self._group_by_wilaya(profiles)
            for wilaya, indices in wilaya_groups.items():
                wilaya_indices = [i for i in indices if i in worthwhile_indices]
                if wilaya_indices:
                    prob += pulp.lpSum(
                        retrofit_costs[i] * x.get(i, 0) for i in wilaya_indices
                    ) <= total_budget * self.MAX_WILAYA_BUDGET_RATIO, f"Wilaya_Budget_{wilaya}"
            
            # حل النموذج
            solver = pulp.PULP_CBC_CMD(msg=verbose, timeLimit=120)
            prob.solve(solver)
            
            # استخراج القرارات
            decisions = [False] * n
            selected_profiles = []
            total_cost = 0.0
            
            for i in worthwhile_indices:
                decision = x[i].varValue == 1 if x[i].varValue else False
                decisions[i] = decision
                if decision:
                    selected_profiles.append(profiles[i])
                    total_cost += retrofit_costs[i]
            
            result.retrofit_decisions = {i: d for i, d in enumerate(decisions)}
            result.selected_profiles = selected_profiles
            result.total_retrofit_cost = total_cost
            result.budget_utilization = (total_cost / total_budget * 100) if total_budget > 0 else 0
            
            # حساب المقاييس قبل التحسين
            (result.original_expected_loss, 
             result.original_var_99, 
             result.original_high_risk_count) = self._calculate_portfolio_metrics(profiles)
            
            # حساب المقاييس بعد التحسين
            optimized_profiles = self._create_optimized_profiles(profiles, decisions)
            (result.optimized_expected_loss, 
             result.optimized_var_99, 
             result.optimized_high_risk_count) = self._calculate_portfolio_metrics(optimized_profiles)
            
            # حساب نسب التحسين
            result.loss_reduction = result.original_expected_loss - result.optimized_expected_loss
            result.var_reduction = result.original_var_99 - result.optimized_var_99
            result.risk_reduction_pct = (
                (result.original_expected_loss - result.optimized_expected_loss) / result.original_expected_loss * 100
                if result.original_expected_loss > 0 else 0
            )
            
            # حساب الإنفاق حسب الولاية
            for wilaya, indices in wilaya_groups.items():
                wilaya_spend = sum(retrofit_costs[i] for i in indices if decisions[i])
                if wilaya_spend > 0:
                    result.wilaya_spending[wilaya] = wilaya_spend
                    result.wilaya_retrofit_counts[wilaya] = sum(1 for i in indices if decisions[i])
            
            result.solution_found = True
            result.optimization_status = "تم الحل الأمثل" if prob.status == pulp.LpStatusOptimal else "تم إيجاد حل ممكن"
            
        except ImportError:
            result.optimization_status = "مكتبة PuLP غير مثبتة. يرجى تثبيتها: pip install pulp"
            result.solution_found = False
        except Exception as e:
            result.optimization_status = f"خطأ في التحسين: {str(e)}"
            result.solution_found = False
        
        result.execution_time = time.time() - start_time
        return result
    
    def optimize_with_scipy(
        self,
        profiles: List[RiskProfile],
        total_budget: float,
        verbose: bool = False
    ) -> OptimizationResult:
        """تحسين المحفظة باستخدام scipy.optimize (حل استرخائي)"""
        import time
        start_time = time.time()
        
        result = OptimizationResult()
        result.total_budget = total_budget
        
        if not profiles:
            result.optimization_status = "لا توجد بيانات"
            result.solution_found = False
            return result
        
        try:
            from scipy.optimize import linprog
            
            n = len(profiles)
            
            retrofit_costs = []
            original_losses = []
            optimized_losses = []
            
            for p in profiles:
                cost = self._calculate_retrofit_cost(p)
                original_loss = self._calculate_expected_loss_for_profile(p)
                temp_score = self._calculate_optimized_risk_score(p, True)
                optimized_loss = temp_score * 0.4 * (p.sum_insured or 0)
                
                retrofit_costs.append(cost)
                original_losses.append(original_loss)
                optimized_losses.append(optimized_loss)
            
            # دالة الهدف
            c = [optimized_losses[i] - original_losses[i] for i in range(n)]
            
            # قيود الميزانية
            A_ub = [retrofit_costs]
            b_ub = [total_budget]
            
            # قيود التركيز الجغرافي
            wilaya_groups = self._group_by_wilaya(profiles)
            for wilaya, indices in wilaya_groups.items():
                wilaya_constraint = [0] * n
                for i in indices:
                    wilaya_constraint[i] = retrofit_costs[i]
                A_ub.append(wilaya_constraint)
                b_ub.append(total_budget * self.MAX_WILAYA_BUDGET_RATIO)
            
            bounds = [(0, 1) for _ in range(n)]
            
            result_linprog = linprog(
                c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs'
            )
            
            if result_linprog.success:
                decisions = [x >= 0.5 for x in result_linprog.x]
                total_cost = sum(retrofit_costs[i] for i, d in enumerate(decisions) if d)
                
                result.retrofit_decisions = {i: d for i, d in enumerate(decisions)}
                result.selected_profiles = [profiles[i] for i, d in enumerate(decisions) if d]
                result.total_retrofit_cost = total_cost
                result.budget_utilization = (total_cost / total_budget * 100) if total_budget > 0 else 0
                
                (result.original_expected_loss, 
                 result.original_var_99, 
                 result.original_high_risk_count) = self._calculate_portfolio_metrics(profiles)
                
                optimized_profiles = self._create_optimized_profiles(profiles, decisions)
                (result.optimized_expected_loss, 
                 result.optimized_var_99, 
                 result.optimized_high_risk_count) = self._calculate_portfolio_metrics(optimized_profiles)
                
                result.loss_reduction = result.original_expected_loss - result.optimized_expected_loss
                result.var_reduction = result.original_var_99 - result.optimized_var_99
                result.risk_reduction_pct = (
                    result.loss_reduction / result.original_expected_loss * 100
                    if result.original_expected_loss > 0 else 0
                )
                
                for wilaya, indices in wilaya_groups.items():
                    wilaya_spend = sum(retrofit_costs[i] for i in indices if decisions[i])
                    if wilaya_spend > 0:
                        result.wilaya_spending[wilaya] = wilaya_spend
                        result.wilaya_retrofit_counts[wilaya] = sum(1 for i in indices if decisions[i])
                
                result.solution_found = True
                result.optimization_status = "تم الحل الأمثل (حل استرخائي)"
            else:
                result.optimization_status = f"لم يتم إيجاد حل - السبب: {result_linprog.message}"
                result.solution_found = False
                
        except ImportError:
            result.optimization_status = "مكتبة scipy غير مثبتة. يرجى تثبيتها: pip install scipy"
            result.solution_found = False
        except Exception as e:
            result.optimization_status = f"خطأ في التحسين: {str(e)}"
            result.solution_found = False
        
        result.execution_time = time.time() - start_time
        return result
    
    def get_optimization_summary(self, result: OptimizationResult) -> str:
        """إنشاء ملخص نصي لنتائج التحسين"""
        if not result.solution_found:
            return f"❌ فشل التحسين: {result.optimization_status}"
        
        summary = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    📊 ملخص تحسين المحفظة                          ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  📈 مقارنة النتائج (بمليون دينار - MDA):                         ║
║  ┌─────────────────────────┬──────────────┬──────────────┐       ║
║  │         المؤشر          │   قبل التحسين │  بعد التحسين │       ║
║  ├─────────────────────────┼──────────────┼──────────────┤       ║
║  │ الخسارة المتوقعة (MDA)  │ {result.original_expected_loss:>12,.2f} │ {result.optimized_expected_loss:>12,.2f} │       ║
║  │ VaR 99% (MDA)           │ {result.original_var_99:>12,.2f} │ {result.optimized_var_99:>12,.2f} │       ║
║  │ عدد البوليصات عالية الخطر│ {result.original_high_risk_count:>12,} │ {result.optimized_high_risk_count:>12,} │       ║
║  └─────────────────────────┴──────────────┴──────────────┘       ║
║                                                                  ║
║  💰 الميزانية والتكاليف (MDA):                                   ║
║  • الميزانية المتاحة: {result.total_budget:>15,.2f} MDA                         ║
║  • التكلفة المستخدمة: {result.total_retrofit_cost:>15,.2f} MDA                         ║
║  • نسبة استخدام الميزانية: {result.budget_utilization:>12.1f}%                        ║
║  • عدد البوليصات المقواة: {len(result.selected_profiles):>12,}                             ║
║                                                                  ║
║  📉 نسب التحسين:                                                ║
║  • تخفيض الخسارة المتوقعة: {result.loss_reduction:>15,.2f} MDA ({result.risk_reduction_pct:.1f}%)    ║
║  • تخفيض VaR 99%: {result.var_reduction:>17,.2f} MDA                    ║
║  • تخفيض البوليصات عالية الخطر: {result.original_high_risk_count - result.optimized_high_risk_count:>9} بوليصات    ║
║                                                                  ║
║  ⏱️ وقت التنفيذ: {result.execution_time:.2f} ثانية                                            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
        
        if result.wilaya_spending:
            summary += "\n\n📌 تفاصيل الإنفاق حسب الولاية (MDA):\n"
            summary += "┌" + "─" * 55 + "┐\n"
            for wilaya, spend in sorted(result.wilaya_spending.items(), key=lambda x: x[1], reverse=True)[:10]:
                count = result.wilaya_retrofit_counts.get(wilaya, 0)
                summary += f"│ {wilaya:<25} │ {spend:>10,.2f} MDA │ {count:>4} │\n"
            summary += "└" + "─" * 55 + "┘"
        
        return summary
    
    def export_optimization_report(
        self, 
        result: OptimizationResult, 
        profiles: List[RiskProfile],
        file_path: str
    ):
        """تصدير تقرير التحسين إلى ملف Excel"""
        try:
            import pandas as pd
            
            retrofit_data = []
            for idx, profile in enumerate(result.selected_profiles):
                retrofit_data.append({
                    'الولاية': profile.wilaya_name,
                    'البلدية': profile.commune_name,
                    'رأس المال المؤمن (MDA)': profile.sum_insured,
                    'رأس المال المؤمن (دج)': profile.sum_insured * 1_000_000,
                    'درجة المخاطر الأصلية': profile.risk_score,
                    'درجة المخاطر بعد التقوية': max(0.05, (profile.risk_score or 0.5) * 0.6),
                    'تكلفة التقوية (MDA)': profile.sum_insured * self.RETROFIT_COST_RATIO,
                    'تكلفة التقوية (دج)': profile.sum_insured * self.RETROFIT_COST_RATIO * 1_000_000,
                    'تخفيض الخسارة (MDA)': (profile.risk_score or 0.5) * 0.4 * profile.sum_insured * self.RETROFIT_RISK_REDUCTION,
                    'نوع المبنى': profile.structure_type.value if profile.structure_type else '-',
                    'المنطقة الزلزالية': profile.seismic_zone.name if profile.seismic_zone else '-'
                })
            
            df_retrofit = pd.DataFrame(retrofit_data)
            
            stats_data = [
                {'المؤشر': 'الخسارة المتوقعة قبل التحسين (MDA)', 'القيمة': result.original_expected_loss},
                {'المؤشر': 'الخسارة المتوقعة قبل التحسين (دج)', 'القيمة': result.original_expected_loss * 1_000_000},
                {'المؤشر': 'الخسارة المتوقعة بعد التحسين (MDA)', 'القيمة': result.optimized_expected_loss},
                {'المؤشر': 'الخسارة المتوقعة بعد التحسين (دج)', 'القيمة': result.optimized_expected_loss * 1_000_000},
                {'المؤشر': 'VaR 99% قبل التحسين (MDA)', 'القيمة': result.original_var_99},
                {'المؤشر': 'VaR 99% قبل التحسين (دج)', 'القيمة': result.original_var_99 * 1_000_000},
                {'المؤشر': 'VaR 99% بعد التحسين (MDA)', 'القيمة': result.optimized_var_99},
                {'المؤشر': 'VaR 99% بعد التحسين (دج)', 'القيمة': result.optimized_var_99 * 1_000_000},
                {'المؤشر': 'عدد البوليصات عالية الخطر قبل التحسين', 'القيمة': result.original_high_risk_count},
                {'المؤشر': 'عدد البوليصات عالية الخطر بعد التحسين', 'القيمة': result.optimized_high_risk_count},
                {'المؤشر': 'الميزانية المتاحة (MDA)', 'القيمة': result.total_budget},
                {'المؤشر': 'الميزانية المتاحة (دج)', 'القيمة': result.total_budget * 1_000_000},
                {'المؤشر': 'التكلفة المستخدمة (MDA)', 'القيمة': result.total_retrofit_cost},
                {'المؤشر': 'التكلفة المستخدمة (دج)', 'القيمة': result.total_retrofit_cost * 1_000_000},
                {'المؤشر': 'نسبة استخدام الميزانية (%)', 'القيمة': result.budget_utilization},
                {'المؤشر': 'عدد البوليصات المقواة', 'القيمة': len(result.selected_profiles)},
                {'المؤشر': 'تخفيض الخسارة (MDA)', 'القيمة': result.loss_reduction},
                {'المؤشر': 'تخفيض الخسارة (دج)', 'القيمة': result.loss_reduction * 1_000_000},
                {'المؤشر': 'نسبة تخفيض الخسارة (%)', 'القيمة': result.risk_reduction_pct},
                {'المؤشر': 'وقت التنفيذ (ثانية)', 'القيمة': result.execution_time},
            ]
            
            df_stats = pd.DataFrame(stats_data)
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df_retrofit.to_excel(writer, sheet_name='البوليصات المقترحة', index=False)
                df_stats.to_excel(writer, sheet_name='الإحصائيات', index=False)
            
            return True
            
        except Exception as e:
            print(f"خطأ في تصدير التقرير: {e}")
            return False