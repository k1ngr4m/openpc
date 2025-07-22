from dataclasses import dataclass
from enum import Enum
from typing import Optional

# class SkuInfo:
#     def __init__(self, sku_code: str, sku_name: str = "", price: float = 0.0, url: str = "", brand: str = "", type: str = ""):
#         self.sku_code = sku_code
#         self.sku_name = sku_name
#         self.price = price
#         self.url = url
#         self.brand = brand
#         self.type = type
#
#     def to_dict(self) -> dict:
#         return {
#             'sku_code': self.sku_code,
#             'sku_name': self.sku_name,
#             'price': self.price,
#             'url': self.url,
#             'brand': self.brand,
#             'type': self.type
#         }

@dataclass
class SkuInfo:
    sku_code: str
    sku_name: str = ""
    price: float = 0.0
    url: str = ""
    brand: str = ""
    type: str = ""
    is_taken_down: int = 0

    def to_dict(self) -> dict:
        return {
            'sku_code': self.sku_code,
            'sku_name': self.sku_name,
            'price': self.price,
            'url': self.url,
            'brand': self.brand,
            'type': self.type,
            'is_taken_down': self.is_taken_down
        }

class SkuType(str, Enum):
    GPU = "显卡"
    CPU = "cpu"
    MOTHERBOARD = "主板"
    MEMORY = "内存"
    STORAGE = "存储"
    POWER_SUPPLY = "电源"
    CASE = "机箱"
    COOLER = "散热器"
    MONITOR = "显示器"
    
    @classmethod
    def get_type_code(cls, sku_type_str: str) -> int:
        for i, member in enumerate(cls):
            if member.value == sku_type_str:
                return i + 1
        raise ValueError(f"Invalid sku type: {sku_type_str}")
    
    @classmethod
    def get_type_str(cls, type_code: int) -> str:
        if 1 <= type_code <= len(cls):
            return list(cls)[type_code - 1].value
        raise ValueError(f"Invalid type code: {type_code}")