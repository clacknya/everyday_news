#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import aiohttp
import aiofiles

from hoshino import Service
from hoshino.typing import CQEvent, MessageSegment

sv_query = Service('每日简报', visible=True, enable_on_default=True, help_='''
[每日简报/报哥/每日新闻] 获取每日简报
'''.strip())
sv_push_yiji = Service('易即简报推送', visible=True, enable_on_default=False, help_='''
每日9点推送易即简报
'''.strip())
sv_push_60s = Service('每天60秒读懂世界推送', visible=True, enable_on_default=False, help_='''
每日1点推送每天60秒读懂世界
'''.strip())

async def yiji() -> bytes:
	try:
		async with aiohttp.ClientSession(raise_for_status=True) as session:
			async with session.get('http://api.soyiji.com//news_jpg') as resp:
				ret = await resp.json()
			async with session.get(ret['url']) as resp:
				ret = await resp.read()
	except Exception as e:
		sv_query.logger.error('易即简报获取失败')
		raise
	else:
		sv_query.logger.info('易即简报获取成功')
		return ret

async def sixty_seconds() -> bytes:
	try:
		async with aiohttp.ClientSession(raise_for_status=True) as session:
			async with session.get('https://api.iyk0.com/60s/') as resp:
			# async with session.get('https://api.2xb.cn/zaob') as resp:
				ret = await resp.json()
			async with session.get(ret['imageUrl']) as resp:
				ret = await resp.read()
	except Exception as e:
		sv_query.logger.error('每天60秒读懂世界获取失败')
		raise
	else:
		sv_query.logger.info('每天60秒读懂世界获取成功')
		return ret

@sv_query.on_fullmatch(('每日简报', '报哥', '每日新闻'))
async def news(bot, ev: CQEvent):
	try:
		async with aiofiles.tempfile.NamedTemporaryFile('wb', delete=False) as f:
			await f.write(await yiji())
		os.chmod(f.name, 0o644)
		await bot.send(ev, MessageSegment.image(f"file:///{f.name}"), at_sender=True)
	finally:
		if os.path.isfile(f.name):
			os.remove(f.name)

@sv_push_yiji.scheduled_job('cron', hour='9')
async def news_yiji_scheduled():
	try:
		async with aiofiles.tempfile.NamedTemporaryFile('wb', delete=False) as f:
			await f.write(await yiji())
		os.chmod(f.name, 0o644)
		await sv_push_yiji.broadcast(MessageSegment.image(f"file:///{f.name}"), 'auto_send_news_message', 2)
	finally:
		if os.path.isfile(f.name):
			os.remove(f.name)

@sv_push_60s.scheduled_job('cron', hour='1')
async def news_60s_scheduled():
	try:
		async with aiofiles.tempfile.NamedTemporaryFile('wb', delete=False) as f:
			await f.write(await sixty_seconds())
		os.chmod(f.name, 0o644)
		await sv_push_60s.broadcast(MessageSegment.image(f"file:///{f.name}"), 'auto_send_news_message', 2)
	finally:
		if os.path.isfile(f.name):
			os.remove(f.name)
