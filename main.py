import random
import time

from gen_fake_people import person as rand_person
import requests
import logging
import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')


class Agent:
    def __init__(self, url, seed):
        self.url = url
        self.seed = seed
        random.seed(seed)
        self.basic_infos = None
        self.session = requests.session()
        self.login_as_admin()

    def post(self, api, *, data=None, json=None):
        resp = self.session.post(f'{self.url}{api}', json=json, data=data)
        return resp.json()

    def put(self, api, *, data=None, json=None):
        resp = self.session.put(f'{self.url}{api}', json=json, data=data)
        return resp.json()

    def get(self, api, *, params=None):
        resp = self.session.get(f'{self.url}{api}', params=params)
        return resp.json()

    def _check_basic_call(self):
        if self.basic_infos is None:
            raise Exception('shall call fill_basic() first')

    def login_as_admin(self):
        logging.info('register')
        resp = self.post('/api/user/register', json={
            'username': 'super_user',
            'password': 'password',
            'authorities': {
                'basic': {'create': True, 'read': True, 'update': True, 'delete': True, 'backup': True,
                          'restore': True},
                'complex': {'create': True, 'read': True, 'update': True, 'delete': True, 'backup': True,
                            'restore': True},
                'moral': {'create': True, 'read': True, 'update': True, 'delete': True, 'backup': True,
                          'restore': True},
                'punish': {'create': True, 'read': True, 'update': True, 'delete': True, 'backup': True,
                           'restore': True},
                'log': {'read': True}
            }
        })
        logging.info('resp: ' + str(resp))

        logging.info('login')
        resp = self.post('/api/user/login', json={
            'username': 'super_user',
            'password': 'password'
        })
        logging.info('resp: ' + str(resp))

    def fill_all(self):
        self.fill_basic()
        self.fill_complex()
        self.fill_moral()
        self.fill_punish()

    departments = '软件学院 大数据学院 微电子学院 管理学院 计算机科学技术学院 经济学院 法学院 数学科学学院 物理学系 化学系'.split(' ')
    n_basic = 10
    n_complex = 10
    n_moral = 10
    n_punish = 10

    def fill_basic(self):
        self.basic_infos = []
        job_no_pool = set(range(10000000, 99999999))
        job_nos = random.sample(job_no_pool, k=self.n_basic)

        for i, job_no in enumerate(job_nos):
            person = rand_person()
            basic = {
                'jobNo': job_no,
                'name': person['name'],
                'department': random.choice(self.departments),
                'phone': person['phone'],
                'hired': 1 if random.random() > 0.1 else 0
            }
            self.basic_infos.append(basic)
            resp = self.put('/api/table/basic', data=basic)
            if resp['ecode'] != '0':
                raise ConnectionError('resp is ' + str(resp))
            logging.info(f'insert {i + 1} / {self.n_basic} basics, resp={resp}')

        assert self.basic_infos, 'After this call, self.basic_info should be filled'


    def _rand_date(self, end_time=None):
        end_time = end_time or datetime.datetime.now()
        start_time = end_time + datetime.timedelta(days=-1000)
        a1 = tuple(start_time.timetuple()[0:9])  # 设置开始日期时间元组（2020-04-11 16:30:21）
        a2 = tuple(end_time.timetuple()[0:9])  # 设置结束日期时间元组（2020-04-11 16:33:21）
        start = int(time.mktime(a1))  # 生成开始时间戳
        end = int(time.mktime(a2))  # 生成结束时间戳
        t = random.randint(start, end)  # 在开始和结束时间戳中随机取出一个
        date_tuple = time.localtime(t)  # 将时间戳生成时间元组
        date = time.strftime("%Y-%m-%d", date_tuple)
        return date


    def _fill_complex_field(self):
        # inspectCategory, inspectReason, inspectResult
        cate_str_list = ['入职考察', '升职考察', '作风考察', '例行考察']
        reason_str_list = ['常规', '特殊', '抽查']
        result_str_list = ['通过', '不通过', '待定', '取消']

        for field in cate_str_list:
            resp = self.put('/api/field/inspectCategory', data={
                'field': field
            })
            logging.info(f'create inspect category, resp = {resp}')
        for field in reason_str_list:
            resp = self.put('/api/field/inspectReason', data={
                'field': field
            })
            logging.info(f'create inspect reason, resp = {resp}')

        for field in result_str_list:
            resp = self.put('/api/field/inspectResult', data={
                'field': field
            })
            logging.info(f'create inspect result, resp = {resp}')

        logging.info('getting complex fields')

        resp = self.get('/api/field/inspectCategory/list')
        logging.info('inspect category: ' + str(resp))
        if resp['ecode'] != '0':
            raise ConnectionError('resp = ' + str(resp))
        self.inspect_categories = resp['content']

        resp = self.get('/api/field/inspectReason/list')
        logging.info('inspect reason: ' + str(resp))
        if resp['ecode'] != '0':
            raise ConnectionError('resp = ' + str(resp))
        self.inspect_reasons = resp['content']

        resp = self.get('/api/field/inspectResult/list')
        logging.info('inspect result: ' + str(resp))
        if resp['ecode'] != '0':
            raise ConnectionError('resp = ' + str(resp))
        self.inspect_results = resp['content']

    def fill_complex(self):
        self._check_basic_call()
        self._fill_complex_field()
        rand_basics = random.choices(self.basic_infos, k=self.n_complex)
        for i, basic in enumerate(rand_basics):
            complex = {
                'jobNo': basic['jobNo'],
                'name': basic['name'],
                'department': basic['department'],
                'inspectAt': self._rand_date(),
                'inspectCategory': random.choice(self.inspect_categories)['fid'],
                'inspectReason': random.choice(self.inspect_reasons)['fid'],
                'auditDepartments': random.choice(self.departments)
            }
            if random.random() > .3:
                complex['startDepartment'] = random.choice(self.departments)
            if random.random() > .3:
                complex['operator'] = random.choice(self.basic_infos)['name']
            if random.random() > .5:
                complex['inspectResult'] = random.choice(self.inspect_results)['fid']
            resp = self.put('/api/table/complex', data=complex)
            if resp['ecode'] != '0':
                raise ConnectionError('resp is ' + str(resp))
            logging.info(f'insert {i + 1} / {self.n_complex} complexes, resp={resp}')

    def _fill_moral_field(self):
        type_str_list = ['学术问题', '生活问题', '经济问题']
        cate_str_list = ['警告', '严重警告', '通报批评', '处分', '开除']
        desp_str_list = ['经核查确有问题', '经各方综合审查，确有问题', '存疑']

        for field in type_str_list:
            resp = self.put('/api/field/type', data={
                'field': field
            })
            logging.info(f'create moral type, resp = {resp}')
        for field in cate_str_list:
            resp = self.put('/api/field/resultCategory', data={
                'field': field
            })
            logging.info(f'create moral result category, resp = {resp}')

        # for field in desp_str_list:
        #     resp = self.put('/api/field/resultDesc', data={
        #         'field': field
        #     })
        #     logging.info(f'create moral result desc, resp = {resp}')

        logging.info('getting moral fields')

        resp = self.get('/api/field/type/list')
        logging.info('moral type: ' + str(resp))
        if resp['ecode'] != '0':
            raise ConnectionError('resp = ' + str(resp))
        self.moral_types = resp['content']

        resp = self.get('/api/field/resultCategory/list')
        logging.info('moral result category: ' + str(resp))
        if resp['ecode'] != '0':
            raise ConnectionError('resp = ' + str(resp))
        self.moral_result_categories = resp['content']

        # resp = self.get('/api/field/resultDesc/list')
        # logging.info('moral result desc: ' + str(resp))
        # if resp['ecode'] != '0':
        #     raise ConnectionError('resp = ' + str(resp))
        # self.moral_result_descriptions = resp['content']

    def fill_moral(self):
        self._check_basic_call()
        self._fill_moral_field()
        rand_basics = random.choices(self.basic_infos, k=self.n_moral)
        for i, basics in enumerate(rand_basics):
            moral = {
                'jobNo': basics['jobNo'],
                'name': basics['name'],
                'department': basics['department'],
                'type': random.choice(self.moral_types)['fid'],
                'recordAt': self._rand_date()
            }
            if random.random() > 0.5:
                moral['situation'] = '问题线索情况_' + random.choice('一 二 三 四 甲 乙 丙 丁'.split())
            resp = self.put('/api/table/moral', data=moral)
            if resp['ecode'] != '0':
                raise ConnectionError('resp is ' + str(resp))
            logging.info(f'insert {i + 1} / {self.n_moral} morals, resp={resp}')

    def fill_punish(self):
        self._check_basic_call()
        rand_basics = random.choices(self.basic_infos, k=self.n_punish)
        for i, basics in enumerate(rand_basics):
            punish = {
                'jobNo': basics['jobNo'],
                'name': basics['name'],
                'department': basics['department'],
                'oSchool': random.choice(['复旦大学', '复旦大学医学院']),
                'punishAt': self._rand_date(),
                'punishBy': random.choice(['教务处', '党委']),
                'detail': '处分内容_' + random.choice('一 二 三 四 甲 乙 丙 丁'.split()),
                'punishTill': self._rand_date(end_time=datetime.datetime.now() + datetime.timedelta(days=2000)),
                'relieveReason': random.choice(['惩罚期满', '表现良好', '表现一般']),
            }
            resp = self.put('/api/table/punish', data=punish)
            if resp['ecode'] != '0':
                raise ConnectionError('resp is ' + str(resp))
            logging.info(f'insert {i + 1} / {self.n_moral} punishes, resp={resp}')
        pass


def main():
    url = 'http://localhost:17426'
    agent = Agent(url, 0)
    agent.fill_all()


if __name__ == '__main__':
    main()
