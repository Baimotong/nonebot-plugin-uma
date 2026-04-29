from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class UmaConfig(BaseModel):
    # 已迁移至 nonebot-plugin-localstore，保留用于兼容已有自定义配置
    uma_data_dir: Optional[Path] = Field(default=None)
    uma_default_server: str = Field(default="jp")
    uma_use_proxy: bool = Field(default=False)
    uma_proxy_url: str = Field(default="http://localhost:1081")
