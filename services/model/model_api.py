from typing import Optional

class SkuInfo:
    def __init__(self, sku_code: str, sku_name: str = "", price: float = 0.0, url: str = "", brand: str = ""):
        self.sku_code = sku_code
        self.sku_name = sku_name
        self.price = price
        self.url = url
        self.brand = brand
        
    def to_dict(self) -> dict:
        return {
            'sku_code': self.sku_code,
            'sku_name': self.sku_name,
            'price': self.price,
            'url': self.url,
            'brand': self.brand
        }