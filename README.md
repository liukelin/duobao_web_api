web请求限制、夺宝购买生成订单号码的例子

最近做一个夺宝类项目（参照网易 一元夺宝），购买流程是购买份数并给相应数量随机号码。

号码规则是：
        号码数量N=商品总需份数 
        号码值：1000002 到 1000001+N 连续的号码

![image](https://github.com/liukelin/duobao_web_api/raw/master/img/case1.jpg)

![image](https://github.com/liukelin/duobao_web_api/raw/master/img/process.png)

购买时候的数量锁定：
对于购买时候的数量锁定，可使用redis，利用incrby原子自增

号码随机获取：
这里就涉及到一个号码池的问题，每个商品对应所有号码，并从这个号码池随机领取。
最简单的方法是使用 redis的set集合，spop随机获取集合元素
