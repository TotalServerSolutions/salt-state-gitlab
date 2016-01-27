# -*- coding: utf-8 -*-
'''
Module for handling Gitlab calls.

:optdepends:    - pyapi-gitlab Python adapter
:configuration: This module is not usable until the following are specified
    either in a pillar or in the minion's config file::

        gitlab.user: admin
        gitlab.password: verybadpass
        gitlab.url: 'https://gitlab.domain.com/'

        OR (for API based authentication)

        gitlab.user: admin
        gitlab.api: '432432432432432'
        gitlab.url: 'https://gitlab.domain.com'
'''

from __future__ import absolute_import

# Import third party libs
HAS_GITLAB = False
try:
    from gitlab import Gitlab
    HAS_GITLAB = True
except ImportError:
    pass


def __virtual__():
    '''
    Only load this module if gitlab
    is installed on this minion.
    '''
    if HAS_GITLAB:
        return 'gitlab'
    return False

__opts__ = {}


def _get_project_by_id(git, id):
    selected_project = git.getproject(id)
    return selected_project


def _get_project_by_name(git, name):
    selected_project = None
    for project in git.getprojects():
        if project.get('path_with_namespace') == name:
            selected_project = project
            break
    return selected_project


def auth(**connection_args):
    '''
    Set up gitlab credentials

    Only intended to be used within Gitlab-enabled modules
    '''
   
    prefix = "gitlab."

    # look in connection_args first, then default to config file
    def get(key, default=None):
        return connection_args.get('connection_' + key,
            __salt__['config.get'](prefix + key, default))

    user = get('user', 'admin')
    password = get('password', 'ADMIN')
    token = get('token')
    url = get('url', 'https://localhost/')
    if token:
        git = Gitlab(url, token=token)
    else:
        git = Gitlab(url)
        git.login(user, password)
    return git


def hook_get(hook_url, project_id=None, project_name=None, **connection_args):
    '''
    Return a specific endpoint (gitlab endpoint-get)

    CLI Example:

    .. code-block:: bash

        salt '*' gitlab.endpoint_get nova
    '''
    git = auth(**connection_args)
    if project_name:
        project = _get_project_by_name(git, project_name)
    else:
        project = _get_project_by_id(git, project_id)
    if not project:
        return {'Error': 'Unable to resolve project'}
    for hook in git.getprojecthooks(project.get('id')):
        if hook.get('url') == hook_url:
            return {hook.get('url'): hook}
    return {'Error': 'Could not find hook for the specified project'}


def hook_list(project_id=None, project_name=None, **connection_args):
    '''
    Return a list of available hooks for project

    CLI Example:

    .. code-block:: bash

        salt '*' gitlab.deploykey_list 341
    '''
    git = auth(**connection_args)
    ret = {}
    if project_name:
        project = _get_project_by_name(git, project_name)
    else:
        project = _get_project_by_id(git, project_id)
    if not project:
        return {'Error': 'Unable to resolve project'}
    for hook in git.getprojecthooks(project.get('id')):
        ret[hook.get('url')] = hook
    return ret


def hook_create(hook_url, issues=False, merge_requests=False, \
    push=False, tag_push=False, project_id=None, project_name=None, **connection_args):
    '''
    Create an hook for a project

    CLI Examples:

    .. code-block:: bash

        salt '*' gitlab.hook_create 'https://hook.url/' push_events=True project_id=300
    '''
    git = auth(**connection_args)
    if project_name:
        project = _get_project_by_name(git, project_name)
    else:
        project = _get_project_by_id(git, project_id)
    if not project:
        return {'Error': 'Unable to resolve project'}
    create = True
    for hook in git.getprojecthooks(project.get('id')):
        if hook.get('url') == hook_url:
            create = False
    if create:  
        git.addprojecthook(project['id'], hook_url, issues=issues, 
            push=push, merge_requests=merge_requests, tag_push=tag_push)
    return hook_get(hook_url, project_id=project['id'])


def hook_delete(hook_url, project_id=None, project_name=None, **connection_args):
    '''
    Delete hook of a Gitlab project

    CLI Examples:

    .. code-block:: bash

        salt '*' gitlab.hook_delete 'https://hook.url/' project_id=300
    '''
    git = auth(**connection_args)
    if project_name:
        project = _get_project_by_name(git, project_name)
    else:
        project = _get_project_by_id(git, project_id)
    if not project:
        return {'Error': 'Unable to resolve project'}
    for hook in git.getprojecthooks(project.get('id')):
        if hook.get('url') == hook_url:
            return git.deleteprojecthook(project['id'], hook['id'])
    return {'Error': 'Could not find hook for the specified project'}


