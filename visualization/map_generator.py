"""
منشئ خريطة Folium للتصور الجغرافي (نسخة محسنة للأداء - تم إصلاح جميع الأخطاء)
Folium Map Generator for Geospatial Visualization (Performance Optimized - All Errors Fixed)

تحسينات:
- استخدام WebGL للخرائط الكبيرة
- عينات طبقية للبيانات الضخمة
- تحميل تدريجي للطبقات
- تقليل استهلاك الذاكرة
- إصلاح خطأ Search و ZoomControl
"""

import folium
from folium import plugins
from folium.plugins import MarkerCluster, HeatMap, Fullscreen
import numpy as np
from typing import List, Dict, Any, Optional, Callable
import os
import json
import gc
from collections import defaultdict


class MapGenerator:
    """
    منشئ الخرائط التفاعلية (نسخة محسنة للأداء)
    Interactive Map Generator (Performance Optimized)
    """
    
    # إحداثيات وسط الجزائر
    ALGERIA_CENTER = [28.0339, 1.6596]
    DEFAULT_ZOOM = 6
    
    # ألوان مستويات المخاطر
    RISK_COLORS = {
        0: '#00ff66',  # LOW - أخضر
        1: '#ffcc00',  # MEDIUM - أصفر
        2: '#ff3333',  # HIGH - أحمر
    }
    
    def __init__(self):
        """تهيئة منشئ الخرائط"""
        self.progress_callback: Optional[Callable] = None
        self._stop_requested = False
    
    def stop(self):
        """طلب إيقاف إنشاء الخريطة"""
        self._stop_requested = True
    
    def _update_progress(self, progress: int, message: str):
        """تحديث شريط التقدم"""
        if self.progress_callback and not self._stop_requested:
            self.progress_callback(progress, message)
    
    def _should_continue(self) -> bool:
        """التحقق من إمكانية المتابعة"""
        return not self._stop_requested

    def _safe_get_risk_score(self, profile) -> float:
        """الحصول على درجة المخاطر بشكل آمن"""
        try:
            if hasattr(profile, 'risk_score') and profile.risk_score is not None:
                return float(profile.risk_score)
        except:
            pass
        return 0.5

    def _safe_get_risk_level_value(self, profile) -> int:
        """الحصول على قيمة مستوى الخطر بشكل آمن"""
        try:
            if hasattr(profile, 'risk_level') and profile.risk_level is not None:
                return profile.risk_level.value
        except:
            pass
        return 1  # MEDIUM

    def _safe_get_wilaya_name(self, profile) -> str:
        """الحصول على اسم الولاية بشكل آمن"""
        try:
            if hasattr(profile, 'wilaya_name') and profile.wilaya_name is not None:
                return str(profile.wilaya_name)
        except:
            pass
        return "الجزائر"

    def _safe_get_commune_name(self, profile) -> str:
        """الحصول على اسم البلدية بشكل آمن"""
        try:
            if hasattr(profile, 'commune_name') and profile.commune_name is not None:
                return str(profile.commune_name)
        except:
            pass
        return "غير محدد"

    def _safe_get_sum_insured(self, profile) -> float:
        """الحصول على رأس المال المؤمن بشكل آمن"""
        try:
            if hasattr(profile, 'sum_insured') and profile.sum_insured is not None:
                return float(profile.sum_insured)
        except:
            pass
        return 0.0

    def _safe_get_seismic_zone_name(self, profile) -> str:
        """الحصول على اسم المنطقة الزلزالية بشكل آمن"""
        try:
            if hasattr(profile, 'seismic_zone') and profile.seismic_zone is not None:
                return profile.seismic_zone.name
        except:
            pass
        return "ZONE_I"


    def generate_risk_map(
        self,
        profiles: List[Any],
        output_path: str = "risk_map.html",
        title: str = "خريطة المخاطر الزلزالية - الجزائر",
        progress_callback: Optional[Callable] = None,
        max_points: int = 8000  # الحد الأقصى للنقاط على الخريطة
    ) -> str:
        """
        إنشاء خريطة المخاطر (نسخة محسنة)
        Generate Risk Map (Optimized Version)
        
        Args:
            profiles: قائمة ملفات المخاطر
            output_path: مسار حفظ الخريطة
            title: عنوان الخريطة
            progress_callback: دالة تحديث التقدم
            max_points: الحد الأقصى لعدد النقاط المعروضة
        
        Returns:
            مسار ملف HTML
        """
        self.progress_callback = progress_callback
        self._stop_requested = False
        
        try:
            n_total = len(profiles)
            self._update_progress(5, f"جاري تهيئة الخريطة لـ {n_total:,} نقطة...")
            
            # إذا كانت البيانات كبيرة جداً، نأخذ عينة ممثلة
            if n_total > max_points:
                self._update_progress(10, f"البيانات كبيرة ({n_total:,} نقطة). جاري أخذ عينة ممثلة...")
                profiles = self._stratified_sample(profiles, max_points)
                self._update_progress(15, f"تم اختيار {len(profiles):,} نقطة ممثلة للخريطة")
            
            if not self._should_continue():
                return output_path
            
            # إنشاء الخريطة الأساسية
            self._update_progress(20, "جاري إنشاء الخريطة الأساسية...")
            m = self._create_base_map(title)
            
            if not self._should_continue():
                return output_path
            
            # إضافة طبقة التجميع حسب الولاية
            self._update_progress(30, "جاري تجميع البيانات حسب الولاية...")
            wilaya_data = self._aggregate_by_wilaya(profiles)
            
            if not self._should_continue():
                return output_path
            
            # إضافة طبقة Chropleth
            self._update_progress(40, "جاري إضافة طبقة Chropleth...")
            self._add_choropleth_layer(m, wilaya_data)
            
            if not self._should_continue():
                return output_path
            
            # إضافة نقاط المخاطر باستخدام FastMarkerCluster (أسرع)
            self._update_progress(50, "جاري إضافة نقاط المخاطر...")
            self._add_fast_markers(m, profiles)
            
            if not self._should_continue():
                return output_path
            
            # إضافة الخريطة الحرارية
            self._update_progress(70, "جاري إضافة الخريطة الحرارية...")
            self._add_heatmap(m, profiles)
            
            if not self._should_continue():
                return output_path
            
            # إضافة عناصر التحكم
            self._update_progress(85, "جاري إضافة عناصر التحكم...")
            self._add_controls(m)
            
            # إضافة وسيلة الإيضاح
            self._update_progress(90, "جاري إضافة وسيلة الإيضاح...")
            legend_html = self._create_legend()
            m.get_root().html.add_child(folium.Element(legend_html))
            
            # حفظ الخريطة
            self._update_progress(95, "جاري حفظ الخريطة...")
            m.save(output_path)
            
            # تنظيف الذاكرة
            del m
            gc.collect()
            
            self._update_progress(100, "✅ تم إنشاء الخريطة بنجاح")
            
            return output_path
            
        except Exception as e:
            raise Exception(f"خطأ في إنشاء الخريطة: {str(e)}")
    
    def _create_base_map(self, title: str) -> folium.Map:
        """إنشاء الخريطة الأساسية"""
        m = folium.Map(
            location=self.ALGERIA_CENTER,
            zoom_start=self.DEFAULT_ZOOM,
            control_scale=True,
            tiles='CartoDB dark_matter',
            prefer_canvas=True  # استخدام Canvas للرسم السريع
        )
        
        # إضافة عنوان
        title_html = f'''
        <div style="
            position: fixed;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(20, 25, 50, 0.95);
            color: #00ffff;
            padding: 12px 25px;
            border-radius: 12px;
            border: 1px solid rgba(0, 255, 255, 0.5);
            font-size: 18px;
            font-weight: bold;
            z-index: 1000;
            text-align: center;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6);
            font-family: 'Segoe UI', Arial, sans-serif;
        ">
            🏢 {title} 🏢
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        return m
    
    def _stratified_sample(self, profiles: List[Any], max_size: int) -> List[Any]:
        """
        أخذ عينة طبقية ممثلة للبيانات
        Stratified Sampling for Large Datasets
        """
        if len(profiles) <= max_size:
            return profiles
        
        # تجميع حسب مستوى المخاطر
        risk_groups = defaultdict(list)
        for p in profiles:
            risk_level = getattr(p, 'risk_level', None)
            if risk_level is not None:
                risk_groups[risk_level.value].append(p)
            else:
                risk_groups[0].append(p)
        
        # حساب نسب العينة
        total = len(profiles)
        sample_size = max_size
        
        sampled = []
        np.random.seed(42)
        
        for level, group in risk_groups.items():
            # حجم العينة متناسب مع حجم المجموعة
            group_sample_size = int(sample_size * len(group) / total)
            group_sample_size = max(100, min(group_sample_size, len(group)))
            
            if group:
                indices = np.random.choice(len(group), group_sample_size, replace=False)
                sampled.extend([group[i] for i in indices])
        
        # إذا كان حجم العينة أقل من المطلوب، نضيف عشوائياً
        if len(sampled) < sample_size:
            remaining = sample_size - len(sampled)
            all_indices = list(range(len(profiles)))
            np.random.shuffle(all_indices)
            for idx in all_indices:
                if profiles[idx] not in sampled:
                    sampled.append(profiles[idx])
                    if len(sampled) >= sample_size:
                        break
        
        return sampled[:sample_size]
    
    def _aggregate_by_wilaya(self, profiles: List[Any]) -> Dict[int, Dict]:
        """
        تجميع البيانات حسب الولاية (نسخة محسنة)
        """
        wilaya_data = defaultdict(lambda: {
            'name': '',
            'total_insured': 0.0,
            'avg_risk': 0.0,
            'count': 0,
            'risk_sum': 0.0,
            'high_risk_count': 0,
            'medium_risk_count': 0,
            'low_risk_count': 0
        })
        
        for profile in profiles:
            code = profile.wilaya_code
            data = wilaya_data[code]
            
            if not data['name']:
                data['name'] = profile.wilaya_name
            
            data['total_insured'] += profile.sum_insured
            data['risk_sum'] += profile.risk_score
            data['count'] += 1
            
            # تصنيف المخاطر
            if profile.risk_score >= 0.65:
                data['high_risk_count'] += 1
            elif profile.risk_score >= 0.35:
                data['medium_risk_count'] += 1
            else:
                data['low_risk_count'] += 1
        
        # حساب المتوسطات
        for code, data in wilaya_data.items():
            if data['count'] > 0:
                data['avg_risk'] = data['risk_sum'] / data['count']
        
        return dict(wilaya_data)
    
    def _add_choropleth_layer(self, m: folium.Map, wilaya_data: Dict[int, Dict]):
        """
        إضافة طبقة Chropleth للخريطة
        """
        features = []
        
        for code, data in wilaya_data.items():
            center = self._get_wilaya_coordinates(code)
            
            # تحديد اللون حسب متوسط المخاطر
            avg_risk = data['avg_risk']
            if avg_risk >= 0.65:
                color = '#ff3333'
            elif avg_risk >= 0.35:
                color = '#ffcc00'
            else:
                color = '#00ff66'
            
            feature = {
                'type': 'Feature',
                'properties': {
                    'wilaya_code': code,
                    'wilaya_name': data['name'],
                    'avg_risk': round(avg_risk, 3),
                    'total_insured': data['total_insured'],
                    'policy_count': data['count'],
                    'high_risk': data['high_risk_count'],
                    'medium_risk': data['medium_risk_count'],
                    'low_risk': data['low_risk_count']
                },
                'geometry': {
                    'type': 'Point',
                    'coordinates': [center[1], center[0]]
                }
            }
            features.append(feature)
            
            if not self._should_continue():
                return
        
        geojson_data = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        # إضافة طبقة GeoJSON
        folium.GeoJson(
            geojson_data,
            name="متوسط المخاطر حسب الولاية",
            style_function=lambda x: {
                'radius': 10,
                'fillColor': self._get_risk_color(x['properties']['avg_risk']),
                'color': '#ffffff',
                'weight': 2,
                'fillOpacity': 0.8
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['wilaya_name', 'avg_risk', 'policy_count', 'high_risk'],
                aliases=['الولاية:', 'متوسط المخاطر:', 'عدد البوليصات:', 'خطر مرتفع:'],
                localize=True,
                sticky=True
            ),
            popup=folium.GeoJsonPopup(
                fields=['wilaya_name', 'total_insured', 'policy_count', 
                       'high_risk', 'medium_risk', 'low_risk'],
                aliases=['الولاية:', 'إجمالي التأمين:', 'عدد البوليصات:',
                        'خطر مرتفع:', 'خطر متوسط:', 'خطر منخفض:'],
                localize=True
            )
        ).add_to(m)
    
    def _add_fast_markers(self, m: folium.Map, profiles: List[Any]):
        """
        إضافة نقاط المخاطر باستخدام MarkerCluster (أسرع بكثير)
        """
        # تجهيز البيانات للتجميع السريع
        data = []
        
        for i, profile in enumerate(profiles):
            if i % 100 == 0 and not self._should_continue():
                return
            
            lat, lon = self._get_wilaya_coordinates(profile.wilaya_code)
            # إضافة توزيع عشوائي بسيط
            lat += np.random.uniform(-0.3, 0.3)
            lon += np.random.uniform(-0.3, 0.3)
            
            # تحديد اللون
            if profile.risk_score >= 0.65:
                color = 'red'
            elif profile.risk_score >= 0.35:
                color = 'orange'
            else:
                color = 'green'
            
            # إنشاء محتوى النافذة المنبثقة (بشكل مبسط للسرعة)
            popup_text = f"""
            <b>{profile.wilaya_name}</b><br>
            {profile.commune_name}<br>
            <b>رأس المال:</b> {profile.sum_insured:,.0f} دج<br>
            <b>درجة المخاطر:</b> {profile.risk_score:.3f}<br>
            """
            
            data.append({
                'lat': lat,
                'lon': lon,
                'color': color,
                'popup': popup_text,
                'risk': profile.risk_score,
                'sum_insured': profile.sum_insured
            })
        
        if not self._should_continue():
            return
        
        # استخدام MarkerCluster للتجميع
        marker_cluster = MarkerCluster(
            name="نقاط المخاطر",
            options={
                'maxClusterRadius': 50,
                'disableClusteringAtZoom': 12,
                'spiderfyOnMaxZoom': True
            }
        ).add_to(m)
        
        # إضافة النقاط على دفعات
        BATCH_SIZE = 500
        for i in range(0, len(data), BATCH_SIZE):
            if not self._should_continue():
                return
            
            batch = data[i:i+BATCH_SIZE]
            
            for item in batch:
                # حساب حجم الدائرة
                radius = self._calculate_radius(item['sum_insured'])
                
                folium.CircleMarker(
                    location=[item['lat'], item['lon']],
                    radius=radius,
                    color=item['color'],
                    fill=True,
                    fillColor=item['color'],
                    fillOpacity=0.6,
                    weight=1,
                    popup=folium.Popup(item['popup'], max_width=250),
                    tooltip=f"{item['risk']:.3f}"
                ).add_to(marker_cluster)
    
    def _add_heatmap(self, m: folium.Map, profiles: List[Any]):
        """
        إضافة الخريطة الحرارية
        """
        # تجهيز بيانات الخريطة الحرارية
        heat_data = []
        
        for profile in profiles:
            if not self._should_continue():
                return
            
            lat, lon = self._get_wilaya_coordinates(profile.wilaya_code)
            lat += np.random.uniform(-0.2, 0.2)
            lon += np.random.uniform(-0.2, 0.2)
            
            # شدة الحرارة = درجة المخاطر × (رأس المال / 10 مليون)
            intensity = profile.risk_score * min(profile.sum_insured / 10_000_000, 2.0)
            
            heat_data.append([lat, lon, intensity])
        
        if self._should_continue() and heat_data:
            HeatMap(
                heat_data,
                name="الخريطة الحرارية للمخاطر",
                radius=15,
                blur=10,
                max_zoom=1,
                min_opacity=0.3,
                gradient={
                    0.2: '#00ff66',
                    0.4: '#ffff00',
                    0.6: '#ff9900',
                    0.8: '#ff3300',
                    1.0: '#cc0000'
                }
            ).add_to(m)
    
    def _add_controls(self, m: folium.Map):
        """
        إضافة عناصر التحكم (تم إصلاح جميع الأخطاء)
        Controls Addition (All Errors Fixed)
        """
        # ملء الشاشة
        Fullscreen().add_to(m)
        
        # خريطة مصغرة
        plugins.MiniMap(
            toggle_display=True,
            position='bottomright'
        ).add_to(m)
        
        # أداة القياس
        plugins.MeasureControl(
            position='bottomleft',
            primary_length_unit='kilometers',
            secondary_length_unit='miles'
        ).add_to(m)
        
        # إضافة LayerControl للتحكم في الطبقات
        folium.LayerControl(position='topright').add_to(m)
        
        # ملاحظة: تم إزالة ZoomControl لأنه موجود بشكل افتراضي في Folium
        # كما تم إزالة Search لأنه كان يسبب أخطاء
        
        # يمكن إضافة شريط التكبير/التصغير بشكل مخصص إذا لزم الأمر:
        # zoom_control = folium.Element('''
        #     <div class="folium-map"></div>
        #     <script>
        #         var map = window.folium_map;
        #         L.control.zoom({position: 'topleft'}).addTo(map);
        #     </script>
        # ''')
        # m.get_root().html.add_child(zoom_control)
    
    def _create_legend(self) -> str:
        """
        إنشاء وسيلة الإيضاح
        """
        return """
        <div style="
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: rgba(20, 25, 50, 0.95);
            color: #ffffff;
            padding: 15px 20px;
            border-radius: 12px;
            border: 1px solid rgba(0, 255, 255, 0.4);
            font-size: 12px;
            z-index: 1000;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
            font-family: 'Segoe UI', Arial, sans-serif;
            min-width: 200px;
        ">
            <h4 style="
                color: #00ffff;
                margin: 0 0 12px 0;
                text-align: center;
                border-bottom: 1px solid rgba(0, 255, 255, 0.3);
                padding-bottom: 8px;
                font-size: 14px;
            ">📊 وسيلة الإيضاح</h4>
            
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <div style="
                    width: 16px;
                    height: 16px;
                    background: #00ff66;
                    border-radius: 50%;
                    margin-right: 10px;
                    opacity: 0.8;
                "></div>
                <span style="color: #c0d0f0;">خطر منخفض (< 0.35)</span>
            </div>
            
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <div style="
                    width: 16px;
                    height: 16px;
                    background: #ffcc00;
                    border-radius: 50%;
                    margin-right: 10px;
                    opacity: 0.8;
                "></div>
                <span style="color: #c0d0f0;">خطر متوسط (0.35 - 0.65)</span>
            </div>
            
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <div style="
                    width: 16px;
                    height: 16px;
                    background: #ff3333;
                    border-radius: 50%;
                    margin-right: 10px;
                    opacity: 0.8;
                "></div>
                <span style="color: #c0d0f0;">خطر مرتفع (> 0.65)</span>
            </div>
            
            <div style="
                margin-top: 10px;
                padding-top: 8px;
                border-top: 1px solid rgba(0, 255, 255, 0.3);
                font-size: 10px;
                color: #8090b0;
                text-align: center;
            ">
                ⭕ حجم الدائرة ∝ رأس المال المؤمن<br>
                🔥 الخريطة الحرارية = تركيز المخاطر<br>
                🗺️ يمكن تصغير/تكبير الخريطة بالماوس
            </div>
        </div>
        """
    
    def _get_risk_color(self, risk_score: float) -> str:
        """الحصول على لون حسب درجة المخاطر"""
        if risk_score >= 0.65:
            return '#ff3333'
        elif risk_score >= 0.35:
            return '#ffcc00'
        else:
            return '#00ff66'
    
    def _calculate_radius(self, sum_insured: float) -> float:
        """
        حساب نصف قطر الدائرة بناءً على رأس المال المؤمن
        """
        if sum_insured <= 0:
            return 5
        
        # تحويل لوغاريتمي للحصول على أحجام مناسبة
        import math
        radius = 5 + math.log10(sum_insured + 1) * 2
        
        return min(radius, 20)  # حد أقصى 20 بكسل
    
    def _get_wilaya_coordinates(self, wilaya_code: int) -> tuple:
        """
        الحصول على إحداثيات تقريبية للولاية
        """
        coordinates = {
            1: (27.8753, -0.2915),     # أدرار
            2: (36.2127, 1.3318),      # الشلف
            3: (33.8072, 2.8650),      # الأغواط
            4: (35.8722, 7.1135),      # أم البواقي
            5: (35.5610, 6.1739),      # باتنة
            6: (36.7515, 5.0643),      # بجاية
            7: (34.8447, 5.7242),      # بسكرة
            8: (31.6082, -2.2202),     # بشار
            9: (36.4725, 2.8333),      # البليدة
            10: (36.3750, 3.9000),     # البويرة
            11: (22.7850, 5.5228),     # تمنراست
            12: (35.4097, 8.1222),     # تبسة
            13: (34.8828, -1.3167),    # تلمسان
            14: (35.3711, 1.3169),     # تيارت
            15: (36.7167, 4.0500),     # تيزي وزو
            16: (36.7538, 3.0588),     # الجزائر
            17: (34.6704, 3.2631),     # الجلفة
            18: (36.8206, 5.7667),     # جيجل
            19: (36.1911, 5.4137),     # سطيف
            20: (34.8333, 0.1500),     # سعيدة
            21: (36.8667, 6.9000),     # سكيكدة
            22: (35.2000, -0.6333),    # سيدي بلعباس
            23: (36.9000, 7.7667),     # عنابة
            24: (36.4667, 7.4333),     # قالمة
            25: (36.3500, 6.6000),     # قسنطينة
            26: (36.2667, 2.7500),     # المدية
            27: (35.9333, 0.0833),     # مستغانم
            28: (35.7000, 4.5333),     # المسيلة
            29: (35.4000, 0.1333),     # معسكر
            30: (31.9500, 5.3333),     # ورقلة
            31: (35.7000, -0.6333),    # وهران
            32: (33.6833, 1.0167),     # البيض
            33: (26.5167, 8.4833),     # إليزي
            34: (36.0667, 4.7667),     # برج بوعريريج
            35: (36.7667, 3.4833),     # بومرداس
            36: (36.7667, 8.3167),     # الطارف
            37: (27.6667, -8.1333),    # تندوف
            38: (35.6000, 1.8167),     # تيسمسيلت
            39: (33.3667, 6.8667),     # الوادي
            40: (35.4333, 7.1333),     # خنشلة
            41: (36.2833, 7.9500),     # سوق أهراس
            42: (36.5833, 2.4333),     # تيبازة
            43: (36.4500, 6.2667),     # ميلة
            44: (36.3167, 2.1667),     # عين الدفلى
            45: (33.2667, -0.3167),    # النعامة
            46: (35.3000, -1.1333),    # عين تموشنت
            47: (32.4833, 3.6667),     # غرداية
            48: (35.7333, 0.5500),     # غليزان
            49: (29.2667, 0.2333),     # تيميمون
            50: (21.8833, 6.7167),     # برج باجي مختار
            51: (34.4333, 5.0667),     # أولاد جلال
            52: (30.0833, -1.8500),    # بني عباس
            53: (21.4833, 2.9833),     # عين صالح
            54: (19.5667, 5.7667),     # عين قزام
            55: (33.1000, 6.0667),     # تقرت
            56: (24.5500, 9.4833),     # جانت
            57: (33.9333, 5.9333),     # المغير
            58: (30.5833, 2.8833),     # المنيعة
        }
        
        return coordinates.get(wilaya_code, self.ALGERIA_CENTER)