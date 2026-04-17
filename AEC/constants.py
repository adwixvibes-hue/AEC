"""
الثوابت والإعدادات العامة للنظام
"""

# ألوان النظام
class Colors:
    PRIMARY = "#1a237e"
    PRIMARY_LIGHT = "#534bae"
    PRIMARY_DARK = "#000051"
    SECONDARY = "#ff6f00"
    SECONDARY_LIGHT = "#ffa040"
    SECONDARY_DARK = "#c43e00"
    
    # ألوان المخاطر
    RISK_HIGH = "#f44336"
    RISK_MEDIUM = "#ff9800"
    RISK_LOW = "#4caf50"
    
    # ألوان الواجهة
    BACKGROUND = "#f5f5f5"
    SURFACE = "#ffffff"
    ERROR = "#b00020"
    SUCCESS = "#4caf50"
    WARNING = "#ff9800"
    INFO = "#2196f3"
    
    # نص
    TEXT_PRIMARY = "#212121"
    TEXT_SECONDARY = "#757575"
    TEXT_DISABLED = "#9e9e9e"

# المناطق الزلزالية في الجزائر
SEISMIC_ZONES = {
    1: {"name": "الشلف", "risk": 0.90, "zone": "III"},
    2: {"name": "البليدة", "risk": 0.85, "zone": "III"},
    3: {"name": "تيبازة", "risk": 0.80, "zone": "III"},
    4: {"name": "بومرداس", "risk": 0.90, "zone": "III"},
    5: {"name": "تيزي وزو", "risk": 0.75, "zone": "II"},
    6: {"name": "بجاية", "risk": 0.70, "zone": "II"},
    7: {"name": "جيجل", "risk": 0.65, "zone": "II"},
    8: {"name": "سكيكدة", "risk": 0.60, "zone": "II"},
    9: {"name": "عنابة", "risk": 0.50, "zone": "I"},
    10: {"name": "الجزائر", "risk": 0.70, "zone": "II"},
    11: {"name": "البويرة", "risk": 0.65, "zone": "II"},
    12: {"name": "المدية", "risk": 0.60, "zone": "II"},
    13: {"name": "عين الدفلى", "risk": 0.70, "zone": "II"},
    14: {"name": "مستغانم", "risk": 0.55, "zone": "II"},
    15: {"name": "وهران", "risk": 0.45, "zone": "I"},
    16: {"name": "باتنة", "risk": 0.50, "zone": "I"},
    17: {"name": "بسكرة", "risk": 0.35, "zone": "I"},
    18: {"name": "سطيف", "risk": 0.55, "zone": "II"},
    19: {"name": "قسنطينة", "risk": 0.50, "zone": "I"},
    20: {"name": "تامنراست", "risk": 0.30, "zone": "I"},
    21: {"name": "تبسة", "risk": 0.40, "zone": "I"},
    22: {"name": "تيارت", "risk": 0.50, "zone": "II"},
}

# إحداثيات الولايات الجزائرية
WILAYA_COORDINATES = {
    "الجزائر": (36.7538, 3.0588),
    "وهران": (35.6969, -0.6331),
    "قسنطينة": (36.3650, 6.6147),
    "عنابة": (36.9000, 7.7667),
    "البليدة": (36.4722, 2.8333),
    "بومرداس": (36.7667, 3.4772),
    "تيبازة": (36.5833, 2.4333),
    "الشلف": (36.1647, 1.3317),
    "تيزي وزو": (36.7167, 4.0500),
    "بجاية": (36.7511, 5.0642),
    "جيجل": (36.8206, 5.7667),
    "سكيكدة": (36.8792, 6.9067),
    "سطيف": (36.1900, 5.4100),
    "باتنة": (35.5500, 6.1667),
    "بسكرة": (34.8500, 5.7333),
    "تامنراست": (22.7850, 5.5228),
    "تبسة": (35.4044, 8.1246),
    "تيارت": (35.3711, 1.3171),
}

# أنواع المباني ومعاملات الخطورة
BUILDING_TYPES = {
    "reinforced_concrete": {"name": "خرسانة مسلحة", "risk_factor": 0.3},
    "steel_frame": {"name": "هيكل فولاذي", "risk_factor": 0.2},
    "masonry": {"name": "بناء حجري", "risk_factor": 0.7},
    "adobe": {"name": "بناء طيني", "risk_factor": 0.9},
    "wood": {"name": "هيكل خشبي", "risk_factor": 0.4},
    "mixed": {"name": "بناء مختلط", "risk_factor": 0.5}
}

# إعدادات المحاكاة المالية
SIMULATION_CONFIG = {
    "default_simulations": 10000,
    "confidence_levels": [0.95, 0.99, 0.999],
    "retention_ratio": 0.30,
    "reinsurance_ratio": 0.70,
}