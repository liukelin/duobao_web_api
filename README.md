web请求限制、夺宝购买生成订单号码的例子

最近做一个夺宝类项目（参照网易 一元夺宝），购买流程是购买份数并给相应数量随机号码。

号码规则是：
        号码数量N=商品总需份数 
        号码值：1000002 到 1000001+N 连续的号码

![image](https://github.com/liukelin/duobao_web_api/raw/master/img/case1.jpg)

![image](https://github.com/liukelin/duobao_web_api/raw/master/img/process.png)

购买时候的数量锁定：
对于购买时候的数量锁定，可使用redis，利用incrby原子自增。

    # 读取商品信息
    goods = get_goods(goods_id)
    if goods:
        goods_total = int(goods['goods_total']) # 商品总库存
        goods_has = int(goods['goods_has'])     # 商品已出售

        # create lock 避免 足量和重复购买, 
        redis_key = 'goods_pay_' + str(goods_id) 

        # 获取锁定库存
        has = redisConn.get(redis_key)
        has = int(has) if has else 0

        # 实际已出售
        goods_has = goods_has + int(has)

        if goods_total > goods_has : # 判断实际库存数

            # 判断实际购买数
            can_num = 0
            if (goods_total - goods_has) >= num:
                can_num = num
            else :
                can_num = goods_total - goods_has

            # lock 锁定数量
            redisConn.incrby(redis_key, can_num)
            redisConn.expire(redis_key, 100) # 锁失效时间
            
            ‘’‘
              购买逻辑操作
            ’‘’
           
           # 扣除库存数
           up_goods_has(goods_id, can_num)
            
           # unlock  最后解除锁定
           redisConn.incrby(redis_key, -can_num)


号码随机获取：
这里就涉及到一个号码池的问题，每个商品对应所有号码，并从这个号码池随机领取。
最简单的方法是使用 redis的set集合，spop随机获取集合元素
    
    num = xx # 购买数量
    # 读取号码集合池
    codeKey = 'goods_code_set_' + str(goods_id)
    CodeNum = redisConn.scard(codeKey)
    
    if CodeNum and int(CodeNum)>0: # 判断池是否存在
        pass
    else: 
        # load code set 加载可用号码到集合
        
        codesAll = [] #所有码　
        StartCode_ = 1000002
        for i in range(StartCode_, StartCode_ + goods_total):
            codesAll.append(i)

        codesOld = [] #已使用码 ，载入已使用过的号码（记录在db的号码记录）
        CList = get_period_code(goods_id) 
        if CList:
            if i in CList:
                codesOld.append(int(i['code']))
        
        # 所有可用号码 
        codesNew = list( set(codesAll).difference( set(codesOld) ) ) 
        for code in codesNew:
            redisConn.sadd(codeKey, code)

    # 随机获取号码
    codes = []
    for i in range(0, num):
        code = redisConn.spop(codeKey)
        if code:
            codes.append(code)
     return codes
