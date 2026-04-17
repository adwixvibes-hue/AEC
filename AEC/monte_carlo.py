"""
محاكاة مونتي كارلو
"""

import numpy as np
from datetime import datetime
import uuid

from data_models import SimulationResult


class MonteCarloSimulator:
    """محاكي مونتي كارلو"""
    
    def __init__(self, retention_ratio: float = 0.30):
        self.retention_ratio = retention_ratio
    
    def run_simulation(self, portfolio_value: float, region_risk_score: float,
                      n_simulations: int = 10000, region_name: str = "") -> SimulationResult:
        """تشغيل المحاكاة"""
        
        # محاكاة شدة الزلزال (توزيع بيتا)
        intensity = np.random.beta(a=2, b=5, size=n_simulations) * 5 + 4
        
        # حساب نسبة الضرر
        damage = 1 / (1 + np.exp(-3 * (intensity - 6.5)))
        damage = damage * (0.5 + region_risk_score)
        damage = np.clip(damage, 0, 1)
        
        # عدم يقين إضافي
        uncertainty = np.random.lognormal(mean=0, sigma=0.3, size=n_simulations)
        
        # الخسائر
        losses = portfolio_value * damage * uncertainty
        losses = np.clip(losses, 0, portfolio_value)
        
        # حصة الشركة
        company_losses = losses * self.retention_ratio
        
        return SimulationResult(
            simulation_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(),
            region_name=region_name,
            portfolio_value=portfolio_value,
            n_simulations=n_simulations,
            mean_loss=np.mean(losses),
            std_loss=np.std(losses),
            var_95=np.percentile(losses, 95),
            var_99=np.percentile(losses, 99),
            tvar_99=np.mean(losses[losses >= np.percentile(losses, 99)]),
            max_loss=np.max(losses),
            company_retention_ratio=self.retention_ratio,
            mean_company_loss=np.mean(company_losses),
            var_99_company=np.percentile(company_losses, 99),
            max_company_loss=np.max(company_losses),
            loss_distribution=losses
        )