import redis
from dataclasses import dataclass
import json
from utils import WxOperation
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config import (RedisConfig)






wx = WxOperation()

@dataclass
class Rate:
    currentRate: float
    time: str

# 连接到本地 Redis
r = redis.Redis(host=RedisConfig.host, port=RedisConfig.port, password=RedisConfig.password)

def send_group_msg():
    try:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(current_time)

        boc_rate = r.hgetall('ere:monitor:currentRate:BOC')

        # 转换为对象字典
        boc_rate_objects = {
            key.decode('utf-8'): Rate(**json.loads(value.decode('utf-8')))
            for key, value in boc_rate.items()
        }

        boc_aud = boc_rate_objects['AUD'].currentRate
        boc_krw = boc_rate_objects['KRW'].currentRate

        icbc_rate = r.hgetall('ere:monitor:currentRate:ICBC')

        # 转换为对象字典
        icbc_rate_objects = {
            key.decode('utf-8'): Rate(**json.loads(value.decode('utf-8')))
            for key, value in icbc_rate.items()
        }

        icbc_aud = icbc_rate_objects['AUD'].currentRate
        icbc_krw = icbc_rate_objects['KRW'].currentRate

        aud_msg = f'📢汇率速递·澳元 现汇卖出价📢\n中国银行：{boc_aud}\n工商银行：{icbc_aud}\n时间：{current_time} ⏰'
        krw_msg = f'📢汇率速递·韩元 现汇卖出价📢\n中国银行：{boc_krw}\n工商银行：{icbc_krw}\n时间：{current_time} ⏰'

        wx.send_msg('汇率速递-日元', [aud_msg], [])
        # wx.send_msg('汇率速递-韩元', [krw_msg], [])

    except redis.ConnectionError as e:
        print(f"Connection error: {e}")




# 创建调度器
scheduler = BlockingScheduler()

# 添加任务，使用 Cron 表达式
# 表示每分钟的第 0 秒执行
scheduler.add_job(send_group_msg, trigger=CronTrigger.from_crontab("0 6-23 * * *"))

# 启动调度器
try:
    while True:
        send_group_msg()
        scheduler.start()
except (KeyboardInterrupt, SystemExit):
    pass
