"""
محمل البيانات (نسخة محسنة مع توحيد وحدة القياس)
Data Loader (Optimized with Unit Standardization)
"""

import pandas as pd
import numpy as np
import re
from typing import List, Optional, Dict, Any, Tuple, Callable

from core.risk_models import RiskProfile, StructureType, BuildingType, SeismicZone


class DataLoader:
    """
    محمل البيانات - يوحد وحدة القياس إلى مليون دينار (MDA)
    Data Loader - Standardizes unit to Million Dinar (MDA)
    """
    
    # عامل التحويل من دينار إلى مليون دينار
    DZD_TO_MDA = 1_000_000
    
    WILAYA_NAMES: Dict[int, str] = {
        1: "أدرار", 2: "الشلف", 3: "الأغواط", 4: "أم البواقي",
        5: "باتنة", 6: "بجاية", 7: "بسكرة", 8: "بشار",
        9: "البليدة", 10: "البويرة", 11: "تمنراست", 12: "تبسة",
        13: "تلمسان", 14: "تيارت", 15: "تيزي وزو", 16: "الجزائر",
        17: "الجلفة", 18: "جيجل", 19: "سطيف", 20: "سعيدة",
        21: "سكيكدة", 22: "سيدي بلعباس", 23: "عنابة", 24: "قالمة",
        25: "قسنطينة", 26: "المدية", 27: "مستغانم", 28: "المسيلة",
        29: "معسكر", 30: "ورقلة", 31: "وهران", 32: "البيض",
        33: "إليزي", 34: "برج بوعريريج", 35: "بومرداس", 36: "الطارف",
        37: "تندوف", 38: "تيسمسيلت", 39: "الوادي", 40: "خنشلة",
        41: "سوق أهراس", 42: "تيبازة", 43: "ميلة", 44: "عين الدفلى",
        45: "النعامة", 46: "عين تموشنت", 47: "غرداية", 48: "غليزان",
    }
    
    @classmethod
    def convert_to_mda(cls, value: float) -> float:
        """
        تحويل القيمة من دينار إلى مليون دينار (MDA)
        Convert from DZD to Million Dinar (MDA)
        
        Args:
            value: القيمة بالدينار
        
        Returns:
            القيمة بمليون دينار
        """
        if value is None:
            return 0.0
        return value / cls.DZD_TO_MDA
    
    @classmethod
    def convert_from_mda(cls, value: float) -> float:
        """
        تحويل القيمة من مليون دينار إلى دينار
        Convert from MDA to DZD
        
        Args:
            value: القيمة بمليون دينار
        
        Returns:
            القيمة بالدينار
        """
        if value is None:
            return 0.0
        return value * cls.DZD_TO_MDA
    
    @classmethod
    def detect_sheet_name(cls, file_path: str) -> List[str]:
        """اكتشاف أسماء الأوراق المتاحة في الملف"""
        try:
            xl_file = pd.ExcelFile(file_path, engine='openpyxl')
            return xl_file.sheet_names
        except Exception as e:
            raise Exception(f"خطأ في قراءة أسماء الأوراق: {str(e)}")
    
    @classmethod
    def get_recommended_sheet(cls, file_path: str) -> str:
        """الحصول على الورقة الموصى بها للتحميل"""
        sheets = cls.detect_sheet_name(file_path)
        
        if not sheets:
            raise ValueError("لم يتم العثور على أي ورقة في الملف")
        
        priority_keywords = ['2023', '2024', '2025', 'data', 'Data', 'Sheet1', 'Feuil1']
        
        for keyword in priority_keywords:
            for sheet in sheets:
                if keyword.lower() in sheet.lower():
                    return sheet
        
        return sheets[0]
    
    @classmethod
    def _detect_columns(cls, df: pd.DataFrame) -> Dict[str, str]:
        """اكتشاف أسماء الأعمدة تلقائياً"""
        columns = df.columns.tolist()
        mapping = {}
        
        wilaya_keywords = ['WILAYA', 'wilaya', 'WILAYA_CODE', 'CODE_WILAYA', 'ولاية']
        for col in columns:
            for kw in wilaya_keywords:
                if kw.lower() in col.lower():
                    mapping['wilaya'] = col
                    break
            if 'wilaya' in mapping:
                break
        
        commune_keywords = ['COMMUNE', 'commune', 'COMMUNE_NAME', 'بلدية']
        for col in columns:
            for kw in commune_keywords:
                if kw.lower() in col.lower():
                    mapping['commune'] = col
                    break
            if 'commune' in mapping:
                break
        
        capital_keywords = ['CAPITAL', 'capital', 'ASSURE', 'assure', 'SUM_INSURED', 'مؤمن']
        for col in columns:
            for kw in capital_keywords:
                if kw.lower() in col.lower():
                    mapping['capital'] = col
                    break
            if 'capital' in mapping:
                break
        
        type_keywords = ['TYPE', 'type', 'BRANCHE', 'نوع']
        for col in columns:
            for kw in type_keywords:
                if kw.lower() in col.lower():
                    mapping['type'] = col
                    break
            if 'type' in mapping:
                break
        
        return mapping
    
    @classmethod
    def _clean_numeric(cls, value) -> float:
        """تنظيف القيم الرقمية"""
        if pd.isna(value):
            return 0.0
        
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            value_str = str(value).strip()
            
            if not value_str or value_str.lower() in ['nan', 'null', 'none', '', 'na']:
                return 0.0
            
            value_str = value_str.replace(',', '.')
            value_str = value_str.replace(' ', '')
            
            cleaned = re.sub(r'[^\d\.\-]', '', value_str)
            
            if cleaned.count('.') > 1:
                parts = cleaned.split('.')
                cleaned = parts[0] + '.' + ''.join(parts[1:])
            
            if not cleaned or cleaned in ['.', '-', '-.', '']:
                return 0.0
            
            return float(cleaned)
            
        except:
            return 0.0
    
    @classmethod
    def _extract_wilaya(cls, wilaya_str) -> Tuple[int, str]:
        """استخراج رمز الولاية واسمها"""
        wilaya_code = 16
        wilaya_name = "الجزائر"
        
        if pd.isna(wilaya_str):
            return wilaya_code, wilaya_name
        
        try:
            wilaya_str = str(wilaya_str).strip()
            
            code_match = re.search(r'\d+', wilaya_str)
            if code_match:
                code = int(code_match.group())
                if 1 <= code <= 58:
                    wilaya_code = code
                    if code in cls.WILAYA_NAMES:
                        wilaya_name = cls.WILAYA_NAMES[code]
            
            if '-' in wilaya_str:
                parts = wilaya_str.split('-', 1)
                if len(parts) > 1 and parts[1].strip():
                    name = parts[1].strip()
                    name = re.sub(r'[^\w\s\-\.]', '', name)
                    if name:
                        wilaya_name = name
        except:
            pass
        
        return wilaya_code, wilaya_name
    
    @classmethod
    def _extract_commune(cls, commune_str) -> str:
        """استخراج اسم البلدية"""
        if pd.isna(commune_str):
            return "غير محدد"
        
        try:
            commune_str = str(commune_str).strip()
            
            if '-' in commune_str:
                parts = commune_str.split('-', 1)
                if len(parts) > 1 and parts[1].strip():
                    name = parts[1].strip()
                    name = re.sub(r'[^\w\s\-\.]', '', name)
                    return name if name else "غير محدد"
            
            cleaned = re.sub(r'[^\w\s\-\.]', '', commune_str)
            return cleaned if cleaned else "غير محدد"
        except:
            return "غير محدد"
    
    @classmethod
    def _infer_types(cls, type_text, capital_assure):
        """استنتاج نوع المبنى والهيكل"""
        building_type = BuildingType.TYPE_2
        structure_type = StructureType.RC_FRAME
        
        if pd.isna(type_text):
            return building_type, structure_type
        
        try:
            type_text_lower = str(type_text).lower()
            
            if 'industrielle' in type_text_lower or 'installation' in type_text_lower:
                building_type = BuildingType.TYPE_1B
                structure_type = StructureType.STEEL_FRAME
            elif 'commerciale' in type_text_lower:
                building_type = BuildingType.TYPE_2
                structure_type = StructureType.RC_FRAME
            elif 'immobilier' in type_text_lower or 'bien' in type_text_lower:
                building_type = BuildingType.TYPE_1A
                structure_type = StructureType.RC_SHEAR_WALL
            
            # المباني الكبيرة تستحق هيكل أقوى
            if capital_assure > 100:  # > 100 MDA
                structure_type = StructureType.RC_SHEAR_WALL
                
        except:
            pass
        
        return building_type, structure_type
    
    @classmethod
    def _estimate_floors(cls, capital_assure_mda: float, type_text) -> int:
        """
        تقدير عدد الطوابق (باستخدام MDA)
        
        Args:
            capital_assure_mda: رأس المال المؤمن بمليون دينار
            type_text: نص نوع المبنى
        """
        try:
            type_text_lower = str(type_text).lower() if not pd.isna(type_text) else ""
            
            if 'industrielle' in type_text_lower:
                if capital_assure_mda < 10:
                    return 1
                elif capital_assure_mda < 50:
                    return 2
                else:
                    return 3
            
            if capital_assure_mda < 3:
                return 1
            elif capital_assure_mda < 10:
                return 2
            elif capital_assure_mda < 30:
                return 3
            elif capital_assure_mda < 100:
                return 5
            elif capital_assure_mda < 500:
                return 8
            else:
                return 12
        except:
            return 2
    
    @classmethod
    def _infer_soil(cls, wilaya_code) -> str:
        """استنتاج نوع التربة"""
        coastal = [2, 6, 9, 15, 16, 18, 21, 23, 27, 31, 35, 36, 42, 46]
        mountain = [5, 10, 14, 19, 24, 25, 26, 34, 38, 40, 41, 43, 44]
        
        if wilaya_code in coastal:
            return 'S3'
        elif wilaya_code in mountain:
            return 'S1'
        else:
            return 'S2'
    
    @classmethod
    def load_from_excel(
        cls,
        file_path: str,
        sheet_name: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
        batch_size: int = 5000
    ) -> List[RiskProfile]:
        """
        تحميل البيانات من ملف Excel (بوحدة MDA)
        Load Data from Excel File (in MDA unit)
        
        Args:
            file_path: مسار الملف
            sheet_name: اسم الورقة (None للاكتشاف التلقائي)
            progress_callback: دالة تحديث التقدم
            batch_size: حجم الدفعة للمعالجة
        
        Returns:
            قائمة RiskProfile (مع sum_insured بمليون دينار)
        """
        if progress_callback:
            progress_callback(1, "📂 جاري فتح ملف البيانات...")
        
        try:
            if sheet_name is None:
                sheet_name = cls.get_recommended_sheet(file_path)
                if progress_callback:
                    progress_callback(3, f"📋 تم اختيار الورقة: {sheet_name}")
            
            df = pd.read_excel(
                file_path,
                sheet_name=sheet_name,
                engine='openpyxl',
                dtype=str
            )
            
            total_rows = len(df)
            if progress_callback:
                progress_callback(5, f"📊 تم قراءة {total_rows:,} صف. جاري اكتشاف الأعمدة...")
            
            column_mapping = cls._detect_columns(df)
            
            if progress_callback:
                progress_callback(8, f"📊 جاري معالجة {total_rows:,} صف...")
            
            profiles = []
            valid = 0
            zero_capital = 0
            
            batches = (total_rows + batch_size - 1) // batch_size
            
            for batch_num in range(batches):
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, total_rows)
                batch_df = df.iloc[start_idx:end_idx]
                
                for _, row in batch_df.iterrows():
                    try:
                        wilaya_str = row.get(column_mapping.get('wilaya', ''), '')
                        commune_str = row.get(column_mapping.get('commune', ''), '')
                        capital_str = row.get(column_mapping.get('capital', ''), '0')
                        type_str = row.get(column_mapping.get('type', ''), '')
                        
                        wilaya_code, wilaya_name = cls._extract_wilaya(wilaya_str)
                        commune_name = cls._extract_commune(commune_str)
                        
                        # تنظيف وتحويل رأس المال إلى مليون دينار (MDA)
                        capital_dzd = cls._clean_numeric(capital_str)
                        capital_mda = cls.convert_to_mda(capital_dzd)
                        
                        if capital_mda <= 0:
                            zero_capital += 1
                            continue
                        
                        building_type, structure_type = cls._infer_types(type_str, capital_mda)
                        floors = cls._estimate_floors(capital_mda, type_str)
                        soil = cls._infer_soil(wilaya_code)
                        
                        profile = RiskProfile(
                            wilaya_code=wilaya_code,
                            wilaya_name=wilaya_name,
                            commune_name=commune_name,
                            building_age=15,
                            number_of_floors=floors,
                            structure_type=structure_type,
                            building_type=building_type,
                            sum_insured=capital_mda,  # التخزين بـ MDA
                            soil_type=soil
                        )
                        
                        profiles.append(profile)
                        valid += 1
                        
                    except Exception:
                        continue
                
                if progress_callback:
                    progress = 10 + int((end_idx / total_rows) * 80)
                    progress_callback(
                        progress,
                        f"📊 دفعة {batch_num + 1}/{batches} | صالح: {valid:,} | رأس مال صفر: {zero_capital:,}"
                    )
            
            if progress_callback:
                progress_callback(95, f"✅ اكتملت المعالجة | صالح: {valid:,}")
            
            if valid == 0:
                raise ValueError(f"لم يتم العثور على أي بوليصة صالحة (رأس مال صفر: {zero_capital:,})")
            
            return profiles
            
        except Exception as e:
            raise Exception(f"خطأ في تحميل البيانات: {str(e)}")
    
    @classmethod
    def get_statistics(cls, profiles: List[RiskProfile]) -> Dict[str, Any]:
        """الحصول على إحصائيات البيانات المحملة"""
        if not profiles:
            return {}
        
        total_insured_mda = sum(p.sum_insured for p in profiles)
        total_insured_dzd = cls.convert_from_mda(total_insured_mda)
        
        wilaya_counts = {}
        for p in profiles:
            wilaya_counts[p.wilaya_name] = wilaya_counts.get(p.wilaya_name, 0) + 1
        
        building_type_counts = {}
        for p in profiles:
            bt = p.building_type.name
            building_type_counts[bt] = building_type_counts.get(bt, 0) + 1
        
        return {
            'total_policies': len(profiles),
            'total_insured_mda': total_insured_mda,
            'total_insured_dzd': total_insured_dzd,
            'avg_insured_mda': total_insured_mda / len(profiles) if profiles else 0,
            'wilaya_distribution': dict(sorted(wilaya_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            'building_type_distribution': building_type_counts,
        }