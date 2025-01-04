from logging import exception

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

        icbc_rate = r.hgetall('ere:monitor:currentRate:ICBC')
        # 转换为对象字典
        icbc_rate_objects = {
            key.decode('utf-8'): Rate(**json.loads(value.decode('utf-8')))
            for key, value in icbc_rate.items()
        }



        currencies = [{"currency_code": "AUD", "currency_name": "澳元"}, {"currency_code": "KRW", "currency_name": "韩元"},
                      {"currency_code": "JPY", "currency_name": "日元"}, {"currency_code": "USD", "currency_name": "美元"},
                      {"currency_code": "GBP", "currency_name": "英镑"}, {"currency_code": "EUR", "currency_name": "欧元"}]

        for currency in currencies:
            currency_code = currency['currency_code']
            currency_name = currency['currency_name']
            group_name = f'汇率速递-{currency_name}'
            boc_currency = boc_rate_objects[currency_code].currentRate
            icbc_currency = icbc_rate_objects[currency_code].currentRate

            msg = f'📢汇率速递·{currency_name} 现汇卖出价📢\n中国银行：{boc_currency}\n工商银行：{icbc_currency}\n时间：{current_time} ⏰'

            wx.send_msg(group_name, [msg], [])


    except exception as e:
        print(f"Connection error: {e}")




# 创建调度器
scheduler = BlockingScheduler()

# 添加任务，使用 Cron 表达式
# 表示每分钟的第 0 秒执行
scheduler.add_job(send_group_msg, trigger=CronTrigger.from_crontab("0 6-23 * * 1-5"))
scheduler.add_job(send_group_msg, trigger=CronTrigger.from_crontab("0 6 * * 6,7"))

# 启动调度器
try:
    # send_group_msg()
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    pass
