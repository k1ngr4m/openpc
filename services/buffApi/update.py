import json
import requests
from typing import Optional, TypedDict
import global_conf.global_vars
from conf.appConf import AppConf, Mode


# 定义配置常量
CODE_OK = 0

# 全局变量
client = None
base_url = ""


# 类型定义
class Response(TypedDict):
    code: int
    msg: str
    data: dict

class CurrVersion(TypedDict):
    downloadUrl: str
    versionTag: str
    zipDownloadUrl: str


def init(url: str, _timeout_sec: int) -> None:
    """初始化 HTTP 客户端"""
    global client, base_url, timeout_sec
    base_url = url
    timeout_sec = _timeout_sec


def req(req_path: str, body: Optional[dict] = None) -> dict:
    """发送 HTTP POST 请求并处理响应"""
    url = base_url + req_path
    headers = {"Content-Type": "application/json"}

    try:
        # 发送请求
        response = requests.post(
            url,
            json=body,
            headers=headers,
            timeout=timeout_sec
        )

        # 检查 HTTP 状态码
        response.raise_for_status()

        # 解析 JSON 响应
        api_resp: Response = response.json()

        # 检查 API 响应码
        if api_resp["code"] != CODE_OK:
            raise Exception(f"API error {api_resp['code']}: {api_resp['msg']}")

        return api_resp["data"]

    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {str(e)}")
    except json.JSONDecodeError:
        raise Exception("Invalid JSON response")


def get_curr_version() -> CurrVersion:
    """获取当前版本信息"""
    data = req("/v1/lol/getCurrVersion")
    return CurrVersion(
        downloadUrl=data.get("downloadUrl", ""),
        versionTag=data.get("versionTag", ""),
        zipDownloadUrl=data.get("zipDownloadUrl", "")
    )