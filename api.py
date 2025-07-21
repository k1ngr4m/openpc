from typing import Any
from fastapi import HTTPException, Request


class Api:
    def __init__(self, jdUtil: Any):
        self.jd = jdUtil

    async def DevHand(self, request: Request):
        return {"buffge": 23456}

    # async def QueryHorseBySummonerName(self, request: Request):
    #     data = await request.json()
    #     summoner_name = data.get("summonerName", "").strip()

    async def QuerySkuInfo(self, request: Request):
        data = await request.json()
        print(data)
        sku_code = data.get("skuCode", "").strip()
        sku_type = data.get("skuType", "").strip()
        sku_info = self.jd.query_sku_info(sku_code)
        return sku_info
