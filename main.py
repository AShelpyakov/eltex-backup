import os
import re
import smtplib
import ssl
from datetime import datetime
from string import Template

import git
from nornir import InitNornir
from nornir.core.task import Result, Task
from nornir_netmiko import netmiko_multiline
from nornir_utils.plugins.functions import print_result

TIME_FORMAT: str = '%d-%b-%Y %H:%M:%S'
PROBLEM_MESSAGE = Template(
    'Subject: Problem hosts\n\nHosts with problems:\n$hosts'
)
DIFF_MESSAGE = Template('Subject: Diff configs\n\n@diff')



def create_backups_dir(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)


def send_mail(
        message: str,
        smtp_server: str,
        smtp_port: int,
        smtp_sender: str,
        smtp_receiver: str,
        smtp_password: str = None,
) -> None:
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
        server.login(smtp_sender, smtp_password)
        server.sendmail(smtp_sender, smtp_receiver, message)


def save_config_to_file(
        nr: object,
        hostname: str,
        config: str
) -> None:
    filename = f'{hostname}.cfg'
    with open(os.path.join(
            nr.config.user_defined['backup_dir'], filename
    ), 'w') as f:
        splited_config: list[str] = config.splitlines(keepends=True)
        for string in splited_config:
            if nr.inventory.hosts[hostname].extended_data()[
                'last_command'
            ] in string:
                break

            if any(re.search(pattern, string) is not None for pattern in
                   nr.inventory.hosts[hostname].extended_data()[
                       'delete_patterns'
                   ]):
                continue

            for command in nr.inventory.hosts[hostname].extended_data()[
                'backup_commands'
            ]:
                if re.search(f'.*{command}$', string):
                    string = f'####### Command: {command} #######\n'
                    break

            original_string: str = string
            for arguments in nr.inventory.hosts[hostname].extended_data()[
                'change_arguments'
            ]:
                string = re.sub(*arguments, string)
                if string is not original_string:
                    continue

            f.writelines(string)


def netmiko_backup_commands(task: Task) -> Result:
    commands: list[str] = task.host.extended_data()['backup_commands'] + [
        task.host.extended_data()['last_command']
    ]
    return netmiko_multiline(task, commands)


def get_netmiko_backups(nr: object) -> None:
    backup_results = nr.run(task=netmiko_backup_commands)
    # print to console result
    # print_result(backup_results)
    for hostname in backup_results:
        if hostname not in nr.data.failed_hosts:
            save_config_to_file(
                nr=nr,
                hostname=hostname,
                config=backup_results[hostname][0].result,
            )


if __name__ == '__main__':
    nr = InitNornir(config_file='./config.yaml')
    create_backups_dir(nr.config.user_defined['backup_dir'])
    get_netmiko_backups(nr)
    if nr.data.failed_hosts:
        send_mail(
            message=PROBLEM_MESSAGE.substitute(
                hosts='\n'.join(host for host in nr.data.failed_hosts)
            ),
            **nr.config.user_defined['smtp'],
        )

    repo = git.Repo.init(nr.config.user_defined['backup_dir'])
    repo_diff: str = repo.git.diff(None)
    if repo_diff:
        repo.index.add('**')
        repo.index.commit(datetime.now().strftime(TIME_FORMAT))
        send_mail(
            message=DIFF_MESSAGE.substitute(diff=repo_diff),
            **nr.config.user_defined['smtp'],
        )
