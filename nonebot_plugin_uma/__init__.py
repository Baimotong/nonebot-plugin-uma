from nonebot import require, on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message

require("nonebot_plugin_apscheduler")

from nonebot.plugin import PluginMetadata

from .config import UmaConfig

__plugin_meta__ = PluginMetadata(
    name="赛马娘插件",
    description="赛马娘模拟抽卡、新闻推送、生日提醒",
    usage="发送 马娘帮助 查看全部指令",
    type="application",
    homepage="https://github.com/Baimotong/nonebot-plugin-uma",
    config=UmaConfig,
    supported_adapters={"~onebot.v11"},
)

from . import gacha, news, birthday  # noqa: E402, F401

HELP_TEXT = """【赛马娘插件帮助】

◆ 抽卡
  马娘单抽 / 单抽马娘 — 马娘池单抽
  马娘十连 / 马十连 — 马娘池十连
  马之井 / 马娘井 — 马娘池200抽天井
  支援卡单抽 — 支援卡池单抽
  支援卡十连 — 支援卡池十连
  支援卡井 — 支援卡池200抽天井
  支援卡抽满破 — 模拟抽到满破
  支援卡选择满破目标 — 设置满破目标(不带参数查看列表)
  支援卡查询满破目标 — 查询当前目标
  支援卡清除满破目标 — 清除目标
  查看马娘卡池 — 查看当前卡池信息
  切换马娘服务器 jp/tw/bili — 切换服务器(群管理)
  切换马娘卡池 数字ID — 切换卡池(群管理)
  更新马娘卡池 — 手动更新卡池数据(超管)

◆ 新闻
  马娘新闻 — 查看日服最新新闻
  开启马娘新闻推送 — 开启日服新闻定时推送
  关闭马娘新闻推送 — 关闭日服新闻定时推送

◆ 生日
  查今天生日马娘 — 今天谁过生日
  查马娘生日 角色名 — 查询角色生日
  查生日马娘 月-日 — 查询某天生日的角色
  开启马娘生日推送 — 开启每日生日提醒
  关闭马娘生日推送 — 关闭每日生日提醒"""

uma_help = on_command("马娘帮助", priority=10, block=True)

@uma_help.handle()
async def handle_help(event: GroupMessageEvent):
    await uma_help.finish(HELP_TEXT)
