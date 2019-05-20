import random, time, pymysql, datetime
import execjs, redis, json, re
import base64, threadpool
import hashlib
import requests
from fake_useragent import UserAgent
from DBUtils.PooledDB import PooledDB


class Test2():
    def __init__(self):
        self.ua = UserAgent()
        # vjl5x加密文件读取
        with open('cpws.js', 'r', encoding='utf-8') as f:
            content_vjl5x = f.read()
        self.vjl5x_js = execjs.compile(content_vjl5x)
        # 文书加密docid
        with open('docid.js', 'r', encoding='utf-8') as f:
            content_doc = f.read()
        self.ctx3 = execjs.compile(content_doc)
        self.db_pool = PooledDB(pymysql, 2, host="10.0.72.2", user='root',
                                passwd='Qfa6csic', db='Company', port=3306, charset="utf8mb4")

    # 生成指定时间段的时间，返回list
    def create_time(self, start, end):
        # start = '2019-01-01'
        # end = '2019-04-15'
        datestart = datetime.datetime.strptime(start, '%Y-%m-%d')
        dateend = datetime.datetime.strptime(end, '%Y-%m-%d')
        time_list = []
        while datestart < dateend:
            datestart += datetime.timedelta(days=1)
            # print(datestart.strftime('%Y-%m-%d'))
            time_list.append(datestart.strftime('%Y-%m-%d'))
        return time_list

    # 获取vjkl5
    def get_vjkl5(self):
        timeout = 5
        while 1:
            proxies = self.get_proxies()
            try:
                session = requests.session()
                url_1 = 'http://wenshu.court.gov.cn/List/List?sorttype=1&conditions=searchWord+1+AJLX++%E6%A1%88%E4%BB%B6%E7%B1%BB%E5%9E%8B:%E5%88%91%E4%BA%8B%E6%A1%88%E4%BB%B6'
                headers_1 = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
                    # "Referer": "http://wenshu.court.gov.cn/list/list/?sorttype=1&number=T9EYXNMW&guid=690587f5-b606-efd81bf9-71543b2db841&conditions=searchWord++CPRQ++%E8%A3%81%E5%88%A4%E6%97%A5%E6%9C%9F:2019-04-01%20TO%202019-04-01",
                    "Host": "wenshu.court.gov.cn",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                    "Origin": "http://wenshu.court.gov.cn",
                    # "X-Requested-With": "XMLHttpRequest",
                    # "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",

                }
                response_1 = session.get(url=url_1,
                                         headers=headers_1,
                                         proxies=proxies,
                                         timeout=timeout
                                         )
                html = response_1.text

                waws_cid = response_1.headers['Set-Cookie'].split(';')[0]

                dynamicurl = re.findall(r'dynamicurl="(.*?)";0', html, re.S)[0]
                wzwsquestion = re.findall(r'wzwsquestion="(.*?)";0', html, re.S)[0]
                wzwsfactor = re.findall(r'wzwsfactor="(.*?)";0', html, re.S)[0]

                result_1 = self.get_url_first(wzwsquestion, wzwsfactor, dynamicurl)
                url_2 = 'http://wenshu.court.gov.cn{}'.format(result_1)
                # print(url_2)
                headers_1['Referer'] = url_1
                response_2 = session.get(url=url_2, headers=headers_1, proxies=proxies, timeout=timeout)
                vjkl5 = response_2.headers['Set-Cookie'].split(';')[0]
                # print(response_2.text)
                # print('-------------------')
                # print(vjkl5)
                # print(waws_cid)
                # print('-------------------')
                if 'vjkl5' in vjkl5:
                    return vjkl5
                else:
                    print('--Error:获取vjl5x时出现问题，暂停10s--')
                    # time.sleep(1)

            except:
                print('--Error:get_vjkl5出现错误--')

    # 生成guid
    def get_guid(self):
        """
        生成guid
        :return:
        """

        def createGuid():
            return str(hex((int(((1 + random.random()) * 0x10000)) | 0)))[3:]

        guid = '{}{}-{}-{}{}-{}{}{}'.format(createGuid(), createGuid(),
                                            createGuid(), createGuid(),
                                            createGuid(), createGuid(),
                                            createGuid(), createGuid(),
                                            )
        return guid

    # 计算生成第一次访问的连接
    def get_url_first(self, wzwsquestion, wzwsfactor, dynamicurl):
        try:
            nub_ = 0
            for question in wzwsquestion:
                nub_ += ord(question)
            nub_ *= int(wzwsfactor)
            nub_ = nub_ + 111111
            challenge = 'WZWS_CONFIRM_PREFIX_LABEL{}'.format(nub_)
            wzwschallenge = 'wzwschallenge={}'.format(str(base64.b64encode(challenge.encode('utf-8')), 'utf-8'))
            # print(wzwschallenge)
            result = '{}?{}'.format(dynamicurl, wzwschallenge)
            return result
        except:
            print('--Error:方法get_url_first--')
            # time.sleep(60)

    # 解析docid，通过Runeval和文书id
    def decrypt_id(self, RunEval, id):

        # while 1:
        try:
            js = self.ctx3.call("GetJs", RunEval)
            js_objs = js.split(";;")
            js1 = js_objs[0] + ';'
            js2 = re.findall(r"_\[_\]\[_\]\((.*?)\)\(\);", js_objs[1])[0]
            key = self.ctx3.call("EvalKey", js1, js2)
            key = re.findall(r"\"([0-9a-z]{32})\"", key)[0]
            docid = self.ctx3.call("DecryptDocID", key, id)
            return docid, False
        except Exception as e:
            print(e)
            print('--Error:方法decrypt_id出现错误--docid解密--')
            return '', True
            # time.sleep(3)

    # 获取ip
    def get_proxies(self):
        while 1:
            try:
                redis_conn = redis.StrictRedis(host='localhost',
                                               password='Cs123456.',
                                               port=6379,
                                               db=1
                                               )
                redis_ip = redis_conn.blpop('ips')
                ip = json.loads(redis_ip[1].decode('UTF-8'))
                # print('--------{}-------'.format(ip['ip']))
                proxy = {
                    'http': 'http://{}'.format(ip['ip'])
                }
                return proxy
            except Exception as e:
                # print(e)
                # print('--Error:获取ip出现错误--')
                pass

    # 根据vjkl5获取vl5x
    def get_vl5x(self, cookie):
        vl5x = self.vjl5x_js.call("getvl5x", cookie.replace('vjkl5=', ''))
        return vl5x

    # 获取列表信息
    def get_list(self, court, page_count, search_time):
        count_while = 0
        abcd = True
        while abcd:
            proxies = self.get_proxies()
            timeout = 5
            page_size = 20
            try:
                vjkl5 = self.get_vjkl5()
                # print(vjkl5)
                vl5x = self.get_vl5x(vjkl5)
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
                    # "Referer": "http://wenshu.court.gov.cn/list/list/?sorttype=1&number=T9EYXNMW&guid=690587f5-b606-efd81bf9-71543b2db841&conditions=searchWord++CPRQ++%E8%A3%81%E5%88%A4%E6%97%A5%E6%9C%9F:2019-04-01%20TO%202019-04-01",
                    "Host": "wenshu.court.gov.cn",
                    "Accept": "*/*",
                    "Origin": "http://wenshu.court.gov.cn",
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Cookie": vjkl5,
                }
                url = 'http://wenshu.court.gov.cn/List/ListContent'
                Param = '裁判日期:{} TO {},{}'.format(search_time, search_time, court)
                # print(Param)
                data = {
                    "Param": Param,
                    "Index": page_count,
                    "Page": page_size,
                    "Order": "法院层级",
                    "Direction": "asc",
                    "vl5x": vl5x,
                    "guid": self.get_guid(),
                }

                decrypt = True
                while decrypt:
                    response = requests.post(url,
                                             data=data,
                                             headers=headers,
                                             proxies=proxies,
                                             timeout=timeout
                                             )
                    json_ = json.loads(response.text)
                    json_list = json.loads(json_)

                    RunEval = ''
                    if len(json_list) > 0:
                        for jl in json_list:
                            if 'RunEval' in jl:
                                RunEval = jl.get('RunEval', '--')
                                # print(RunEval)
                            else:
                                ws_id = jl.get('文书ID', '--')
                                # print(ws_id)
                                if RunEval is not '-' and ws_id is not '-':
                                    docid, decrypt = self.decrypt_id(RunEval, ws_id)
                                    if decrypt is False:
                                        ws_info_url = 'http://wenshu.court.gov.cn/CreateContentJS/CreateContentJS.aspx?DocID={}'.format(
                                            docid)
                                        # print(ws_info_url)
                                        self.get_ws_info(ws_info_url, search_time)
                                    else:
                                        print('--doc_id加密失败，重新请求--')
                        # print('------------------{}*****'.format(len(json_list)))
                        if len(json_list) - 1 == page_size:
                            return True
                        else:
                            return False
                    else:
                        print('--{}--无数据--'.format(Param))
                        return False
            except Exception as e:
                # print(e)
                if count_while >= 5:
                    abcd = False
                    print('--Error:方法get_list出现错误--')
                else:
                    count_while += 1
                    # time.sleep(2)

    # 获取文书详细信息
    def get_ws_info(self, url_1, search_time):

        abcd = True
        count_while = 1
        while abcd:
            html = self.get_info_html(url_1)
            try:

                json_info_1 = re.findall(r'stringify\((.*?)\);', html, re.S)[0]
                json_info_2 = re.findall(r'var jsonHtmlData = "(.*?)";', html, re.S)[0]
                json_2 = json.loads(json_info_2.replace('\\', ''))
                json_1 = json.loads(json_info_1)
                upload_date = json_1.get('上传日期', '--').replace('Date(', '').replace(')', '').replace('/', '')
                item = {
                    # 标题
                    "title": json_2.get('Title', ''),
                    # 公开时间
                    "pubdate": json_2.get('PubDate', ''),
                    # 网页内容
                    "html": json_2.get('Html', ''),
                    "doc_id": json_1.get('文书ID', ''),
                    "case_name": json_1.get('案件名称', ''),
                    "case_no": json_1.get('案号', ''),
                    "trial_procedure": json_1.get('审判程序', ''),
                    "upload_date": time.strftime('%Y-%m-%d', time.localtime(int(upload_date) / 1000)),
                    "case_type": json_1.get('案件类型', ''),
                    "correction_instrument": json_1.get('补正文书', ''),
                    "court_name": json_1.get('法院名称', ''),
                    "court_id": json_1.get('法院ID', ''),
                    "court_provinces": json_1.get('法院省份', ''),
                    "court_city": json_1.get('法院地市', ''),
                    "court_districts_counties": json_1.get('法院区县', ''),
                    "court_area": json_1.get('法院区域', ''),
                    "instrument_type": json_1.get('文书类型', ''),
                    "full_document_types": json_1.get('文书全文类型', ''),
                    "referee_date": json_1.get('裁判日期', ''),
                    "close_mode": json_1.get('结案方式', ''),
                    "level_of_effectiveness": json_1.get('效力层级', ''),
                    "unpublic_reasons": json_1.get('不公开理由', ''),
                    "DocContent": json_1.get('DocContent', ''),
                    "the_original_text_of_the_first_paragraph_of_the_text": json_1.get('文本首部段落原文', ''),
                    "the_original_part_of_the_information_of_litigant_participants": json_1.get('诉讼参与人信息部分原文', ''),
                    "the_original_text_of_the_proceedings_record_paragraph": json_1.get('诉讼记录段原文', ''),
                    "the_basic_situation_of_the_case_paragraph": json_1.get('案件基本情况段原文', ''),
                    "referee_essential_paragraph_original": json_1.get('裁判要旨段原文', ''),
                    "the_original_text_of_judgment_result_paragraph": json_1.get('判决结果段原文', ''),
                    "additional_text": json_1.get('附加原文', ''),
                    "judgement_date": search_time,
                    "text_end_original": json_1.get('文本尾部原文', '')
                }
                result = self.insert_db(item, search_time, json_1.get('法院名称', ''))
                print(result)
                abcd = False
            except Exception as e:
                if count_while >= 3:
                    print('--Error:方法get_ws_info出现错误--')
                    abcd = False
                else:
                    count_while += 1
                    # time.sleep(2)

    # 获取详细信息的页面
    def get_info_html(self, url_1):
        count_ = 0
        error_false = True
        timeout = 5
        while error_false:
            proxies = self.get_proxies()
            try:
                session = requests.session()
                headers_1 = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
                    # "Referer": "http://wenshu.court.gov.cn/list/list/?sorttype=1&number=T9EYXNMW&guid=690587f5-b606-efd81bf9-71543b2db841&conditions=searchWord++CPRQ++%E8%A3%81%E5%88%A4%E6%97%A5%E6%9C%9F:2019-04-01%20TO%202019-04-01",
                    "Host": "wenshu.court.gov.cn",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                    "Origin": "http://wenshu.court.gov.cn",
                    # "X-Requested-With": "XMLHttpRequest",
                    # "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",

                }
                response_1 = session.get(url=url_1,
                                         headers=headers_1, proxies=proxies, timeout=timeout
                                         )
                html = response_1.text
                dynamicurl = re.findall(r'dynamicurl="(.*?)";0', html, re.S)[0]
                wzwsquestion = re.findall(r'wzwsquestion="(.*?)";0', html, re.S)[0]
                wzwsfactor = re.findall(r'wzwsfactor="(.*?)";0', html, re.S)[0]

                result_1 = self.get_url_first(wzwsquestion, wzwsfactor, dynamicurl)
                url_2 = 'http://wenshu.court.gov.cn{}'.format(result_1)
                # print(url_2)
                headers_1['Referer'] = url_1
                response_2 = session.get(url=url_2, headers=headers_1, proxies=proxies, timeout=timeout)
                if 'window.location.href' not in response_2.text:
                    return response_2.text
                else:
                    print('--进入验证码页，再次请求--')

                    # time.sleep(2)
            except Exception as e:
                if count_ >= 10:
                    print('--Error:获取详细信息get_info_html出现问题--')
                    error_false = False
                else:
                    count_ += 1
                    # time.sleep(2)

    # 存入数据库
    def insert_db(self, datas, search_time, court_name):
        while 1:
            # print(datas)
            conn = self.db_pool.connection()
            cursor = conn.cursor()
            now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            try:

                keys = ','.join(datas.keys())
                values = ','.join(['%s'] * len(datas))
                sql = 'insert ignore into company_judicial_doc ({keys}) values({values})'.format(keys=keys,
                                                                                                 values=values)
                nub_ = cursor.execute(sql, tuple(datas.values()))
                conn.commit()
                cursor.close()
                conn.close()
                result = '--{}--Success:--{}条收录成功--{}--{}--'.format(now_time, nub_, search_time, court_name)
                return result
                # print(result)
            except Exception as e:
                conn.rollback()
                cursor.close()
                conn.close()
                print('--Error:方法insert_db报错--')
                time.sleep(60)

    # 获取查询日期下某省份下所有有数据的中级法院
    def get_time_court_list(self, search_time, parval):
        while 1:
            proxies = self.get_proxies()
            try:
                data = {
                    "Param": "裁判日期:{} TO {},法院地域:{}".format(search_time, search_time, parval),
                    "parval": parval,
                }
                # print(data)
                headers = {
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                    "Connection": "keep-alive",
                    "Content-Length": "173",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    # "Cookie": "Hm_lvt_d2caefee2de09b8a6ea438d74fd98db2=1556329837; _gscu_2116842793=56329837m7vf5550; _gscbrs_2116842793=1; ASP.NET_SessionId=iqthwxnvc3bzgi0wd4ms2rzr; wzws_cid=a1b2fbac088afe3984fa276c640ed47a96812c67a5a27ff79b28a1c784db4486ae4983407dacdd4ec8f850a445fe420434ff58d4546d97bc81501fb9eb7d62d0; vjkl5=b970b0ac95ffe75d33010218ba9d37947050fd82; Hm_lpvt_d2caefee2de09b8a6ea438d74fd98db2=1556353601; _gscs_2116842793=t56348424pp8km916|pv:37",
                    "Host": "wenshu.court.gov.cn",
                    "Origin": "http://wenshu.court.gov.cn",
                    # "Referer": "http://wenshu.court.gov.cn/list/list/?sorttype=1&number=0.7426800858147795&guid=298d1f5b-db6e-7db7ca98-018e74ac5119&conditions=searchWord++CPRQ++%E8%A3%81%E5%88%A4%E6%97%A5%E6%9C%9F:2019-04-01%20TO%202019-04-01",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
                    "X-Requested-With": "XMLHttpRequest",
                }
                url = 'http://wenshu.court.gov.cn/List/CourtTreeContent'
                response = requests.post(url, data=data, headers=headers, proxies=proxies, timeout=5)

                mid_court_json_1 = json.loads(response.text)
                mid_court_json_2 = json.loads(mid_court_json_1)
                result_list = []
                for court_json in mid_court_json_2[0]['Child']:
                    if 'NULL' not in court_json['id']:
                        result_list.append(court_json)
                # print(result_list)
                return result_list
            except Exception as e:
                print(e)
                print('--Error:方法get_time_court_list出现错误--')
                # time.sleep(2)

    # 获取基层法院信息信息
    def get_jiceng_court_list(self, search_time, parval):
        count_ = 0
        while 1:
            proxies = self.get_proxies()
            try:
                data = {
                    "Param": "裁判日期:{} TO {},中级法院:{}".format(search_time, search_time, parval),
                    "parval": parval,
                }
                headers = {
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                    "Connection": "keep-alive",
                    "Content-Length": "173",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    # "Cookie": "Hm_lvt_d2caefee2de09b8a6ea438d74fd98db2=1556329837; _gscu_2116842793=56329837m7vf5550; _gscbrs_2116842793=1; ASP.NET_SessionId=iqthwxnvc3bzgi0wd4ms2rzr; wzws_cid=a1b2fbac088afe3984fa276c640ed47a96812c67a5a27ff79b28a1c784db4486ae4983407dacdd4ec8f850a445fe420434ff58d4546d97bc81501fb9eb7d62d0; vjkl5=b970b0ac95ffe75d33010218ba9d37947050fd82; Hm_lpvt_d2caefee2de09b8a6ea438d74fd98db2=1556353601; _gscs_2116842793=t56348424pp8km916|pv:37",
                    "Host": "wenshu.court.gov.cn",
                    "Origin": "http://wenshu.court.gov.cn",
                    # "Referer": "http://wenshu.court.gov.cn/list/list/?sorttype=1&number=0.7426800858147795&guid=298d1f5b-db6e-7db7ca98-018e74ac5119&conditions=searchWord++CPRQ++%E8%A3%81%E5%88%A4%E6%97%A5%E6%9C%9F:2019-04-01%20TO%202019-04-01",
                    "User-Agent": self.ua.random,
                    "X-Requested-With": "XMLHttpRequest",
                }
                url = 'http://wenshu.court.gov.cn/List/CourtTreeContent'
                response = requests.post(url, data=data, headers=headers, proxies=proxies, timeout=5)

                mid_court_json_1 = json.loads(response.text)
                mid_court_json_2 = json.loads(mid_court_json_1)
                result_list = []
                for court_json in mid_court_json_2[0]['Child']:
                    if 'NULL' not in court_json['id']:
                        result_list.append(court_json)
                # print(result_list)
                return result_list
            except Exception as e:
                if count_ >= 5:
                    # print(e)
                    print('--Error:方法get_jiceng_court_list出现错误--')
                    return []
                else:
                    count_ += 1
                    time.sleep(2)

    # 获取查询日期和省份下的所有有信息的法院
    def get_all_court(self, search_time, praval):
        court_list = []
        if praval != '最高人民法院':
            result_list = self.get_time_court_list(search_time, praval)

            for r in result_list:

                count_anjian = int(r['Value'])
                if count_anjian >= 0:
                    # print('------------------------------------------------------------------------------------{}--{}--'.format(r['Value'], r['Key']))
                    court_list.append([r['Field'], r['Key']])
                    jc_result_list = self.get_jiceng_court_list(search_time, r['Key'])
                    for jr in jc_result_list:
                        court_list.append([jr['Field'], jr['Key']])
                else:
                    # pass
                    court_list.append([r['Field'], r['Key']])
        else:
            court_list.append(['法院层级', '最高法院'])
        return court_list

    def run(self, search_time, praval):
        print('--开始--{}--{}--'.format(search_time, praval))
        court_list = self.get_all_court(search_time, praval)
        for court in court_list:
            court_info = '{}:{},法院层级:{}'.format(court[0], court[1], court[0])
            if '最高法院' in court_info:
                court_info = '{}:{}'.format(court[0], court[1])
            result = True
            page_count = 1

            while result:
                # print(court_info)
                result = self.get_list(court_info, page_count, search_time)
                if result:

                    if page_count >= 20:
                        print('--Info:{}--页数超出20--停止--'.format(court_info))
                        result = False
                    else:
                        page_count += 1
                        print('--Success:法院：{}--进入第--{}--页--'.format(court_info, page_count))
                        # else:
                        #     page_count += 1
                        #     print('--Success:法院：{}--进入第--{}--页--'.format(court_info, page_count))