def deploykey_create(title, key, project_id=None, project_name=None, 
                   **connection_args):
    '''
    Add deploy key to Gitlab project

    CLI Examples:

    .. code-block:: bash

        salt '*' gitlab.deploykey_create title keyfrsdfdsfds 43
    '''
    git = auth(**connection_args)
    if project_name:
        project = _get_project_by_name(git, project_name)
    else:
        project = _get_project_by_id(git, project_id)
    if not project:
        return {'Error': 'Unable to resolve project'}
    create = True
    for dkey in git.getdeploykeys(project['id']):
        if dkey.get('title') == title:
            create = False
    if create:
        git.adddeploykey(project['id'], title, key)
    return deploykey_get(title, project_id=project['id'])


def deploykey_delete(key_title, project_id=None, project_name=None, **connection_args):
    '''
    Delete a deploy key from Gitlab project

    CLI Examples:

    .. code-block:: bash

        salt '*' gitlab.deploykey_delete key.domain.com 12
        salt '*' gitlab.deploykey_delete key.domain.com project_name=namespace/path
    '''
    git = auth(**connection_args)
    if project_name:
        project = _get_project_by_name(git, project_name)
    else:
        project = _get_project_by_id(git, project_id)
    if not project:
        return {'Error': 'Unable to resolve project'}
    for key in git.listdeploykeys(project.get('id')):
        if key.get('title') == key_title:
            git.deletedeploykey(project['id'], key['id'])
            return 'Gitlab deploy key ID "{0}" deleted'.format(key['id'])
    return {'Error': 'Could not find deploy key for the specified project'}


def deploykey_get(title, project_id=None, project_name=None, **connection_args):
    '''
    Return a specific deploy key

    CLI Examples:

    .. code-block:: bash

        salt '*' gitlab.deploykey_get key.domain.com 12
        salt '*' gitlab.deploykey_get key.domain.com project_name=namespace/path
    '''
    git = auth(**connection_args)
    if project_name:
        project = _get_project_by_name(git, project_name)
    else:
        project = _get_project_by_id(git, project_id)
    if not project:
        return {'Error': 'Unable to resolve project'}
    for key in git.getdeploykeys(project.get('id')):
        if key.get('title') == title:
            return {key.get('title'): key}
    return {'Error': 'Could not find deploy key for the specified project'}


def deploykey_list(project_id=None, project_name=None, **connection_args):
    '''
    Return a list of available deploy keys for project

    CLI Example:

    .. code-block:: bash

        salt '*' gitlab.deploykey_list 341
    '''
    git = auth(**connection_args)
    ret = {}
    if project_name:
        project = _get_project_by_name(git, project_name)
    else:
        project = _get_project_by_id(git, project_id)
    if not project:
        return {'Error': 'Unable to resolve project'}
    for key in git.listdeploykeys(project.get('id')):
        ret[key.get('title')] = key
    return ret

def project_create(name, description=None, enabled=True, profile=None,
                  **connection_args):
    '''
    Create a gitlab project

    CLI Examples:

    .. code-block:: bash

        salt '*' gitlab.project_create nova description='nova project'
        salt '*' gitlab.project_create test enabled=False
    '''
    git = auth(**connection_args)
    data = git.createproject(name, description=description, enabled=True, profile=profile)
    if not data:
        return {'Error': 'Unable to create project'}
    return project_get(data['id'], profile=profile, **connection_args)


def project_delete(project_id=None, name=None, profile=None, **connection_args):
    '''
    Delete a project (gitlab project-delete)

    CLI Examples:

    .. code-block:: bash

        salt '*' gitlab.project_delete c965f79c4f864eaaa9c3b41904e67082
        salt '*' gitlab.project_delete project_id=c965f79c4f864eaaa9c3b41904e67082
        salt '*' gitlab.project_delete name=demo
    '''
    git = auth(**connection_args)
    if name:
        for project in git.projects.list():
            if project.name == name:
                project_id = project.id
                break
    if not project_id:
        return {'Error': 'Unable to resolve project id'}
    git.projects.delete(project_id)
    ret = 'Tenant ID {0} deleted'.format(project_id)
    if name:

        ret += ' ({0})'.format(name)
    return ret


def project_get(project_id=None, name=None, **connection_args):
    '''
    Return a specific project

    CLI Examples:

    .. code-block:: bash

        salt '*' gitlab.project_get 323
        salt '*' gitlab.project_get project_id=323
        salt '*' gitlab.project_get name=namespace/repository
    '''
    git = auth(**connection_args)
    ret = {}
    if name:
        project = _get_project_by_name(git, name)
    else:
        project = _get_project_by_id(git, project_id)
    if not project:
        return {'Error': 'Error in retrieving project'}
    ret[project.get('name')] = project
    return ret

