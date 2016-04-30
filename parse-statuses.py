# vim:fdm=marker:
import sys
import os
import re
import glob

def Help():#{{{
    print('''
NAME
    {0}(V1) - parse douban statuses 处理豆瓣广播

USAGE
    {0} doubaner_id

    doubaner_id: 豆瓣个人主页大头像右侧的用户标识，或者个人主页URL地址最右两个//之间的单词或数字。

EXAMPLE
    {0} ahbei
'''.format(os.path.basename(sys.argv[0])))
    sys.exit()
#}}}

if len(sys.argv) != 2:
    Help()

################################################################
# 运行参数

doubaner_id = sys.argv[1]
output_by_year = False # TODO

################################################################

# RegEx and Template #{{{
re_spaces = re.compile(r'\s\s+', re.DOTALL)
re_tag = re.compile(r'<.+?>', re.DOTALL)
re_status_item = re.compile(r'<div class="status-item".+?<!-- \d+, \w+\.html -->', re.DOTALL)
re_text = re.compile(r'<div class="text">.+?</div>', re.DOTALL)
re_title = re.compile(r'<div class="title">\s*<a href="([^"]+)" .+?</div>', re.DOTALL)
re_quote = re.compile(r'<blockquote>.+?</blockquote>', re.DOTALL)
re_time = re.compile(r'<span class="created_at" title="([^"]+)"><a href="([^"]+)">', re.DOTALL)
re_reply = re.compile(r'\b\d+回应\b', re.DOTALL)
status_item_template = '''
<div class="status-item{0}">
<div class="text">{1}{2}</div>
<div class="quote">{3}</div>
<div class="time">{4}</div>
</div>
'''
#}}}
def RemoveTags(html_string):#{{{
    return re_tag.sub('', html_string)
#}}}
def ShortenSpaces(html_string):#{{{
    return re_spaces.sub(' ', html_string)
#}}}

filelist = glob.glob('./{uid}/statuses/*.html'.format(uid = doubaner_id))
filelist.sort()

doubaner_name = None#{{{
if len(filelist) > 0:
    html = open(filelist[0], encoding = 'utf-8').read()
    m_title = re.search(r'<title>\s*(\S+?)的广播\s*</title>', html, re.DOTALL)
    m_account = re.search(r'<span>(\S+?)的帐号</span>', html, re.DOTALL)
    if m_title and m_account:
        doubaner_name = m_title.group(1)
        account_name = m_account.group(1)
        if doubaner_name == '我' and doubaner_name != account_name:
            is_self_backup = True
            doubaner_name = account_name
        else:
            is_self_backup = False
    else:
        print('广播文件中找不到用户昵称。')
        sys.exit()
else:
    print('找不到广播文件。')
    sys.exit()
#}}}

class Output:#{{{
    def __init__(self, filename):#{{{
        self.output_file = open(filename, 'w', encoding = 'utf-8')
        self.output_file.write('''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{uname}的广播</title>
'''.format(uname = doubaner_name))
        self.output_file.write('''<style>
body { color: #403333; font-size: 10pt; }
a { color: #06c; text-decoration: none; }
a:hover { color: #900; text-decoration: underline; }
.status-item { border-bottom: #999 1px dashed; }
.reshare { border-left: #545652 1px solid; }
.time { color: #999; }
</style>
</head>
<body>
''')
#}}}
    def Write(self, is_reshare, status_text, subject, quote, time_bar):#{{{
        self.output_file.write(status_item_template.format(
                ' reshare' if is_reshare else '',
                status_text,
                subject,
                quote,
                time_bar))
#}}}
    def Finish(self):#{{{
        self.output_file.write('''
</body>
</html>
''')
        self.output_file.close()
#}}}
#}}}

output_filename = './{uid}/{uid}-statuses-all.html'.format(uid = doubaner_id)
output = Output(output_filename)

parsed_statuses = set()
for filename in filelist:#{{{
    html = open(filename, encoding = 'utf-8').read()
    status_items = re_status_item.findall(html)

    print(filename, len(status_items))

    for item in status_items:#{{{
        if is_self_backup:
            is_reshare = item.find('data-action-type="unreshare"') > -1
        else:
            is_reshare = item.find('<span class="reshared_by">') > -1
        m_text = re_text.search(item)
        status_text = ShortenSpaces(RemoveTags(m_text.group(0))) if m_text else ''
        m_title = re_title.search(item)
        if m_title:
            title_text = ShortenSpaces(RemoveTags(m_title.group(0)))
            title_link = m_title.group(1)
            subject = ' <a href="{0}">{1}</a>'.format(title_link, title_text)
        elif item.find('group-pics') > -1:
            subject = ' 图片...'
        else:
            subject = ''
        m_quote = re_quote.search(item)
        quote = RemoveTags(m_quote.group(0)).strip() if m_quote else ''
        m_time = re_time.search(item)
        if m_time:
            created_at = m_time.group(1)
            status_link = m_time.group(2)
            m_reply = re_reply.search(item)
            reply = m_reply.group(0) if m_reply else ''
            time_bar = '<a href="{0}">{1}</a> {2}'.format(status_link, created_at, reply)
            status_token = status_link[status_link.rfind('/',0,-1)+1:-1]
        else:
            time_bar = ''
            status_token = item
        if status_token not in parsed_statuses:
            parsed_statuses.add(status_token)
            output.Write(is_reshare, status_text, subject, quote, time_bar)
#}}}
#}}}

output.Finish()
