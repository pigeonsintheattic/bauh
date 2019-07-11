import re
import subprocess
from typing import List

from fpakman.core import system
from fpakman.core.model import Application

BASE_CMD = 'flatpak'


def app_str_to_json(line: str, version: str) -> dict:

    app_array = line.split('\t')

    if version >= '1.3.0':
        app = {'name': app_array[0],
               'id': app_array[1],
               'version': app_array[2],
               'branch': app_array[3]}
    elif '1.0' <= version < '1.1':
        app = {'ref': app_array[0], 'options': app_array[1]}

        ref_data = app['ref'].split('/')
        app['id'] = ref_data[0]
        app['arch'] = ref_data[1]
        app['branch'] = ref_data[2]
        app['name'] = ref_data[0].split('.')[-1]
        app['version'] = None
    elif '1.2' <= version < '1.3':
        app = {'name': app_array[1].strip().split('.')[-1],
               'id': app_array[1],
               'version': app_array[2],
               'branch': app_array[3],
               'arch': app_array[4],
               'origin': app_array[5]}
    else:
        raise Exception('Unsupported version')

    extra_fields = get_app_info_fields(app['id'], app['branch'], ['origin', 'arch', 'ref', 'commit'], check_runtime=True)
    app.update(extra_fields)

    return app


def get_app_info_fields(app_id: str, branch: str, fields: List[str] = [], check_runtime: bool = False):
    info = re.findall(r'\w+:\s.+', get_app_info(app_id, branch))
    data = {}
    fields_to_retrieve = len(fields) + (1 if check_runtime and 'ref' not in fields else 0)

    for field in info:

        if fields and fields_to_retrieve == 0:
            break

        field_val = field.split(':')
        field_name = field_val[0].lower()

        if not fields or field_name in fields or (check_runtime and field_name == 'ref'):
            data[field_name] = field_val[1].strip()

            if fields:
                fields_to_retrieve -= 1

        if check_runtime and field_name == 'ref':
            data['runtime'] = data['ref'].startswith('runtime/')

    return data


def is_installed():
    version = get_version()
    return False if version is None else True


def get_version():
    res = system.run_cmd('{} --version'.format(BASE_CMD), print_error=False)
    return res.split(' ')[1].strip() if res else None


def get_app_info(app_id: str, branch: str):
    return system.run_cmd('{} info {} {}'.format(BASE_CMD, app_id, branch))


def list_installed() -> List[dict]:
    apps_str = system.run_cmd('{} list'.format(BASE_CMD))

    if apps_str:
        version = get_version()
        app_lines = apps_str.split('\n')
        return [app_str_to_json(line, version) for line in app_lines if line]

    return []


def update_and_stream(app_ref: str):
    """
    Updates the app reference and streams Flatpak output,
    :param app_ref:
    :return:
    """
    return system.stream_cmd([BASE_CMD, 'update', '-y', app_ref])


def uninstall_and_stream(app_ref: str):
    """
    Removes the app by its reference
    :param app_ref:
    :return:
    """
    return system.cmd_to_subprocess([BASE_CMD, 'uninstall', app_ref, '-y'])


def list_updates_as_str():
    return system.run_cmd('{} update'.format(BASE_CMD), ignore_return_code=True)


def downgrade_and_stream(app_ref: str, commit: str, root_password: str):

    pwdin, downgrade_cmd = None, []

    if root_password is not None:
        downgrade_cmd.extend(['sudo', '-S'])
        pwdin = system.stream_cmd(['echo', root_password])

    downgrade_cmd.extend([BASE_CMD, 'update', '--commit={}'.format(commit), app_ref, '-y'])
    return subprocess.Popen(downgrade_cmd, stdin=pwdin, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout


def get_app_commits(app_ref: str, origin: str) -> List[str]:
    log = system.run_cmd('{} remote-info --log {} {}'.format(BASE_CMD, origin, app_ref))
    return re.findall(r'Commit+:\s(.+)', log)


def get_app_commits_data(app_ref: str, origin: str) -> List[dict]:
    log = system.run_cmd('{} remote-info --log {} {}'.format(BASE_CMD, origin, app_ref))

    res = re.findall(r'(Commit|Subject|Date):\s(.+)', log)

    commits = []

    commit = {}

    for idx, data in enumerate(res):
        commit[data[0].strip().lower()] = data[1].strip()

        if (idx + 1) % 3 == 0:
            commits.append(commit)
            commit = {}

    return commits


def search(word: str) -> List[dict]:
    cli_version = get_version()

    res = system.run_cmd('{} search {}'.format(BASE_CMD, word))

    found = []

    split_res = res.split('\n')

    if split_res and split_res[0].lower() != 'no matches found':
        for info in split_res:
            if info:
                info_list = info.split('\t')

                if cli_version >= '1.3.0':
                    version = info_list[3].strip()
                    found.append({
                        'name': info_list[0].strip(),
                        'description': info_list[1].strip(),
                        'id': info_list[2].strip(),
                        'version': version,
                        'latest_version': version,
                        'branch': info_list[4].strip(),
                        'origin': info_list[5].strip(),
                        'runtime': False,
                        'arch': None,  # unknown at this moment,
                        'ref': None  # unknown at this moment
                    })
                elif cli_version >= '1.2.0':
                    desc = info_list[0].split('-')
                    version = info_list[2].strip()
                    found.append({
                        'name': desc[0].strip(),
                        'description': desc[1].strip(),
                        'id': info_list[1].strip(),
                        'version': version,
                        'latest_version': version,
                        'branch': info_list[3].strip(),
                        'origin': info_list[4].strip(),
                        'runtime': False,
                        'arch': None,  # unknown at this moment,
                        'ref': None  # unknown at this moment
                    })
                else:
                    version = info_list[1].strip()
                    found.append({
                        'name': '',
                        'description': info_list[4].strip(),
                        'id': info_list[0].strip(),
                        'version': version,
                        'latest_version': version,
                        'branch': info_list[2].strip(),
                        'origin': info_list[3].strip(),
                        'runtime': False,
                        'arch': None,  # unknown at this moment,
                        'ref': None  # unknown at this moment
                    })
    return found


def install_and_stream(app_id: str, origin: str):
    return system.cmd_to_subprocess([BASE_CMD, 'install', origin, app_id, '-y'])


def set_default_remotes():
    system.run_cmd('flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo')