def project_list(**connection_args):
    '''
    Return a list of available projects

    CLI Example:

    .. code-block:: bash

        salt '*' gitlab.project_list
    '''
    git = auth(**connection_args)
    ret = {}
    for project in git.getprojects():
        ret[project.get('name')] = project
    return ret


def project_update(project_id=None, name=None, email=None,
                  enabled=None, **connection_args):
    '''
    Update a project's information (gitlab project-update)
    The following fields may be updated: name, email, enabled.
    Can only update name if targeting by ID

    CLI Examples:

    .. code-block:: bash

        salt '*' gitlab.project_update name=admin enabled=True
        salt '*' gitlab.project_update c965f79c4f864eaaa9c3b41904e67082 name=admin email=admin@domain.com
    '''
    git = auth(**connection_args)
    if not project_id:
        for project in git.projects.list():
            if project.name == name:
                project_id = project.id
                break
    if not project_id:
        return {'Error': 'Unable to resolve project id'}

    project = git.projects.get(project_id)
    if not name:
        name = project.name
    if not email:
        email = project.email
    if enabled is None:
        enabled = project.enabled
    git.projects.update(project_id, name, email, enabled)

def user_list(**connection_args):
    '''
    Return a list of available users

    CLI Example:

    .. code-block:: bash

        salt '*' gitlab.user_list
    '''
    git = auth(**connection_args)
    ret = {}
    for user in git.getusers():
        ret[user.get('name')] = user
    return ret

def _get_user_by_name(git, username):
    selected_user = None
    for user in git.getusers():
        if user.get('username') == username:
            selected_user = user
            break
    return selected_user

def _get_user_by_id(git, id):
    selected_user = git.getuser(id)
    return selected_user

def user_get(user_id=None, username=None, **connection_args):
    '''
    Return a specific user

    CLI Examples:

    .. code-block:: bash

        salt '*' gitlab.user_get 11
        salt '*' gitlab.user_get user_id=11
        salt '*' gitlab.user_get username=kevinquinnyo
    '''
    git = auth(**connection_args)
    ret = {}
    if username:
        user = _get_user_by_name(git, username)
    else:
        user = _get_user_by_id(git, user_id)
    if not user:
        return {'Error': 'Error in retrieving user'}
    ret[user.get('username')] = user
    return ret

def user_list(**connection_args):
    '''
    Return a list of available users

    CLI Example:

    .. code-block:: bash

        salt '*' gitlab.user_list
    '''
    git = auth(**connection_args)
    ret = {}
    for user in git.getusers():
        ret[user.get('name')] = user
    return ret

def user_create(name,
                username,
                password,
                email,
                **connection_args):
    '''
    Create a gitlab user

    CLI Examples:

    .. code-block:: bash

        salt '*' gitlab.user_create 'Kevin Quinn' kevinquinnyo 'p4ssw0rd' kevin@example.com admin=True
    '''

    if 'can_create_group' not in  connection_args:
        connection_args['can_create_group'] = False
    git = auth(**connection_args)
    data = git.createuser(name,
                        username,
                        password,
                        email,
                        **connection_args)
    if not data:
        return {'Error': 'Unable to create user'}
    return user_get(data['id'], **connection_args)

def user_delete(user_id=None, **connection_args):
    '''
    Delete a user

    CLI Examples:

    .. code-block:: bash

        salt '*' gitlab.user_delete username=kevinquinnyo
        salt '*' gitlab.user_delete 11
    '''
    git = auth(**connection_args)
    user = _get_user_by_id(git, user_id)
    if not user:
        return {'Error': 'Unable to find user with user_id {0}'.format(user_id)}
    deleted = git.deleteuser(user_id)
    if deleted:
        return {'user_id': user['id'], 'user_name': user['name'], 'deleted': True}
    return {'Error': 'Unable to delete user {0} (username: {1})'.format(user['id'], user['username'])}

def user_update(user_id=None,
                    name=None,
                    username=None,
                    password=None,
                    email=None,
                    **connection_args):
    '''
    Update a user's information (gitlab user-update)
    The following fields may be updated: name, email, username, password.
    Can only update name if targeting by ID

    CLI Examples:

    .. code-block:: bash

        salt '*' gitlab.user_update name=admin enabled=True
        salt '*' gitlab.user_update 11 name=admin email=admin@domain.com
    '''
    git = auth(**connection_args)
    if not user_id:
        user = _get_user_by_name(username)
        user_id = user['id']
    if not user_id:
        return {'Error': 'Unable to resolve user id'}
    user = git.getuser(user_id)
    if not name:
        name = user['name']
    if not username:
        username = user['username']
    if not email:
        email = user['email']
    if password:
        user_edited = git.edituser(user_id, name=name, username=username, email=email, password=password)
    else: 
        user_edited = git.edituser(user_id, name=name, username=username, email=email)
    return user_edited