if __name__ == '__main__':
    t = Test2()
    # 时间段list
    start = '2015-06-04'
    end = '2016-01-01'

    search_time_list = t.create_time(start, end)
    # 省份list
    praval_list = [
        '最高人民法院',
        '北京市',
        '天津市',
        '河北省',
        '山西省',
        '内蒙古自治区',
        '辽宁省',
        '辽宁省沈阳市中级人民法院',
        '吉林省',
        '黑龙江省',
        '上海市',
        '江苏省',
        '浙江省',
        '安徽省',
        '福建省',
        '江西省',
        '山东省',
        '河南省',
        '湖北省',
        '湖南省',
        '广东省',
        '广西壮族自治区',
        '海南省',
        '重庆市',
        '四川省',
        '贵州省',
        '云南省',
        '西藏自治区',
        '陕西省',
        '甘肃省',
        '青海省',
        '宁夏回族自治区',
        '新疆维吾尔自治区',
        '新疆维吾尔自治区高级人民法院生产建设兵团分院']
    task_param_list = []
    for search_time in search_time_list:
        for praval in praval_list:
            task_param_list.append(([search_time, praval], None))
    # print(task_param_list)
    pool = threadpool.ThreadPool(20)
    reqs = threadpool.makeRequests(t.run, task_param_list)
    for req in reqs:
        pool.putRequest(req)

    pool.wait()
