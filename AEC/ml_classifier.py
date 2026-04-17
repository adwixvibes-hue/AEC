"""
تصنيف المخاطر باستخدام CatBoost
"""

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import os
from typing import Dict, Any
from collections import Counter

from data_models import InsurancePolicy, RegionRisk
from constants import BUILDING_TYPES


class RiskClassifier:
    """مصنف المخاطر"""
    
    def __init__(self, model_path: str = "models/risk_classifier.cbm"):
        self.model_path = model_path
        self.model = None
        self.is_trained = False
        
        if os.path.exists(model_path):
            self.load_model()
    
    def calculate_risk_score(self, policy: InsurancePolicy, region: RegionRisk) -> float:
        """حساب درجة المخاطر"""
        # عوامل مختلفة
        base = region.base_risk_score
        building = BUILDING_TYPES.get(policy.building_type, {'risk_factor': 0.5})['risk_factor']
        age = min(policy.calculate_age() / 50, 1.0)
        
        # وزن واقعي
        score = base * 0.4 + building * 0.3 + age * 0.2 + np.random.uniform(0, 0.1)
        return np.clip(score, 0, 1)
    
    def prepare_data(self, policies: list, regions_data: dict):
        """تحضير البيانات للتدريب"""
        features = []
        labels = []
        
        for policy in policies:
            region = regions_data.get(policy.wilaya)
            if not region:
                continue
            
            risk = self.calculate_risk_score(policy, region)
            
            features.append({
                'log_value': np.log1p(policy.insured_value),
                'age': policy.calculate_age(),
                'base_risk': region.base_risk_score,
                'building_factor': BUILDING_TYPES.get(policy.building_type, {'risk_factor': 0.5})['risk_factor'],
            })
            
            # تصنيف ثلاثي
            if risk >= 0.65:
                labels.append(2)
            elif risk >= 0.35:
                labels.append(1)
            else:
                labels.append(0)
        
        X = pd.DataFrame(features)
        y = np.array(labels)
        
        print(f"\n📊 توزيع التصنيفات:")
        counts = Counter(y)
        print(f"   أخضر: {counts.get(0, 0)}")
        print(f"   برتقالي: {counts.get(1, 0)}")
        print(f"   أحمر: {counts.get(2, 0)}")
        
        return X, y
    
    def train(self, policies: list, regions_data: dict) -> Dict:
        """تدريب النموذج"""
        print("🔄 تحضير البيانات للتدريب...")
        
        # أخذ عينة للتدريب
        sample_size = min(30000, len(policies))
        if len(policies) > sample_size:
            indices = np.random.choice(len(policies), sample_size, replace=False)
            policies = [policies[i] for i in indices]
        
        X, y = self.prepare_data(policies, regions_data)
        
        if len(X) == 0 or len(np.unique(y)) < 2:
            return {'accuracy': 0, 'error': 'بيانات غير كافية'}
        
        # تقسيم البيانات
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"📊 تدريب: {len(X_train)}, اختبار: {len(X_test)}")
        
        # إنشاء النموذج
        self.model = CatBoostClassifier(
            iterations=200,
            learning_rate=0.05,
            depth=5,
            loss_function='MultiClass',
            verbose=50,
            random_seed=42
        )
        
        print("🚀 بدء التدريب...")
        self.model.fit(X_train, y_train, eval_set=(X_test, y_test), verbose=50)
        
        # التقييم
        y_pred = self.model.predict(X_test)
        accuracy = (y_pred.flatten() == y_test).mean()
        
        self.is_trained = True
        self.save_model()
        
        print(f"✅ الدقة: {accuracy:.2%}")
        return {'accuracy': accuracy}
    
    def predict(self, policies: list, regions_data: dict) -> pd.DataFrame:
        """التصنيف"""
        if not self.is_trained:
            return self._rule_based_predict(policies, regions_data)
        
        results = []
        for policy in policies[:5000]:  # حد للسرعة
            region = regions_data.get(policy.wilaya)
            if region:
                risk = self.calculate_risk_score(policy, region)
                if risk >= 0.65:
                    cat = 'أحمر'
                elif risk >= 0.35:
                    cat = 'برتقالي'
                else:
                    cat = 'أخضر'
                
                results.append({
                    'policy_id': policy.policy_id,
                    'wilaya': policy.wilaya,
                    'risk_category': cat
                })
        
        return pd.DataFrame(results)
    
    def _rule_based_predict(self, policies: list, regions_data: dict) -> pd.DataFrame:
        """تصنيف مبني على القواعد"""
        results = []
        for policy in policies:
            region = regions_data.get(policy.wilaya)
            if region:
                risk = self.calculate_risk_score(policy, region)
                if risk >= 0.65:
                    cat = 'أحمر'
                elif risk >= 0.35:
                    cat = 'برتقالي'
                else:
                    cat = 'أخضر'
                
                results.append({
                    'policy_id': policy.policy_id,
                    'wilaya': policy.wilaya,
                    'risk_category': cat
                })
        return pd.DataFrame(results)
    
    def predict_single(self, policy: InsurancePolicy, region: RegionRisk) -> Dict:
        """تصنيف بوليصة واحدة"""
        risk = self.calculate_risk_score(policy, region)
        
        if risk >= 0.65:
            return {'risk_category': 'أحمر', 'risk_score': risk}
        elif risk >= 0.35:
            return {'risk_category': 'برتقالي', 'risk_score': risk}
        else:
            return {'risk_category': 'أخضر', 'risk_score': risk}
    
    def save_model(self):
        """حفظ النموذج"""
        if self.model:
            os.makedirs("models", exist_ok=True)
            self.model.save_model(self.model_path)
    
    def load_model(self) -> bool:
        """تحميل النموذج"""
        try:
            self.model = CatBoostClassifier()
            self.model.load_model(self.model_path)
            self.is_trained = True
            return True
        except:
            return False