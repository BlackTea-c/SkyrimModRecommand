原本想做电影推荐系统的，但是很多人做过了  （有前端）
这里做一个上古卷轴mod得推荐系统，我看像n网什么的都是热度推荐很少有为用户
进行个性化得推荐。

目前本地网站已经写得差不多了，还特地美化了一下，马上就可以开始爬数据开始
写推荐系统了。

现在的话直接下载到本地cd到moiveRe文件夹然后去终端python manage.py runsever就行了
具体操作代码看django。


3/7 成功爬取了100多组数据，期间有个问题就是
设置环境变量，指向你的Django项目的settings模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moiveRe.settings')
配置Django
django.setup()

这个一直报错找不到moiveRe.settings

原因是一定要把py文件放在moiveRe根目录下面。要不就识别不到。



3/11  实现了Usercf并且实时更新。

3/12  实现了itemcf,效果肯定是比usercf好。