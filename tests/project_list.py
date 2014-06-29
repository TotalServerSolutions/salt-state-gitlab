#!/usr/local/bin/python

import gitlab

user = 'newt'
password = 'ADMIN'
token = ''
url = 'https://repo.cz/'

if token:
    git = gitlab.Gitlab(url, token=token)
else:
    git = gitlab.Gitlab(url)
    git.login(user, password)

print git

#for project in git.getprojects():
#	print project

project_id = 341
name = 'django/horizon-billing'
#name = None
ret = {}

if name:
    for project in git.getprojects():
        if project.get('path_with_namespace') == name:
            selected_project = project
            project_id = project.get('id')
            break
    if not project_id:
        print {'Error': 'Unable to resolve project ID'}
else:
    selected_project = git.getproject(project_id)

if not selected_project:
    print {'Error': 'Error in retrieving project'}

print  selected_project

ret[selected_project.get('name')] = selected_project
print ret
