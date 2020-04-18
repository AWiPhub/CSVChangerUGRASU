import cherrypy
import os
from jinja2 import Environment, FileSystemLoader
import csv
import re
from itertools import groupby
from collections import defaultdict
import string
import codecs, io
from io import StringIO, BytesIO
from datetime import datetime
from cherrypy import tools

env = Environment(loader=FileSystemLoader('html'))

class HelloWorld(object):

    SKIP_USER_NAMES = ['-', 'Администратор Пользователь', 'Администратор', 'под именем']
    
    @cherrypy.expose
    def index(self):
        data_to_show = ['Hello', 'world']
        tmpl = env.get_template('index.html')
        return tmpl.render(data=data_to_show)
        
    def parse_row(self, row):
        date, name = row[:2]
        date = datetime.strptime(date, '%d/%m/%y, %H:%M')
        return f'{name} {date.strftime("%d.%m.%y")}', (name.strip(), date)

    @cherrypy.expose
    def ObrAll(self, filename, target_encoding='1251', username=None):
        reader = csv.reader(StringIO(filename.file.read().decode('utf-8')))

        UsersList = []  # Изначальный список
        newlist = []  # Список без дубликатов
        frequency = {}

        # Исключения имён
        for row in reader:
            Date = re.sub(r'[^0-9./]+', r'', row[0][0:8])
            User = row[1]
            if User != '-' and User != 'Администратор Пользователь' and User != 'Администратор \u3000' and ("под именем" in User) == False:
                List = Date + ' ' + User
            UsersList.append(List)
        UsersList = [el for el, _ in groupby(UsersList)]

        # Избавление от дупликатов
        for i in UsersList:
            if i not in newlist:
                newlist.append(i)

        # Разбитие на "слова"
        newlist = ",".join(newlist)
        newlist = re.sub(r'[^0-9/,]+', r'', newlist)
        newlist = newlist.replace("/", ".")
        newlist = newlist.split(",")

        # Подсчёт
        for word in newlist:
            count = frequency.get(word, 0)
            frequency[word] = count + 1
        frequency_list = frequency.keys()

        file_out = StringIO()
        # with open(file_name + "UnicUserPerDay.csv", "w", newline="", encoding='utf-8') as file_out:
        writer = csv.writer(file_out, delimiter=",")
        for i in frequency_list:
            ITOG = [i, frequency[i]]
            writer.writerow(ITOG)
        file_out.seek(0)
        
        filename = filename.filename[0:-4]
        filenames = f"attachment; filename={filename}_UniqUsersPerDay.csv"
        cherrypy.response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        cherrypy.response.headers['Content-Disposition'] = filenames
        return file_out.read().encode(target_encoding)

    @cherrypy.expose
    def ObrFIO(self, filename, username=None, target_encoding='1251'):
        reader = csv.reader(StringIO(filename.file.read().decode('utf-8')))
        reader = iter(reader)
        next(reader)
        users = sorted((row for row in map(self.parse_row, reader) if row[1][0] not in self.SKIP_USER_NAMES), key=lambda row: row[1][1])
        if username is not None and username:
            username = str(username).lower()
            users = filter(lambda row: row[1][0].lower().find(username) > -1, users)
        users = dict(users)

        file_out = StringIO()
        writer = csv.writer(file_out, delimiter=",")
        for name, date in users.values():
            writer.writerow((date.strftime('%d.%m.%y'), name))
        file_out.seek(0)
        filename = filename.filename.replace('.csv', '')
        filenames = f"attachment; filename={filename}.csv"
        cherrypy.response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        cherrypy.response.headers['Content-Disposition'] = filenames
        return file_out.read().encode(target_encoding)

config = {
    'global': {
        'server.socket_host': '0.0.0.0',
        'server.socket_port': int(os.environ.get('PORT', 5000)),
    },
    '/assets': {
        'tools.staticdir.root': os.path.dirname(os.path.abspath(__file__)),
        'tools.staticdir.on': True,
        'tools.staticdir.dir': 'assets',
    }
}

cherrypy.quickstart(HelloWorld(), '/', config=config)