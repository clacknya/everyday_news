#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = '0.1.0'

import os
import aiohttp
import aiofiles

from hoshino import Service
from hoshino.typing import CQEvent, MessageSegment

sv = Service('everydayNews', visible=True, enable_on_default=False, help_='''
[每日简报] 请发送“每日简报、报哥或每日新闻”
'''.strip())

path = os.path.dirname(__file__)

async def getImgUrl() -> str:
	try:
		async with aiohttp.ClientSession(raise_for_status=True) as session:
			async with session.get('http://api.soyiji.com//news_jpg') as resp:
				ret = await resp.json()
	except Exception as e:
		sv.logger.error('图片URL获取失败')
	else:
		sv.logger.info('图片URL获取成功')
		return ret['url']

async def getImg() -> bytes:
	try:
		async with aiohttp.ClientSession(raise_for_status=True) as session:
			async with session.get(await getImgUrl(), headers={'Referer': 'safe.soyiji.com'}) as resp:
				ret = await resp.read()
	except Exception as e:
		sv.logger.error('图片获取失败')
	else:
		sv.logger.info('图片获取成功')
		return ret

@sv.on_fullmatch(('每日简报', '报哥', '每日新闻'))
async def news(bot, ev: CQEvent):
	try:
		async with aiofiles.tempfile.NamedTemporaryFile('wb', delete=False) as f:
			await f.write(await getImg())
		os.chmod(f.name, 0o644)
		await bot.send(ev, MessageSegment.image(f"file:///{f.name}"), at_sender=True)
	finally:
		if os.path.isfile(f.name):
			os.remove(f.name)

@sv.scheduled_job('cron', hour='9')
async def news_scheduled():
	try:
		async with aiofiles.tempfile.NamedTemporaryFile('wb', delete=False) as f:
			await f.write(await getImg())
		os.chmod(f.name, 0o644)
		await sv.broadcast(MessageSegment.image(f"file:///{f.name}"), 'auto_send_news_message', 2)
	finally:
		if os.path.isfile(f.name):
			os.remove(f.name)
