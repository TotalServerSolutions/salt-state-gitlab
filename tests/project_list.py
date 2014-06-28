#!/usr/local/bin/python

import gitlab

user = 'newt'
password = 'ADMIN'
token = ''
url = 'https:///'

if token:
    git = gitlab.Gitlab(url, token=token)
else:
    git = gitlab.Gitlab(url)
    git.login(user, password)

print git

for project in git.getprojects():
	print project
