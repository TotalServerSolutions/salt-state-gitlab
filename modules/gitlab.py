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


def hook_create(hook_url, issues_events=False, merge_requests_events=False, \
    push_events=False, project_id=None, project_name=None, **connection_args):
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
        git.addprojecthook(project['id'], hook_url)
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


def deploykey_create(name, service_type, description=None, profile=None,
                   **connection_args):
    '''
    Add deploy to Gitlab project

    CLI Examples:

    .. code-block:: bash

        salt '*' gitlab.service_create nova compute \
                'OpenStack Compute Service'
    '''
    git = auth(**connection_args)
    service = git.services.create(name, service_type, description)
    return service_get(service.id, profile=profile, **connection_args)


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

def deploykey_get(key_title, project_id=None, project_name=None, **connection_args):
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
    for key in git.listdeploykeys(project.get('id')):
        if key.get('title') == key_title:
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
    new = git.projects.create(name, description, enabled)
    return project_get(new.id, profile=profile, **connection_args)


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
