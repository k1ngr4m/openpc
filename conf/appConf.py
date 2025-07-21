from enum import Enum

from pydantic import BaseModel, Field

class Mode(str, Enum):
    DEBUG = "debug"
    PROD = "prod"

class LogConf(BaseModel):
    Level: str = Field(default="info", json_schema_extra={"env": "logLevel"})

class BuffApi(BaseModel):
    Url: str = Field(default="https://k2-api.buffge.com:40012/prod/lol", json_schema_extra={"env": "buffApiUrl"})
    Timeout: int = Field(default=5)

class WebViewConf(BaseModel):
    IndexUrl: str = Field(default="http://localhost:5173")

class AppConf(BaseModel):
    mode: Mode = Field(default="debug", json_schema_extra={"env": "APP_MODE"})
    log: LogConf = Field(default_factory=LogConf)
    app_name: str = Field(default="openpc")
    buff_api: BuffApi = Field(default_factory=BuffApi)
    website_title: str = Field(default="localhost:5173")
    web_view: WebViewConf = Field(default_factory=WebViewConf)

