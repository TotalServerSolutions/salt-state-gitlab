# -*- coding: utf-8 -*-
'''
Management of Gitlab projects
==============================

:depends:   - pyapi-gitlab Python module
:configuration: See :py:mod:`salt.modules.gitlab` for setup instructions.

.. code-block:: yaml

    Gitlab projects:
      gitlab.project_present:
        - names:
          - namespace1/repository1
          - namespace1/repository2
          - namespace2/repository1

    jenkins:
      gitlab.hook_present:
        - name: http://url_of_hook
        - project: 'namespace/repository'

    some_deploy_key:
      gitlab.deploykey_present:
        - name: title_of_key
        - key: public_key
        - project: 'namespace/repository'

'''


def __virtual__():
    '''
    Only load if the gitlab module is in __salt__
    '''
    return 'gitlab' if 'gitlab.auth' in __salt__ else False


def project_present(name, description=None, enabled=True, profile=None,
                   **connection_args):
    ''''
    Ensures that the gitlab project exists

    name
        The name of the project to manage

    description
        The description to use for this project

    enabled
        Availability state for this project
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': 'Tenant "{0}" already exists'.format(name)}

    # Check if project is already present
    project = __salt__['gitlab.project_get'](name=name,
                                             profile=profile,
                                             **connection_args)

    if 'Error' not in project:
        if project[name]['description'] != description:
            __salt__['gitlab.project_update'](name, description,
                                               enabled,
                                               profile=profile,
                                               **connection_args)
            comment = 'Tenant "{0}" has been updated'.format(name)
            ret['comment'] = comment
            ret['changes']['Description'] = 'Updated'
        if project[name]['enabled'] != enabled:
            __salt__['gitlab.project_update'](name, description,
                                               enabled,
                                               profile=profile,
                                               **connection_args)
            comment = 'Tenant "{0}" has been updated'.format(name)
            ret['comment'] = comment
            ret['changes']['Enabled'] = 'Now {0}'.format(enabled)
    else:
        # Create project
        __salt__['gitlab.project_create'](name, description, enabled,
                                           profile=profile,
                                           **connection_args)
        ret['comment'] = 'Tenant "{0}" has been added'.format(name)
        ret['changes']['Tenant'] = 'Created'
    return ret


def project_absent(name, profile=None, **connection_args):
    '''
    Ensure that the gitlab project is absent.

    name
        The name of the project that should not exist
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': 'Tenant "{0}" is already absent'.format(name)}

    # Check if project is present
    project = __salt__['gitlab.project_get'](name=name,
                                             profile=profile,
                                             **connection_args)
    if 'Error' not in project:
        # Delete project
        __salt__['gitlab.project_delete'](name=name, profile=profile,
                                           **connection_args)
        ret['comment'] = 'Tenant "{0}" has been deleted'.format(name)
        ret['changes']['Tenant'] = 'Deleted'

    return ret


def deploykey_present(name, key, project, **connection_args):
    '''
    Ensure deploy key present in Gitlab project

    name
        The title of the key

    key
        SSH public key

    project
        path to project, i.e. namespace/repo-name

    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': 'Deploy key "{0}" already exists in project {1}'.format(name, project)}

    # Check if key is already present
    dkey = __salt__['gitlab.deploykey_get'](name,
                                           project_name=project,
                                           **connection_args)
    if key.startswith('/'):
        keyfile = key
        with file(keyfile) as f:
            key = f.read()
        f.close()

    if 'Error' not in dkey:
        return ret
    else:
        # Create deploy key
        dkey = __salt__['gitlab.deploykey_create'](name, key,
                                                  project_name=project,
                                                  **connection_args)
        ret['comment'] = 'Deploy key "{0}" has been added'.format(name)
        ret['changes']['Deploykey'] = 'Created'
    return ret


def deploykey_absent(name, profile=None, **connection_args):
    '''
    Ensure that the deploy key doesn't exist in Gitlab project

    name
        The name of the service that should not exist
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': 'Service "{0}" is already absent'.format(name)}

    # Check if service is present
    role = __salt__['gitlab.service_get'](name=name,
                                            profile=profile,
                                            **connection_args)
    if 'Error' not in role:
        # Delete service
        __salt__['gitlab.service_delete'](name=name,
                                            profile=profile,
                                            **connection_args)
        ret['comment'] = 'Service "{0}" has been deleted'.format(name)
        ret['changes']['Service'] = 'Deleted'

    return ret


def hook_present(name, project, **connection_args):
    '''
    Ensure hook present in Gitlab project

    name
        The URL of hook

    project
        path to project, i.e. namespace/repo-name

    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': 'Hook "{0}" already exists in project {1}'.format(name, project)}

    # Check if key is already present
    hook = __salt__['gitlab.hook_get'](name,
                                       project_name=project,
                                       **connection_args)

    if 'Error' not in hook:
        return ret
    else:
        # Create hook
        hook = __salt__['gitlab.hook_create'](name,
                                              project_name=project,
                                              **connection_args)
        ret['comment'] = 'Hook "{0}" has been added'.format(name)
        ret['changes']['Hook'] = 'Created'
    return ret

## user present
def user_present(username, name, email, password, **connection_args):
    ''''
    Ensures that the gitlab user exists

    username
        The username of the user to manage
    
    name
        The name of the user to manage

    password
        The password of the user to manage

    email
        The email of the user to manage
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': 'User "{0}" already exists'.format(name)}

    # Check if user is already present
    user = __salt__['gitlab.user_get'](username=username, **connection_args)

    if 'Error' not in user:
        key = username
        if user[key]['username'] != username:
            ret['changes']['Username'] = 'Now {0}'.format(username)
        if user[key]['email'] != email:
            ret['changes']['Email'] = 'Now {0}'.format(email)
        if user[key]['name'] != name:
            ret['changes']['Name'] = 'Now {0}'.format(name)
        # don't know if there's a way to retreive password hash
        # just go ahead and update it
        if password:
            ret['changes']['Password'] = 'Now {0}'.format(password)

        update = __salt__['gitlab.user_update'](user_id=user[key]['id'],
                                            name=name,
                                            username=username,
                                            password=password,
                                            email='foo@bar.com',
                                            **connection_args)
        comment = 'User "{0}" has been updated and debug email {1}'.format(name, email)
        ret['comment'] = comment
    else:
        # Create user
        __salt__['gitlab.user_create'](name, username,
                                            password,
                                            email,
                                            **connection_args)
        ret['comment'] = 'User "{0}" has been added'.format(name)
        ret['changes']['User'] = 'Created'
    return ret

def branch_present(project, name, ref, **connection_args):
    '''
    Ensure branch present in Gitlab project

    name
        The name of the branch

    project
        path to project, i.e. namespace/repo-name

    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': 'Branch "{0}" already exists in project {1}'.format(name, project)}

    # Check if branch is already present
    branch = __salt__['gitlab.branch_get'](name, project, **connection_args)

    print "___DEBUG___ branch is {0}".format(branch)
    if 'Error' not in branch:
        return ret
    else:
        # Create branch
        branch = __salt__['gitlab.branch_create'](project,  name, ref, **connection_args)
        ret['comment'] = 'Branch "{0}" has been added'.format(name)
        ret['changes']['Branch'] = 'Created'
    return ret
