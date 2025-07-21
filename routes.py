from timeit import default_timer

from fastapi import Request, APIRouter, Depends, FastAPI

from api import Api


def register_routes(app: FastAPI, api: Api):
    # 1. “test” 路由，支持所有 HTTP 方法
    @app.api_route(
        "/test",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )
    async def test_handler(request: Request):
        if request.method == "OPTIONS":
            return {"status": "OK"}
        return await api.DevHand(request)

    # 2. 创建 /v1 路由组
    v1 = APIRouter(prefix="/v1")

    # 2.1 测试路由
    @v1.get("/test")
    async def test_v1():
        return {"status": "OK"}

    @v1.post("/querySkuInfo")
    async def query_sku_info(request: Request):
        return await api.QuerySkuInfo(request)

    # @v1.get("/getCurrSummoner")
    # async def get_curr_summoner(request: Request):
    #     return await api.GetCurrSummoner(request)
    #
    # @v1.post(
    #     "/summoner/queryByName/info",
    #     dependencies=[Depends(api.ProphetActiveMid)],
    # )
    # async def get_summoner_info(request: Request):
    #     return await api.GetSummonerInfoByName(request)

    # # 2.1 查询用户马匹信息（带中间件 ProphetActiveMid）
    # @v1.post(
    #     "/horse/queryBySummonerName",
    #     dependencies=[Depends(api.ProphetActiveMid)],
    # )
    # async def query_horse_by_summoner(request: Request):
    #     return await api.QueryHorseBySummonerName(request)

    # # 2.2 获取所有配置
    # @v1.post("/config/getAll")
    # async def get_all_conf(request: Request):
    #     return await api.GetAllConf(request)


    # 最后把 v1 注册到主应用
    app.include_router(v1)