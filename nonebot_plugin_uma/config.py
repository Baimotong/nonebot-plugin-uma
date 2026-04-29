from pathlib import Path

from pydantic import BaseModel, Field


class UmaConfig(BaseModel):
    uma_data_dir: Path = Field(default=Path("data/uma"))
    uma_default_server: str = Field(default="jp")
    uma_use_proxy: bool = Field(default=False)
    uma_proxy_url: str = Field(default="http://localhost:1081")
