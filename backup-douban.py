# vim:fdm=marker:
import sys
import os
import re
import pycurl
import io
import datetime

def Help():#{{{
    print('''
NAME
    {0}(V1) - backup douban statuses 备份豆瓣广播

USAGE
    {0} doubaner_id page_range

    doubaner_id: 豆瓣个人主页大头像右侧的用户标识，或者个人主页URL地址最右两个//之间的单词或数字。
    page_range: 页码范围，可以是一个数字，或用英文减号(-)连接的两个数字。

EXAMPLE
    {0} ahbei 1
    {0} ahbei 1-10
'''.format(os.path.basename(sys.argv[0])))
    sys.exit()
#}}}

if len(sys.argv) != 3:
    Help()

################################################################
# 运行参数

doubaner_id = sys.argv[1]
backup_type = 'statuses' # TODO: notes reviews
if re.match(r'^\d+$', sys.argv[2]):
    number = int(sys.argv[2])
    page_range = (number, number)
elif re.match(r'^\d+-\d+$', sys.argv[2]):
    page_range = tuple(int(v) for v in sys.argv[2].split('-'))
else:
    Help()

cookie_file = 'douban-cookies.txt'
cainfo_file = 'cacert.pem'

today = 99999999 - int(datetime.date.today().strftime('%Y%m%d')) # newer date should be sorted to the front

################################################################

def ReadURL(url):#{{{
    buffer = io.BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.CAINFO, cainfo_file)
    c.setopt(c.COOKIEFILE, cookie_file)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    c.close()
    return buffer.getvalue()
#}}}

not_found_count = 0
if backup_type == 'statuses':#{{{
    dirpath = '{uid}/{ctype}'.format(uid = doubaner_id, ctype = backup_type)
    if not os.path.isdir(dirpath):
        os.makedirs(dirpath)
    base_url = 'https://www.douban.com/people/{uid}/{ctype}'.format(uid = doubaner_id, ctype = backup_type)
    for i in range(page_range[0], page_range[1] + 1):
        url = base_url + '?p={page}'.format(page = i)
        output_file = dirpath + '/{date}-{page:03}.html'.format(date = today, page = i)
        print('backup', url)
        webpage_bytes = ReadURL(url)
        if webpage_bytes.find(b'class="status-item"') == -1:
            not_found_count += 1
            if not_found_count >= 2:
                break
        open(output_file, mode = 'wb').write(webpage_bytes)
#}}}
