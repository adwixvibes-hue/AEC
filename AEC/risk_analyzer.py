"""
محلل المخاطر الرئيسي
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
import os
from datetime import datetime

from data_models import RegionRisk, PortfolioSummary, InsurancePolicy
from constants import SEISMIC_ZONES, WILAYA_COORDINATES, BUILDING_TYPES


class RiskAnalyzer:
    """محلل المخاطر الرئيسي"""
    
    def __init__(self):
        self.regions_data: Dict[str, RegionRisk] = {}
        self.policies: List[InsurancePolicy] = []
        self.portfolio_summary = PortfolioSummary()
        self.risk_statistics: Dict[str, Any] = {}
        
    def initialize_algeria_data(self):
        """تهيئة بيانات الجزائر"""
        print("🗺️ جاري تهيئة بيانات الجزائر...")
        
        for code, zone_data in SEISMIC_ZONES.items():
            region = RegionRisk(
                wilaya_name=zone_data['name'],
                wilaya_code=code,
                seismic_zone=zone_data['zone'],
                base_risk_score=zone_data['risk'],
                historical_earthquakes=self._get_historical_earthquakes(zone_data['name']),
                adjusted_risk_score=zone_data['risk']
            )
            self.regions_data[zone_data['name']] = region
        
        print(f"✅ تم تهيئة {len(self.regions_data)} منطقة")
    
    def _get_historical_earthquakes(self, wilaya_name: str) -> int:
        """عدد الزلازل التاريخية"""
        data = {
            "الشلف": 15, "البليدة": 12, "بومرداس": 14, "تيبازة": 10,
            "تيزي وزو": 8, "بجاية": 7, "جيجل": 6, "سكيكدة": 5,
            "عنابة": 4, "الجزائر": 9, "البويرة": 6, "المدية": 5,
            "عين الدفلى": 7, "وهران": 3, "قسنطينة": 5, "سطيف": 6
        }
        return data.get(wilaya_name, 3)
    
    def load_csv_files(self, filepaths: List[str]):
        """تحميل ملفات CSV"""
        total = 0
        for filepath in filepaths:
            if os.path.exists(filepath):
                count = self._load_single_csv(filepath)
                total += count
                print(f"✅ تم تحميل {count:,} بوليصة من {filepath}")
        print(f"\n📊 إجمالي البوالص المحملة: {total:,}")
        self.calculate_portfolio_metrics()
    
    def _load_single_csv(self, filepath: str) -> int:
        """تحميل ملف CSV واحد"""
        try:
            df = pd.read_csv(filepath, encoding='utf-8')
            count = 0
            
            for _, row in df.iterrows():
                try:
                    # استخراج اسم الولاية
                    raw_wilaya = str(row['WILAYA']).strip()
                    if ' - ' in raw_wilaya:
                        wilaya = raw_wilaya.split(' - ')[-1].strip()
                    elif '-' in raw_wilaya:
                        wilaya = raw_wilaya.split('-')[-1].strip()
                    else:
                        wilaya = raw_wilaya
                    
                    # تنظيف القيم
                    capital = float(str(row['CAPITAL_ASSURE']).replace(',', '').replace('"', ''))
                    premium = float(str(row['PRIME_NETTE']).replace(',', '').replace('"', ''))
                    
                    if capital <= 0 or premium < 0:
                        continue
                    
                    # نوع المبنى
                    raw_type = str(row.get('TYPE', 'Standard'))
                    if 'immobilier' in raw_type or 'Bien' in raw_type:
                        building_type = 'mixed'
                    elif 'Industrielle' in raw_type:
                        building_type = 'reinforced_concrete'
                    elif 'Commerciale' in raw_type:
                        building_type = 'steel_frame'
                    else:
                        building_type = 'mixed'
                    
                    policy = InsurancePolicy(
                        policy_id=str(row['NUMERO_POLICE']),
                        wilaya=wilaya,
                        insured_value=capital,
                        premium=premium,
                        building_type=building_type,
                        construction_year=2010
                    )
                    self.add_policy(policy)
                    count += 1
                    
                except Exception:
                    continue
            
            return count
        except Exception as e:
            print(f"خطأ في {filepath}: {e}")
            return 0
    
    def add_policy(self, policy: InsurancePolicy):
        """إضافة بوليصة"""
        if policy.wilaya not in self.regions_data:
            # إضافة منطقة جديدة إذا لم تكن موجودة
            risk = 0.5
            zone = "II"
            region = RegionRisk(
                wilaya_name=policy.wilaya,
                wilaya_code=999,
                seismic_zone=zone,
                base_risk_score=risk,
                adjusted_risk_score=risk
            )
            self.regions_data[policy.wilaya] = region
        
        self.policies.append(policy)
        region = self.regions_data[policy.wilaya]
        region.total_insured_value += policy.insured_value
        region.policy_count += 1
        region.premium_volume += policy.premium
    
    def calculate_portfolio_metrics(self) -> PortfolioSummary:
        """حساب مقاييس المحفظة"""
        if not self.policies:
            return self.portfolio_summary
        
        total_value = sum(p.insured_value for p in self.policies)
        total_premium = sum(p.premium for p in self.policies)
        
        # تحديث درجات المخاطر للمناطق
        for region in self.regions_data.values():
            if region.total_insured_value > 0:
                factor = min(np.log10(region.total_insured_value) / 10, 1.5)
                region.adjusted_risk_score = min(region.base_risk_score * factor, 1.0)
        
        # حساب التعرض للمخاطر
        high_risk = 0
        medium_risk = 0
        low_risk = 0
        
        for policy in self.policies:
            region = self.regions_data.get(policy.wilaya)
            if region:
                score = region.adjusted_risk_score
                if score >= 0.7:
                    high_risk += policy.insured_value
                elif score >= 0.4:
                    medium_risk += policy.insured_value
                else:
                    low_risk += policy.insured_value
        
        # حساب متوسط المخاطر المرجح
        weighted_risk = 0
        for policy in self.policies:
            region = self.regions_data.get(policy.wilaya)
            if region:
                weighted_risk += region.adjusted_risk_score * policy.insured_value
        weighted_risk /= total_value if total_value > 0 else 1
        
        self.portfolio_summary = PortfolioSummary(
            total_policies=len(self.policies),
            total_insured_value=total_value,
            total_premium=total_premium,
            average_risk_score=weighted_risk,
            regions_count=len(set(p.wilaya for p in self.policies)),
            high_risk_exposure=high_risk,
            medium_risk_exposure=medium_risk,
            low_risk_exposure=low_risk
        )
        
        return self.portfolio_summary
    
    def calculate_concentration_risk(self) -> pd.DataFrame:
        """حساب مخاطر التركيز"""
        data = []
        total = self.portfolio_summary.total_insured_value
        
        for name, region in self.regions_data.items():
            if region.total_insured_value > 0:
                concentration = (region.total_insured_value / total * 100) if total > 0 else 0
                risk_index = concentration * region.adjusted_risk_score
                
                data.append({
                    'المنطقة': name,
                    'القيمة المؤمنة': region.total_insured_value,
                    'عدد الوثائق': region.policy_count,
                    'درجة الخطورة المعدلة': region.adjusted_risk_score,
                    'نسبة التركيز': concentration,
                    'مؤشر المخاطر المركب': risk_index,
                    'فئة المخاطر': region.get_risk_category()
                })
        
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values('مؤشر المخاطر المركب', ascending=False)
        return df
    
    def get_risk_distribution(self) -> Dict[str, float]:
        """توزيع المخاطر"""
        dist = {'أحمر': 0, 'برتقالي': 0, 'أخضر': 0}
        for region in self.regions_data.values():
            if region.total_insured_value > 0:
                dist[region.get_risk_category()] += region.total_insured_value
        return dist
    
    def get_high_risk_concentration_ratio(self) -> float:
        """نسبة تركيز المخاطر العالية"""
        total = self.portfolio_summary.total_insured_value
        if total > 0:
            return (self.portfolio_summary.high_risk_exposure / total) * 100
        return 0
    
    def get_region_risk_profile(self, region_name: str) -> Optional[Dict]:
        """ملف مخاطر المنطقة"""
        if region_name not in self.regions_data:
            return None
        
        region = self.regions_data[region_name]
        return {
            'basic_info': {'name': region.wilaya_name, 'seismic_zone': region.seismic_zone},
            'risk_scores': {'adjusted_risk': region.adjusted_risk_score, 'risk_category': region.get_risk_category()},
            'portfolio_stats': {
                'total_policies': region.policy_count,
                'total_insured_value': region.total_insured_value,
                'concentration': region.calculate_concentration(self.portfolio_summary.total_insured_value)
            }
        }
    
    def generate_risk_report(self) -> str:
        """تقرير المخاطر"""
        self.calculate_portfolio_metrics()
        dist = self.get_risk_distribution()
        total = sum(dist.values())
        
        report = f"""
{'='*60}
تقرير تحليل المخاطر
{'='*60}
التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 ملخص المحفظة:
• إجمالي القيمة: {self.portfolio_summary.total_insured_value:,.0f} دج
• عدد الوثائق: {self.portfolio_summary.total_policies:,}
• متوسط الخطورة: {self.portfolio_summary.average_risk_score:.3f}

📈 توزيع المخاطر:
• أحمر: {dist['أحمر']:,.0f} دج ({dist['أحمر']/total*100 if total>0 else 0:.1f}%)
• برتقالي: {dist['برتقالي']:,.0f} دج ({dist['برتقالي']/total*100 if total>0 else 0:.1f}%)
• أخضر: {dist['أخضر']:,.0f} دج ({dist['أخضر']/total*100 if total>0 else 0:.1f}%)

{'='*60}
"""
        return report