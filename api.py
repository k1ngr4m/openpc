from typing import Any
from fastapi import HTTPException, Request
import services.logger.logger as logger
import jdUtil as jdUtil

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
        sku_info = await self.jd.query_sku_info(sku_code)
        if sku_info:
            sku_info['type'] = sku_type
            self.jd.mysql.insert_sku_info(sku_info)
        return sku_info
