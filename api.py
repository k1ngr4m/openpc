from typing import Any
from fastapi import HTTPException, Request
import services.logger.logger as logger
import jdUtil as jdUtil
from services.model.model_api import SkuInfo

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
        sku_type = data.get("skuType", "").strip()
        
        # 使用 SkuInfo 类封装数据
        raw_info = await self.jd.query_sku_info(sku_code)
        if raw_info:
            sku_info = SkuInfo(
                sku_code=raw_info['sku_code'],
                sku_name=raw_info['sku_name'],
                price=raw_info['price'],
                url=raw_info['url'],
                brand=raw_info['brand']
            )
            sku_info.type = sku_type  # 添加 type 字段
            self.jd.mysql.insert_sku_info(sku_info.to_dict())
            return sku_info.to_dict()
        
        return None
