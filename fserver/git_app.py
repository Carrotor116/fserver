# -*- coding: utf-8 -*-

from flask import make_response, Response
from flask import request
from flask_httpauth import HTTPBasicAuth

from fserver import conf
from fserver.app import app
from fserver.fserver_app import do_get
from fserver.git import git_command, git_command_with_input

auth = HTTPBasicAuth()


@auth.verify_password
def authenticate(username, password):
    return username == conf.USER_NAME and password == conf.PASSWORD


@app.route('/<string:repo_name>/git-upload-pack', methods=['POST'])
def git_upload_pack(repo_name):
    if not conf.GIT_SERVICE or not is_git():
        return do_get('{}/git-upload-pack'.format(repo_name))

    repo_name = repo_name if repo_name.endswith('.git') else repo_name + '.git'
    args = ['upload-pack', "--stateless-rpc", '.']
    res = git_command_with_input(repo_name, request.data, *args)

    return Response(res)


@app.route('/<string:repo_name>/git-receive-pack', methods=['POST'])
@auth.login_required
def git_receive_pack(repo_name):
    # push
    if not conf.GIT_SERVICE or not is_git():
        return do_get('{}/git-receive-pack'.format(repo_name))

    repo = repo_name if repo_name.endswith('.git') else repo_name + '.git'
    args = ['receive-pack', "--stateless-rpc", '.']
    res = git_command_with_input(repo, request.data, *args)
    return Response(res)


@app.route('/<string:repo_name>/info/refs', methods=['GET'])
def git_info_refs(repo_name):
    if not conf.GIT_SERVICE or not is_git():
        return do_get('{}/info/refs'.format(repo_name))

    repo_name = repo_name if repo_name.endswith('.git') else repo_name + '.git'

    service = request.args.get('service')

    if service and 'git-' in service:
        service_name = service[4:]
    else:
        service_name = 'upload-pack'

    if service_name == 'receive-pack' and not auth.username():
        # push
        return auth.login_required(git_info_refs)(repo_name)

    args = [service_name, "--stateless-rpc", "--advertise-refs", "."]

    res = git_command(repo_name, *args)

    first_line = '# service=git-%s\n0000' % service_name
    first_line = ('%.4x' % len(first_line)) + first_line

    resp = make_response(first_line + res.decode())
    resp.headers['Content-Type'] = 'application/x-git-%s-advertisement' % service_name
    return resp


def is_git():
    ag = request.headers.get('User-Agent')
    ag = ag.lower().split('/')[0]
    return ag == 'git'
