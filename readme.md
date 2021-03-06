# py_weibo

一个小的微博抓取脚本

可抓取的信息有：

- 指定人的所有(对你)可见微博

- 每条微博的创建时间

- 微博 id 
  
- 可访问这条微博的 url (非 100%　有效, 原因见 program details)
  
- 微博发布设备来源
  
- 微博(原创)中的高清大图
  
- 转发微博的原微博内容
  
- 这条微博的评论(脚本限制最大 1000 条)
  
  
### 脚本特色:

1 使用 python yield 语法，省内存，不把所有微博记录保存在内存中，若要持久化，可重定向到文件

2 使用 Chrome 浏览器 cookie ，脚本自己不登录，需要在浏览器做一次登录，使 cookie 有效

3 无限重试，在抓取过程中，频繁抓取会突然导致 cookie 失效，需要立刻手动登录一次微博(https://m.weibo.cn/)，
  脚本通过 requests 的 url 来判断是否属于这种需要登录的情况，如果是，则重新载入浏览器的 cookie，新载入的
  浏览器 cookie 即为刚刚重新登录过的，从而完成了"断点"抓取，无需重新运行脚本

4 不同于用作大数据研究的微博抓取程序，该脚本注重准确性、完整性，不断重试一定要获取到指定人所有微博
  
###  抓取结果示例:

```
tombkeeper: 02-21 20:07
    id: 4077682889542353   http://weibo.com/1401527553/EwASYE2oV   https://m.weibo.cn/status/4077682889542353
    [来自:微博 weibo.com] [置顶] 西方说的“退化左派”（Regressive Left），接近于大陆语境下的“精神白左”、“圣母”。这群人最厉害的地方是有一撮护心毛，叫：“就算我错了，也是一种慈悲高尚的错；就算我使诈，也是为了慈悲高尚而使诈；就算我不择手段，也是出于慈悲高尚的目的”。有这撮护心毛保底，他们在精神上是不可战胜的。 ​​​
    转发自:False
    评论1 巨蟹爷爷 在 02-21 21:13 使用设备 iPhone客户端 回复内容: 是和尚么
    评论2 momoka旅行去 在 02-21 23:41 使用设备 HUAWEI Mate 8 回复内容: 护心毛哈哈哈，此乃新精神胜利法
    评论3 Patrick-He 在 02-21 23:51 使用设备 iPhone 7 Plus 回复内容: “都是为你好”
    评论4 主演诗词加小说 在 02-22 06:29 使用设备 三星android智能手机 回复内容: 真神经病啊！
    评论5 guangyuge 在 02-22 09:24 使用设备 UC浏览器 回复内容: 我的本意是好的，虽然干了错事你们也不能批评我
    评论6 Deathspe11 在 03-01 18:36 使用设备 微博 weibo.com 回复内容: 绝对的，强无敌。
    评论7 阿瑞天天在摸鱼 在 06-23 02:15 使用设备 微博 weibo.com 回复内容: 那可如何是好
    评论8 是健气不是贱气 在 06-23 16:06 使用设备 Weibo.intl 回复内容: 只要你的心是善良的，对错都是别人的事。 《大鱼·海棠》
    评论9 Gooooooooooooo0 在 07-06 01:14 使用设备 Android客户端 回复内容: 评判方法是？拔毛方法是？
    评论10 土鳖龟徐波説_得赔偿方舟_亿美元 在 07-08 11:56 使用设备 UC浏览器 回复内容: 🔥
```


###  program details

1 网络访问使用 requests

2 json dict 使用 jsonpath 语法访问，该语法可与 Chrome 插件 jsonhandle 无缝连接，
  jsonhandle 与 jsonpath 的路径是一样的，在 jsonhandle 用鼠标定位到路径，复制到
  python 中即可使用
 
3 没有精确的办法判断获取到了全部微博，没有总 page count，无法信任 weibo count ，因为
  用户的不可见微博也可能包含在里面，如果信任这个数目，会造成死循环
 

4 几个 url 模板

个人信息，得到获取微博需要的 containerid

hxxps://m.weibo.cn/api/container/getIndex?type=uid&value=5044281310

每一页的微博 

hxxps://m.weibo.cn/api/container/getIndex?type=uid&value=5044281310&containerid=1076035044281310&page=1

5 服务器很不稳定，json 字段中的 $.cardlistInfo.page 也不可信

6 总结服务器不稳定的地方在于 获取微博数目没办法校验是否获取完全、没办法了解微博 page 是否能结束了
  能获取多少微博全看运气

7 增加一条不可信：
  通过 url hxxps://m.weibo.cn/api/container/getIndex?type=uid&value=5044281310&containerid=1076035044281310&page=1
  可以获取到微博，对应到 tombkeeper 的最后一页微博是 
  hxxps://m.weibo.cn/api/container/getIndex?type=uid&containerid=1076031401527553&page=1423 
  每一页中由 $.cards 列表保存微博内容， 由 $.cards[0].mblog.bid 能拼凑出该条微博的访问地址，结果到 tombkeeper 最后一页
  发现这个规律不是 100% 的