# coding=utf-8

import os
import sys
import requests
import jsonpath
import time

curpath = os.path.dirname(os.path.realpath(__file__))

from io_in_out import io_print
from io_in_out import io_stderr_print


def _get_chrome_cookies_files():
    '''
    browsercookie 中预设的 cookies 路径老了，新版的 chrome cookies 路径不是那个
    在这个函数里更新
    '''
    import glob
    fullpath_chrome_cookies = os.path.join(os.getenv('APPDATA', ''),
                                           r'..\Local\Google\Chrome\User Data\Profile 1\Cookies')
    for e in glob.glob(fullpath_chrome_cookies):
        yield e


def _get_chrome_cookies():
    import browsercookie
    from itertools import chain

    a = browsercookie.Chrome()
    files_old = a.find_cookie_files()
    files = chain(_get_chrome_cookies_files(), files_old)

    return browsercookie.chrome(files)


def _cookies_curpath(cookie_jar_to_save=None):
    '''
    用来保存 cookie 到本地，防止多次读取 Chrome 目录
    pycharm 无法在 tmp 目录写文件，权限不够，用这个函数先躲一躲
    if is None cookie_jar_to_save, try to read _chrome_cache_cookies.txt
    if cookie_jar_to_save , save cookies to _chrome_cache_cookies.txt
    '''
    import pickle
    from requests.cookies import RequestsCookieJar

    fullpath = os.path.join(curpath, u'_chrome_cache_cookies.txt')

    if cookie_jar_to_save:
        if os.path.exists(fullpath):
            os.remove(fullpath)
        a = RequestsCookieJar()
        a.update(cookie_jar_to_save)
        with open(fullpath, 'wb') as fw:
            pickle.dump(a
                        , fw
                        )
        return cookie_jar_to_save

    if not os.path.exists(fullpath):
        return None

    with open(fullpath, 'rb') as fr:
        pc = pickle.load(fr)
        return pc


