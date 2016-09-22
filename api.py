#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author: liukelin  314566990@qq.com

'''

购买夺宝号码，并扣除商品库存数

'''
import os
import time
import redis

from wsgiref.simple_server import make_server

config = {
    'mysql':{
        'host': "localhost",
        'database': 'kelin_test',
        'user': 'root',
        'password': '123456',
        }
    'redis': {
        'host':'localhost',
        'port':3306,
        'db':0
    }
}
# db_mysql = torndb.Connection(**config['mysql'])
pool = redis.ConnectionPool(**config['redis'])
redisConn = redis.Redis(connection_pool=pool)


def pay():

    uid = 1 # 用户id
    num = 1 # 期望购买数
    goods_id = 1 # 


    # 读取商品信息
    goods = get_goods(goods_id)
    if goods:
        goods_total = int(period['goods_total']) # 商品总库存
        goods_has = int(period['goods_has'])     # 商品已出售

        # create lock 避免 足量和重复购买, 
        redis_key = 'goods_pay_' + str(goods_id) 

        # 获取锁定库存
        has = redisConn.get(redis_key)
        has = int(has) if has else 0

        # 实际已出售
        goods_has = goods_has + int(has)

        if goods_total > goods_has : # 判断库存数

            # 判断实际购买数
            can_num = 0
            if (goods_total - goods_has) >= num:
                can_num = num
            else :
                can_num = goods_total - goods_has

            # lock 锁定数量
            redisConn.incrby(redis_key, can_num)
            redisConn.expire(redis_key, 100) # 锁失效时间


            '''
              随机获取号码
            '''
            reu = set_period_code(goods_id, uid, can_num)

            # 扣除库存数
            up_goods_has(goods_id, can_num)

            # unlock 
            redisConn.incrby(redis_key, -can_num)

        return False

'''
    获取码
    goods_id     
    num 取号码数
'''
def set_period_code(goods_id, uid, num):
    StartCode = 10000001
    num = int(num)
    if not goods_id or not uid or num<=0:
        return False


    goods = get_goods(goods_id)
    if goods:
        goods_total = int(goods['goods_total'])
        goods_has = int(goods['goods_has'])

        if goods_total <= goods_has:
            return False
    else:
        return False

    # 读取号码集合
    codeKey = 'goods_code_set_' + str(goods_id)
    CodeNum = redisConn.scard(codeKey)
    if CodeNum and int(CodeNum)>0:
        pass
    else: 
        # load code set 加载可用号码到集合

        codesAll = [] #所有码　
        StartCode_ = StartCode+1
        for i in range(StartCode_, StartCode_ + goods_total):
            codesAll.append(i)

        codesOld = [] #已使用码
        CList = get_period_code(goods_id)
        if CList:
            if i in CList:
                codesOld.append(int(i['code']))

        codesNew = list( set(codesAll).difference( set(codesOld) ) )
        for code in codesNew:
            redisConn.sadd(codeKey, code)

    # 随机获取号码
    codes = []
    for i in range(0, num):
        code = redisConn.spop(codeKey)
        if code:
            codes.append(code)

    # 入库
    reu = set_code(uid, goods_id, codes)

    return reu,len(codes)

# 获取商品信息
def get_goods(goods_id):
    return db_mysql.get(" select * from `goods` where `goods_id`=%s ", goods_id)

# 获取商品已售号码
def get_goods_code(goods_id):
    return db_mysql.query(" select `id`,`code` from `goods_code` where `goods_id`=%s ", goods_id)

# 扣除已购买数
def up_goods_has(goods_id, num):
    return db_mysql.execute(" update `goods_code` set `goods_has`=`goods_has`+%s where `goods_id`=%s ", num, goods_id)

def set_code(uid, goods_id, codes=[]):

    createtime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    sql = " INSERT INTO  `orders_code` (`code`, `goods_id` ,`uid`, `time`) values "
    for code in codes:
        sql +=  "('%s', '%s', '%s', '%s')," %( code, goods_id, uid, createtime)
    sql = sql[:-1]
    suc = db_mysql.execute(sql)
    return suc


def application(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [b'<h1>Hello, web!</h1>',time.time()]

def wsgi_server(address, port):
    # 创建一个服务器，IP地址为空，端口是8000，处理函数是application:
    httpd = make_server(address, port, application)
    print('Serving HTTP on port %s...' % port)
    # 开始监听HTTP请求:
    httpd.serve_forever()

if __name__=='__main__':
    wsgi_server('0.0.0.0', 6000)
    
















