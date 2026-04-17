"""
خيوط العمل لمنع تجميد الواجهة (نسخة محسنة كاملة)
Background Workers to Prevent UI Freezing (Full Optimized Version)
"""

from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition
from typing import List, Optional, Callable
import pandas as pd
import numpy as np
import gc
import re

from core.risk_models import RiskProfile, PortfolioSummary, StructureType, BuildingType
from core.rpa_classifier import CatBoostRiskModel, RPAClassifier
from core.monte_carlo import MonteCarloSimulator


class DataLoaderWorker(QThread):
    """
    خيط تحميل البيانات (نسخة محسنة)
    Data Loading Worker Thread (Optimized)
    """
    
    progress_updated = pyqtSignal(int, str)
    data_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    # قاموس الولايات الجزائرية
    WILAYA_NAMES = {
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
    
    def __init__(self, file_path: str, sheet_name: str = None):
        super().__init__()
        self.file_path = file_path
        self.sheet_name = sheet_name  # None يعني اكتشاف تلقائي
        self._is_paused = False
        self._is_stopped = False
        self.mutex = QMutex()
        self.pause_condition = QWaitCondition()
    
    def _detect_sheet_name(self) -> str:
        """
        اكتشاف اسم الورقة تلقائياً
        Auto-detect Sheet Name
        """
        try:
            # قراءة أسماء الأوراق المتاحة
            xl_file = pd.ExcelFile(self.file_path, engine='openpyxl')
            available_sheets = xl_file.sheet_names
            
            self.progress_updated.emit(2, f"📋 الأوراق المتاحة: {', '.join(available_sheets)}")
            
            if not available_sheets:
                raise ValueError("لم يتم العثور على أي ورقة في الملف")
            
            # البحث عن ورقة تحتوي على بيانات (حسب الأولوية)
            priority_keywords = ['2023', '2024', '2025', 'data', 'Data', 'Sheet1', 'Feuil1']
            
            for keyword in priority_keywords:
                for sheet in available_sheets:
                    if keyword.lower() in sheet.lower():
                        self.progress_updated.emit(3, f"✅ تم اختيار الورقة: {sheet}")
                        return sheet
            
            # إذا لم نجد أي من الكلمات المفتاحية، نستخدم الورقة الأولى
            first_sheet = available_sheets[0]
            self.progress_updated.emit(3, f"✅ تم اختيار الورقة الأولى: {first_sheet}")
            return first_sheet
            
        except Exception as e:
            raise Exception(f"خطأ في قراءة أسماء الأوراق: {str(e)}")
    
    def _get_column_mapping(self, df: pd.DataFrame) -> dict:
        """
        اكتشاف أسماء الأعمدة تلقائياً
        Auto-detect Column Names
        """
        columns = df.columns.tolist()
        mapping = {}
        
        # البحث عن عمود الولاية
        wilaya_keywords = ['WILAYA', 'wilaya', 'WILAYA_CODE', 'CODE_WILAYA', 'ولاية']
        for col in columns:
            for kw in wilaya_keywords:
                if kw.lower() in col.lower():
                    mapping['wilaya'] = col
                    break
            if 'wilaya' in mapping:
                break
        
        # البحث عن عمود البلدية
        commune_keywords = ['COMMUNE', 'commune', 'COMMUNE_NAME', 'بلدية']
        for col in columns:
            for kw in commune_keywords:
                if kw.lower() in col.lower():
                    mapping['commune'] = col
                    break
            if 'commune' in mapping:
                break
        
        # البحث عن عمود رأس المال
        capital_keywords = ['CAPITAL', 'capital', 'ASSURE', 'assure', 'SUM_INSURED', 'مؤمن']
        for col in columns:
            for kw in capital_keywords:
                if kw.lower() in col.lower():
                    mapping['capital'] = col
                    break
            if 'capital' in mapping:
                break
        
        # البحث عن عمود النوع
        type_keywords = ['TYPE', 'type', 'BRANCHE', 'نوع']
        for col in columns:
            for kw in type_keywords:
                if kw.lower() in col.lower():
                    mapping['type'] = col
                    break
            if 'type' in mapping:
                break
        
        # البحث عن عمود القسط
        prime_keywords = ['PRIME', 'prime', 'PREMIUM', 'قسط']
        for col in columns:
            for kw in prime_keywords:
                if kw.lower() in col.lower():
                    mapping['prime'] = col
                    break
            if 'prime' in mapping:
                break
        
        # البحث عن عمود التاريخ
        date_keywords = ['DATE', 'date', 'EFFET', 'effet', 'EFFECT', 'تاريخ']
        for col in columns:
            for kw in date_keywords:
                if kw.lower() in col.lower():
                    mapping['date'] = col
                    break
            if 'date' in mapping:
                break
        
        # إذا لم نجد بعض الأعمدة، نستخدم افتراضيات
        if 'wilaya' not in mapping and len(columns) > 0:
            mapping['wilaya'] = columns[0]
        if 'commune' not in mapping and len(columns) > 1:
            mapping['commune'] = columns[1]
        if 'capital' not in mapping and len(columns) > 2:
            mapping['capital'] = columns[2]
        if 'type' not in mapping and len(columns) > 3:
            mapping['type'] = columns[3]
        
        self.progress_updated.emit(4, f"📊 تم اكتشاف الأعمدة: {list(mapping.keys())}")
        
        return mapping
    
    def _clean_numeric(self, value) -> float:
        """تنظيف القيم الرقمية"""
        if pd.isna(value):
            return 0.0
        
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            value_str = str(value).strip()
            
            if not value_str or value_str.lower() in ['nan', 'null', 'none', '', 'na']:
                return 0.0
            
            # استبدال الفاصلة العشرية بنقطة
            value_str = value_str.replace(',', '.')
            value_str = value_str.replace(' ', '')
            
            # إزالة الرموز غير الرقمية
            cleaned = re.sub(r'[^\d\.\-]', '', value_str)
            
            if cleaned.count('.') > 1:
                parts = cleaned.split('.')
                cleaned = parts[0] + '.' + ''.join(parts[1:])
            
            if cleaned.startswith('-'):
                pass
            elif '-' in cleaned:
                cleaned = cleaned.replace('-', '')
            
            if not cleaned or cleaned in ['.', '-', '-.', '']:
                return 0.0
            
            return float(cleaned)
            
        except:
            return 0.0
    
    def _extract_wilaya(self, wilaya_str) -> tuple:
        """استخراج رمز الولاية واسمها"""
        wilaya_code = 16
        wilaya_name = "الجزائر"
        
        if pd.isna(wilaya_str):
            return wilaya_code, wilaya_name
        
        try:
            wilaya_str = str(wilaya_str).strip()
            
            # محاولة استخراج الرقم أولاً
            code_match = re.search(r'\d+', wilaya_str)
            if code_match:
                code = int(code_match.group())
                if 1 <= code <= 58:  # رموز الولايات الجزائرية
                    wilaya_code = code
                    if code in self.WILAYA_NAMES:
                        wilaya_name = self.WILAYA_NAMES[code]
            
            # استخراج الاسم بعد الشرطة
            if '-' in wilaya_str:
                parts = wilaya_str.split('-', 1)
                if len(parts) > 1 and parts[1].strip():
                    name = parts[1].strip()
                    # تنظيف الاسم
                    name = re.sub(r'[^\w\s\-\.]', '', name)
                    if name:
                        wilaya_name = name
        except:
            pass
        
        return wilaya_code, wilaya_name
    
    def _extract_commune(self, commune_str) -> str:
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
    
    def _infer_types(self, type_text, capital_assure):
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
            
            if capital_assure > 100_000_000:
                structure_type = StructureType.RC_SHEAR_WALL
                
        except:
            pass
        
        return building_type, structure_type
    
    def _estimate_floors(self, capital_assure, type_text) -> int:
        """تقدير عدد الطوابق"""
        try:
            type_text_lower = str(type_text).lower() if not pd.isna(type_text) else ""
            
            if 'industrielle' in type_text_lower:
                if capital_assure < 10_000_000:
                    return 1
                elif capital_assure < 50_000_000:
                    return 2
                else:
                    return 3
            
            if capital_assure < 3_000_000:
                return 1
            elif capital_assure < 10_000_000:
                return 2
            elif capital_assure < 30_000_000:
                return 3
            elif capital_assure < 100_000_000:
                return 5
            elif capital_assure < 500_000_000:
                return 8
            else:
                return 12
        except:
            return 2
    
    def _estimate_age(self, row, column_mapping) -> int:
        """تقدير عمر المبنى"""
        try:
            date_col = column_mapping.get('date')
            if date_col:
                date_effet = row.get(date_col)
                if date_effet and pd.notna(date_effet):
                    date_str = str(date_effet)
                    year_match = re.search(r'(\d{4})', date_str)
                    if year_match:
                        year = int(year_match.group(1))
                        age = 2024 - year + 5
                        return max(1, min(age, 60))
        except:
            pass
        return 15
    
    def _infer_soil(self, wilaya_code) -> str:
        """استنتاج نوع التربة"""
        coastal = [2, 6, 9, 15, 16, 18, 21, 23, 27, 31, 35, 36, 42, 46]
        mountain = [5, 10, 14, 19, 24, 25, 26, 34, 38, 40, 41, 43, 44]
        
        if wilaya_code in coastal:
            return 'S3'
        elif wilaya_code in mountain:
            return 'S1'
        else:
            return 'S2'
    
    def run(self):
        """تنفيذ تحميل البيانات"""
        try:
            self.progress_updated.emit(1, "📂 جاري فتح ملف البيانات...")
            
            # اكتشاف اسم الورقة تلقائياً إذا لم يتم تحديده
            if self.sheet_name is None:
                sheet_name = self._detect_sheet_name()
            else:
                sheet_name = self.sheet_name
            
            self.progress_updated.emit(5, f"📄 جاري قراءة الورقة: {sheet_name}...")
            
            # قراءة الملف
            df = pd.read_excel(
                self.file_path,
                sheet_name=sheet_name,
                engine='openpyxl',
                dtype=str
            )
            
            total_rows = len(df)
            self.progress_updated.emit(8, f"📊 تم قراءة {total_rows:,} صف. جاري اكتشاف الأعمدة...")
            
            # اكتشاف أسماء الأعمدة
            column_mapping = self._get_column_mapping(df)
            
            self.progress_updated.emit(10, f"📊 جاري معالجة {total_rows:,} صف...")
            
            profiles = []
            valid = 0
            invalid = 0
            zero_capital = 0
            
            BATCH_SIZE = 5000
            batches = (total_rows + BATCH_SIZE - 1) // BATCH_SIZE
            
            for batch_num in range(batches):
                # التحقق من الإيقاف
                self.mutex.lock()
                if self._is_paused:
                    self.pause_condition.wait(self.mutex)
                self.mutex.unlock()
                
                if self._is_stopped:
                    self.progress_updated.emit(0, "⏹️ تم إيقاف التحميل")
                    return
                
                start_idx = batch_num * BATCH_SIZE
                end_idx = min(start_idx + BATCH_SIZE, total_rows)
                batch_df = df.iloc[start_idx:end_idx]
                
                for _, row in batch_df.iterrows():
                    try:
                        # استخراج البيانات باستخدام أسماء الأعمدة المكتشفة
                        wilaya_str = row.get(column_mapping.get('wilaya', ''), '')
                        commune_str = row.get(column_mapping.get('commune', ''), '')
                        capital_str = row.get(column_mapping.get('capital', ''), '0')
                        type_str = row.get(column_mapping.get('type', ''), '')
                        
                        # استخراج الولاية والبلدية
                        wilaya_code, wilaya_name = self._extract_wilaya(wilaya_str)
                        commune_name = self._extract_commune(commune_str)
                        
                        # تنظيف رأس المال المؤمن
                        capital_assure = self._clean_numeric(capital_str)
                        
                        if capital_assure <= 0:
                            zero_capital += 1
                            continue
                        
                        # استنتاج الأنواع
                        building_type, structure_type = self._infer_types(type_str, capital_assure)
                        floors = self._estimate_floors(capital_assure, type_str)
                        age = self._estimate_age(row, column_mapping)
                        soil = self._infer_soil(wilaya_code)
                        
                        profile = RiskProfile(
                            wilaya_code=wilaya_code,
                            wilaya_name=wilaya_name,
                            commune_name=commune_name,
                            building_age=age,
                            number_of_floors=floors,
                            structure_type=structure_type,
                            building_type=building_type,
                            sum_insured=capital_assure,
                            soil_type=soil
                        )
                        
                        profiles.append(profile)
                        valid += 1
                        
                    except Exception:
                        invalid += 1
                        continue
                
                progress = 10 + int((end_idx / total_rows) * 80)
                self.progress_updated.emit(
                    progress,
                    f"📊 دفعة {batch_num + 1}/{batches} | صالح: {valid:,} | رأس مال صفر: {zero_capital:,}"
                )
                
                if batch_num % 3 == 0:
                    gc.collect()
            
            del df
            gc.collect()
            
            if valid == 0:
                self.error_occurred.emit(
                    f"❌ لم يتم العثور على أي بوليصة صالحة\n"
                    f"الورقة المستخدمة: {sheet_name}\n"
                    f"عدد الصفوف الكلي: {total_rows:,}\n"
                    f"رأس مال صفر: {zero_capital:,}"
                )
                return
            
            self.progress_updated.emit(
                95,
                f"✅ اكتملت المعالجة | صالح: {valid:,} | رأس مال صفر: {zero_capital:,} | غير صالح: {invalid:,}"
            )
            self.data_loaded.emit(profiles)
            self.progress_updated.emit(100, f"🎉 تم تحميل {valid:,} بوليصة بنجاح من الورقة: {sheet_name}")
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            self.error_occurred.emit(f"❌ خطأ في تحميل البيانات:\n{str(e)}")
    
    def pause(self):
        self.mutex.lock()
        self._is_paused = True
        self.mutex.unlock()
    
    def resume(self):
        self.mutex.lock()
        self._is_paused = False
        self.pause_condition.wakeAll()
        self.mutex.unlock()
    
    def stop(self):
        self.mutex.lock()
        self._is_stopped = True
        self._is_paused = False
        self.pause_condition.wakeAll()
        self.mutex.unlock()


class RiskAnalysisWorker(QThread):
    """
    خيط تحليل المخاطر (نسخة محسنة)
    Risk Analysis Worker Thread (Optimized)
    """
    
    progress_updated = pyqtSignal(int, str)
    analysis_completed = pyqtSignal(object, object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, profiles: List[RiskProfile], use_vectorized: bool = True):
        super().__init__()
        self.profiles = profiles
        self.use_vectorized = use_vectorized
        self.model = CatBoostRiskModel(use_cache=True)
        self.simulator = MonteCarloSimulator()
        self._is_stopped = False
        self.mutex = QMutex()
    
    def run(self):
        """تنفيذ تحليل المخاطر"""
        try:
            n_profiles = len(self.profiles)
            self.progress_updated.emit(5, f"🔍 جاري تهيئة النموذج لتحليل {n_profiles:,} بوليصة...")
            
            # تحليل المخاطر
            if self.use_vectorized and n_profiles > 5000:
                self._run_vectorized_analysis()
            else:
                self._run_batch_analysis()
            
            if self._is_stopped:
                return
            
            self.progress_updated.emit(70, "📊 جاري حساب توزيع الخسائر (مونت كارلو)...")
            
            # محاكاة مونت كارلو
            if n_profiles > 20000:
                n_simulations = 2000
            elif n_profiles > 10000:
                n_simulations = 3000
            else:
                n_simulations = 5000
            
            self.progress_updated.emit(75, f"🎲 جاري محاكاة {n_simulations} سيناريو...")
            
            if n_profiles > 30000:
                sample_size = min(15000, n_profiles)
                indices = np.random.choice(n_profiles, sample_size, replace=False)
                sample_profiles = [self.profiles[i] for i in indices]
                summary = self.simulator.calculate_portfolio_metrics(sample_profiles, n_simulations)
                scale_factor = n_profiles / sample_size
                summary.total_policies = n_profiles
                summary.total_sum_insured = sum(p.sum_insured for p in self.profiles)
                summary.expected_loss *= scale_factor
                summary.var_95 *= scale_factor
                summary.var_99 *= scale_factor
                summary.tvar_95 *= scale_factor
            else:
                summary = self.simulator.calculate_portfolio_metrics(self.profiles, n_simulations)
            
            if self._is_stopped:
                return
            
            self.progress_updated.emit(95, "📋 جاري تجهيز النتائج النهائية...")
            
            self.model.clear_cache()
            gc.collect()
            
            self.analysis_completed.emit(self.profiles, summary)
            self.progress_updated.emit(100, f"✅ اكتمل تحليل {n_profiles:,} بوليصة بنجاح")
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            self.error_occurred.emit(f"❌ خطأ في تحليل المخاطر:\n{str(e)}")
    
    def _run_vectorized_analysis(self):
        """تحليل متجه سريع"""
        n = len(self.profiles)
        self.progress_updated.emit(15, "⚡ جاري التحليل المتجه للبيانات (Vectorized)...")
        self.model.predict_batch_vectorized(self.profiles)
        self.progress_updated.emit(60, f"✅ تم تحليل {n:,} بوليصة")
    
    def _run_batch_analysis(self):
        """تحليل دفعي"""
        n = len(self.profiles)
        self.progress_updated.emit(15, "📦 جاري التحليل الدفعي للبيانات...")
        
        def progress_cb(progress, message):
            adjusted = 15 + int(progress * 0.55)
            self.progress_updated.emit(adjusted, message)
        
        self.model.predict_batch(self.profiles, progress_cb)
    
    def stop(self):
        self.mutex.lock()
        self._is_stopped = True
        self.mutex.unlock()


class MapGeneratorWorker(QThread):
    """
    خيط إنشاء الخريطة (نسخة محسنة)
    Map Generator Worker Thread (Optimized)
    """
    
    progress_updated = pyqtSignal(int, str)
    map_generated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, profiles: List[RiskProfile], output_path: str):
        super().__init__()
        self.profiles = profiles
        self.output_path = output_path
        self._is_stopped = False
        self.mutex = QMutex()
    
    def run(self):
        """تنفيذ إنشاء الخريطة"""
        try:
            from visualization.map_generator import MapGenerator
            
            n = len(self.profiles)
            self.progress_updated.emit(10, f"🗺️ جاري تهيئة الخريطة لـ {n:,} نقطة...")
            
            generator = MapGenerator()
            
            if n > 10000:
                self.progress_updated.emit(20, f"📊 البيانات كبيرة ({n:,} نقطة). جاري استخدام عينة ممثلة...")
                sample_profiles = self._stratified_sample(self.profiles, 8000)
                self.progress_updated.emit(30, f"✅ تم اختيار {len(sample_profiles):,} نقطة للخريطة")
            else:
                sample_profiles = self.profiles
            
            def progress_cb(progress, message):
                if not self._is_stopped:
                    adjusted = 30 + int(progress * 0.6)
                    self.progress_updated.emit(adjusted, message)
            
            map_path = generator.generate_risk_map(
                sample_profiles,
                self.output_path,
                title="خريطة المخاطر الزلزالية - الجزائر",
                progress_callback=progress_cb
            )
            
            if self._is_stopped:
                return
            
            self.progress_updated.emit(95, "💾 جاري حفظ الخريطة...")
            self.map_generated.emit(map_path)
            self.progress_updated.emit(100, "✅ تم إنشاء الخريطة بنجاح")
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            self.error_occurred.emit(f"❌ خطأ في إنشاء الخريطة:\n{str(e)}")
    
    def _stratified_sample(self, profiles: List[RiskProfile], max_size: int) -> List[RiskProfile]:
        """أخذ عينة طبقية ممثلة"""
        if len(profiles) <= max_size:
            return profiles
        
        low = [p for p in profiles if p.risk_score < 0.35]
        med = [p for p in profiles if 0.35 <= p.risk_score < 0.65]
        high = [p for p in profiles if p.risk_score >= 0.65]
        
        total = len(profiles)
        sample_low = int(max_size * len(low) / total) if low else 0
        sample_med = int(max_size * len(med) / total) if med else 0
        sample_high = max_size - sample_low - sample_med
        
        np.random.seed(42)
        sampled = []
        
        if low and sample_low > 0:
            indices = np.random.choice(len(low), min(sample_low, len(low)), replace=False)
            sampled.extend([low[i] for i in indices])
        if med and sample_med > 0:
            indices = np.random.choice(len(med), min(sample_med, len(med)), replace=False)
            sampled.extend([med[i] for i in indices])
        if high and sample_high > 0:
            indices = np.random.choice(len(high), min(sample_high, len(high)), replace=False)
            sampled.extend([high[i] for i in indices])
        
        return sampled
    
    def stop(self):
        self.mutex.lock()
        self._is_stopped = True
        self.mutex.unlock()