class weibo(object):
    def __init__(self):
        # self._cookie = _cookies_curpath(None)
        self._cookie = _get_chrome_cookies()

    def _access_net(self, *args, **kwargs):
        t = 1
        # for _ in range(50000):

        not_ok_response = []
        while True:
            try:
                time.sleep(0.3)
                kwargs.update(cookies=self._cookie)
                res = requests.get(*args, **kwargs)
                res_json = res.json()

                # 如果出现 ok=0 需要再重试 5 次，确认结束 因为没有精确办法知道什么时候可以结束
                ok = jsonpath.jsonpath(res_json, u'$.ok')[0]
                if not (ok == 1):
                    not_ok_response.append(res)
                    if len(not_ok_response) > 5:
                        return res_json, res
                else:
                    return res_json, res
            except ValueError:
                io_stderr_print(u'retry {}'.format(res.url))
                if res.url.startswith(u'https://login.sina.com.cn/'):
                    self._cookie = _get_chrome_cookies()
                time.sleep(t)
                t += 3
        else:
            raise ValueError('max times tried')

    def get_weibo_containerid(self, uid):

        r, res = self._access_net(u'https://m.weibo.cn/api/container/getIndex'
                                  , params={u'type': u'uid', u'value': uid})

        # jsonpath.jsonpath(r,u'$.userInfo.toolbar_menus[2].params.menu_list[0].actionlog.oid')[0]
        return jsonpath.jsonpath(r, u'$.tabsInfo.tabs[1].containerid')[0]

    def iter_weibo(self, uid, containerid):

        count = 1

        for page in range(1, 100000):

            r, res = self._access_net(u'https://m.weibo.cn/api/container/getIndex'
                                      , params={u'containerid': containerid, u'type': u'uid', u'page': page})

            ok = jsonpath.jsonpath(r, u'$.ok')[0]

            if not (ok == 1):
                io_stderr_print(u'not ok {}'.format(res.url))
                io_stderr_print(res.content[:500:])
                break

            next_page = jsonpath.jsonpath(r, u'$.cardlistInfo.page')[0]
            cards = jsonpath.jsonpath(r, u'$.cards')[0]

            for card in cards:
                v = self._parse_weibo_card(card)
                if v:
                    v.update(index=count)
                    yield v
                    count += 1

            if next_page is None:
                io_stderr_print(u'next page is None {}'.format(res.url))
                io_stderr_print(res.content[:500:])
                break

        else:
            io_stderr_print(u'page run out')

    def _parse_weibo_card(self, card):
        card_type = jsonpath.jsonpath(card, u'$.card_type')[0]

        # 默认 card_type == 9 是微博 多量看看是不是这样
        if card_type == 11:  # 安插的广告
            return {}

        weibo_id = jsonpath.jsonpath(card, u'$.mblog.id')[0]

        original_pic = jsonpath.jsonpath(card, u'$.mblog.original_pic')
        if original_pic: original_pic = original_pic[0]

        text = []

        create_at = jsonpath.jsonpath(card, u'$.mblog.created_at')
        if create_at: create_at = create_at[0]

        source = jsonpath.jsonpath(card, u'$.mblog.source')
        if source: text.append(u'[来自:{}] '.format(source[0]))
        title = jsonpath.jsonpath(card, u'$.mblog.title.text')
        if title: text.append(u'[{}] '.format(title[0]))

        t = jsonpath.jsonpath(card, u'$.mblog.raw_text')
        if not t: t = jsonpath.jsonpath(card, u'$.mblog.text')
        if t: text.append(t[0])

        retweeted = jsonpath.jsonpath(card, u'$.mblog.retweeted_status.text')
        if retweeted:
            retweeted = u'[{}] {}'.format(
                jsonpath.jsonpath(card, u'$.mblog.retweeted_status.id')[0]
                , retweeted[0])

        bid = jsonpath.jsonpath(card, u'$.mblog.bid')[0]
        uid = jsonpath.jsonpath(card, u'$..mblog.user.id')[0]
        this_weibo_url = u'http://weibo.com/{}/{}'.format(uid, bid)

        comments_count = jsonpath.jsonpath(card, u'$.mblog.comments_count')

        pics = []
        ps = jsonpath.jsonpath(card, u'$.mblog.pics')
        if ps:
            ps = ps[0]
            for p in ps:
                pics.append(jsonpath.jsonpath(p, u'$.large.url')[0])

        return {
            u'id': weibo_id,
            u'url': this_weibo_url,
            u'created_at': create_at,
            u'text': u''.join(text),
            u'from': jsonpath.jsonpath(card, u'$.mblog.user.screen_name')[0],
            u'retweeted': retweeted,
            u'comments': self.weibo_comments(weibo_id, min(comments_count, 1000)),
            u'pics': pics,
        }

    def weibo_comments(self, weibo_id, comments_count):
        comments = []
        
        for page_comment in (1, 1000):
            r_comment, res_comment = self._access_net(u'https://m.weibo.cn/api/comments/show'
                                                      , params={u'id': weibo_id, u'page': page_comment})

            ok = jsonpath.jsonpath(r_comment, u'$.ok')[0]

            if not (ok == 1):
                break

            datas = jsonpath.jsonpath(r_comment, u'$.data')[0]
            for data in datas:
                cm_screen_name = jsonpath.jsonpath(data, u'$.user.screen_name')[0]
                cm_create_at = jsonpath.jsonpath(data, u'$.created_at')[0]
                cm_source = jsonpath.jsonpath(data, u'$.source')[0]
                cm_text = jsonpath.jsonpath(data, u'$.text')[0]

                comments.append(
                    u'{} 在 {} 使用设备 {} 回复内容: {}'.format(cm_screen_name, cm_create_at, cm_source, cm_text)
                )
                if len(comments) == comments_count: break

        comments.reverse()
        return comments


def print_weibo(wb):
    io_print(u'{} {}: {}'.format(
        wb.get(u'index'), wb.get(u'from'), wb.get(u'created_at')))

    wb_id = wb.get(u'id')
    url1 = wb.get(u'url')
    url2 = u'https://m.weibo.cn/status/{}'.format(wb_id)
    io_print(u'    id: {}   {}   {}'.format(wb_id, url1, url2))
    io_print(u'    {}'.format(wb.get(u'text')))

    for i, pic_url in enumerate(wb.get(u'pics')):
        io_print(u'    图片{} {}'.format(i + 1, pic_url))

    io_print(u'    转发自:{}'.format(wb.get(u'retweeted')))

    for i, comment in enumerate(wb.get(u'comments', [])):
        io_print(u'    评论{} {}'.format(i + 1, comment))


def user(dest_uid):
    obj = weibo()

    weibo_containerid = obj.get_weibo_containerid(dest_uid)

    for v in obj.iter_weibo(dest_uid, weibo_containerid):
        print_weibo(v)
        print('')


def entry():
    tombkeeper = u'1401527553'
    user(tombkeeper)


if __name__ == '__main__':
    entry()
