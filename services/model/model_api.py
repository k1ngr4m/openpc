from dataclasses import dataclass
from enum import Enum
from typing import Optional

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
    COOLER = "散热器"
    MEMORY = "内存"
    SSD = "固态硬盘"
    POWER_SUPPLY = "电源"
    CASE = "机箱"
    FAN = "风扇"
    HDD = "机械硬盘"

    # 在类初始化后创建映射
    _value_to_code = None
    _code_to_value = None

    @classmethod
    def _init_mappings(cls):
        """初始化映射关系（延迟加载）"""
        if cls._value_to_code is None:
            members = list(cls)
            cls._value_to_code = {member.value: i + 1 for i, member in enumerate(members)}
            cls._code_to_value = {i + 1: member.value for i, member in enumerate(members)}

    @classmethod
    def get_type_code(cls, sku_type_str: str) -> int:
        cls._init_mappings()  # 确保映射已初始化
        if code := cls._value_to_code.get(sku_type_str):
            return code
        raise ValueError(f"Invalid sku type: {sku_type_str}")

    @classmethod
    def get_type_str(cls, type_code: int) -> str:
        cls._init_mappings()  # 确保映射已初始化
        if value := cls._code_to_value.get(type_code):
            return value
        raise ValueError(f"Invalid type code: {type_code}")