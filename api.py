from typing import Any
from fastapi import HTTPException, Request
import services.logger.logger as logger
import jdUtil as jdUtil
from services.model.model_api import SkuInfo, SkuType

class Api:
    def __init__(self, jdUtil: jdUtil):
        self.jd = jdUtil

    async def DevHand(self, request: Request):
        return {"buffge": 23456}

    # async def QueryHorseBySummonerName(self, request: Request):
    #     data = await request.json()
    #     summoner_name = data.get("summonerName", "").strip()

    async def QuerySkuInfo(self, request: Request):
        data = await request.json()
        sku_code = data.get("skuCode", "").strip()
        sku_type_str = data.get("skuType", "").strip()
        
        # 使用 SkuType 转换类型字符串为整数代码
        try:
            sku_type_code = SkuType.get_type_code(sku_type_str)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid sku type: {sku_type_str}")
            
        # 使用 SkuInfo 类封装数据
        raw_info = await self.jd.query_sku_info(sku_code)
        if raw_info:
            sku_info = SkuInfo(
                sku_code=raw_info['sku_code'],
                sku_name=raw_info['sku_name'],
                price=raw_info['price'],
                url=raw_info['url'],
                brand=raw_info['brand'],
                type=str(sku_type_code),
                is_taken_down=raw_info['is_taken_down']
            )
            self.jd.mysql.insert_sku_info(sku_info.to_dict())
            return sku_info.to_dict()
        
        return None

    async def GetProductList(self, request: Request):
        data = await request.json()
        sku_type = data.get("type", "").strip()

        sku_list = self.jd.mysql.query_sku_info_by_type(sku_type)

        return [{
            "sku_name": sku['sku_name'],
            "price": sku['price']
        } for sku in sku_list]
