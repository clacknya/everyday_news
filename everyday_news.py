#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import asyncio
import aiohttp
import aiofiles
import datetime

from hoshino import Service
from hoshino.typing import CQEvent, MessageSegment

TZ: datetime.timezone = datetime.timezone(datetime.timedelta(hours=+8))

sv_query = Service('每日简报', visible=True, enable_on_default=True, help_='''
[每日简报/报哥/每日新闻] 获取每日简报
'''.strip())
sv_push_yiji = Service('易即简报推送', visible=True, enable_on_default=False, help_='''
每日9点推送易即简报
'''.strip())
sv_push_60s = Service('每天60秒读懂世界推送', visible=True, enable_on_default=False, help_='''
每日1点半推送每天60秒读懂世界
'''.strip())

async def yiji() -> bytes:
	retry_attempts = 3
	while retry_attempts > 0:
		try:
			async with aiohttp.ClientSession(raise_for_status=True) as session:
				async with session.get('http://118.31.18.68:8080/news/api/news-file/get') as resp:
					ret = await resp.json()
				date = datetime.datetime.strptime(ret['result']['date'], '%Y-%m-%d').astimezone(TZ).date()
				if datetime.datetime.today().date() > date:
					sv_query.logger.warning('易即简报今日未更新，等待后重试')
					await asyncio.sleep(300)
					continue
				async with session.get(ret['result']['data'][0]) as resp:
					ret = await resp.read()
		except (
			aiohttp.client_exceptions.ClientPayloadError,
			asyncio.exceptions.TimeoutError,
		) as e:
			retry_attempts -= 1
			sv_query.logger.warning(f"易即简报获取出错，剩余尝试次数{retry_attempts}")
			sv_query.logger.warning(e)
		except aiohttp.client_exceptions.InvalidURL as e:
			sv_query.logger.warning('易即简报地址未就绪，等待后重试')
			sv_query.logger.warning(e)
			await asyncio.sleep(300)
		except Exception as e:
			raise
		else:
			return ret
	raise Exception('易即简报获取失败')

async def sixty_seconds() -> bytes:
	retry_attempts = 3
	while retry_attempts > 0:
		try:
			async with aiohttp.ClientSession(raise_for_status=True) as session:
				async with session.get('https://api.2xb.cn/zaob') as resp:
					ret = await resp.json()
				date = datetime.datetime.strptime(ret['datatime'], '%Y-%m-%d').astimezone(TZ).date()
				if datetime.datetime.today().date() > date:
					sv_query.logger.warning('每天60秒读懂世界今日未更新，等待后重试')
					await asyncio.sleep(300)
					continue
				async with session.get(ret['imageUrl']) as resp:
					ret = await resp.read()
		except (
			aiohttp.client_exceptions.ClientPayloadError,
			asyncio.exceptions.TimeoutError,
		) as e:
			retry_attempts -= 1
			sv_query.logger.warning(f"每天60秒读懂世界获取出错，剩余尝试次数{retry_attempts}")
			sv_query.logger.warning(e)
		except aiohttp.client_exceptions.InvalidURL as e:
			sv_query.logger.warning('每天60秒读懂世界地址未就绪，等待后重试')
			sv_query.logger.warning(e)
			await asyncio.sleep(300)
		except Exception as e:
			raise
		else:
			return ret
	raise Exception('每天60秒读懂世界获取失败')

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

@sv_push_yiji.scheduled_job('cron', hour='9', minute='30')
async def news_yiji_scheduled():
	try:
		async with aiofiles.tempfile.NamedTemporaryFile('wb', delete=False) as f:
			await f.write(await yiji())
		os.chmod(f.name, 0o644)
		await sv_push_yiji.broadcast(MessageSegment.image(f"file:///{f.name}"), 'auto_send_news_message', 2)
	finally:
		if os.path.isfile(f.name):
			os.remove(f.name)

@sv_push_60s.scheduled_job('cron', hour='1', minute='30')
async def news_60s_scheduled():
	try:
		async with aiofiles.tempfile.NamedTemporaryFile('wb', delete=False) as f:
			await f.write(await sixty_seconds())
		os.chmod(f.name, 0o644)
		await sv_push_60s.broadcast(MessageSegment.image(f"file:///{f.name}"), 'auto_send_news_message', 2)
	finally:
		if os.path.isfile(f.name):
			os.remove(f.name)
