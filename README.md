web接口代码层请求限制、夺宝购买生成订单号码的例子

一、最近做一个夺宝类项目（参照网易 一元夺宝），购买流程是购买份数，并给相应数量随机号码，最后整个商品的号码是连续的。

号码规则是：
        号码数量N = 商品总需份数 
        号码值：1000002 到 1000001+N 连续的号码

![image](https://github.com/liukelin/duobao_web_api/raw/master/img/case1.jpg)

![image](https://github.com/liukelin/duobao_web_api/raw/master/img/process.png)

购买时候的数量锁定：
对于购买时候的数量锁定，最简单可使用redis，利用incrby原子自增，（也可以使用一个集合，原子性是关键）。

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



二、代码层对连续请求的限制
        
        web接口遇到最多的或许是，用户在短时间内连续请求，如果代码逻辑判断写的不好的话容易造成数据的错误。
        
        nginx可做限流，这里讲针对代码层限制请求的一个小技巧
        
        因为redis的单线程的，并且存在一个incr(原子自增+1并返回值)，这样的话，即时多个并发请求incr操作，也会对每个请求给出一个不重复的顺序的号码。
        
        key = 'orders_pay'+str(uid)
        check = redisConn.incr(key)
        if check and int(check)<=1:
            redisConn.expire(key_, 5) # 设定过期
        else:
            return '请求太频繁，请稍后再试'
        
        上面代码，限制了同一个uid,只对第一个请求的通过，并设置5秒等待时间。
        试想：  1.可以将uid限制，换成对一个IP？ 
               2.或者对所有限制，并int(check)<=N 同时允许N个请求通过，其余的阻挡
        
        time = 1 # 每秒限制
        num = 10000 # 允许单位时间内请求数
        key = 'orders_pay'
        check = redisConn.incr(key)
        if check and int(check)<=num: 
            redisConn.expire(key_, time) # 设定过期
        else:
            return '请求太频繁，请稍后再试'
            
        
