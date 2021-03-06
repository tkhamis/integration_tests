import pytest

from cfme.utils.appliance import DummyAppliance
from cfme.utils.log import logger
from cfme.utils.path import data_path
from cfme.fixtures.artifactor_plugin import fire_art_hook


@pytest.fixture(scope="session", autouse=True)
def ensure_websocket_role_disabled(appliance):
    # TODO: This is a temporary solution until we find something better.
    if isinstance(appliance, DummyAppliance) or appliance.is_dev:
        return
    server_settings = appliance.server.settings
    roles = server_settings.server_roles_db
    if 'websocket' in roles and roles['websocket']:
        logger.info('Disabling the websocket role to ensure we get no intrusive popups')
        server_settings.disable_server_roles('websocket')


@pytest.fixture(scope="session", autouse=True)
def fix_merkyl_workaround(request, appliance):
    """Workaround around merkyl not opening an iptables port for communication"""
    if isinstance(appliance, DummyAppliance) or appliance.is_dev:
        return
    ssh_client = appliance.ssh_client
    if ssh_client.run_command('test -s /etc/init.d/merkyl').failed:
        logger.info('Rudely overwriting merkyl init.d on appliance;')
        local_file = data_path.join("bundles").join("merkyl").join("merkyl")
        remote_file = "/etc/init.d/merkyl"
        ssh_client.put_file(local_file.strpath, remote_file)
        ssh_client.run_command("service merkyl restart")
        fire_art_hook(
            request.config,
            'setup_merkyl',
            ip=appliance.hostname)


@pytest.fixture(scope="session", autouse=True)
def fix_missing_hostname(appliance):
    """Fix for hostname missing from the /etc/hosts file

    Note: Affects RHOS-based appliances but can't hurt the others so
          it's applied on all.
    """
    if isinstance(appliance, DummyAppliance) or appliance.is_dev:
        return
    logger.info("Checking appliance's /etc/hosts for a resolvable hostname")
    hosts_grep_cmd = 'grep {} /etc/hosts'.format(appliance.get_resolvable_hostname())
    with appliance.ssh_client as ssh_client:
        if ssh_client.run_command(hosts_grep_cmd).failed:
            logger.info('Setting appliance hostname')
            if not appliance.set_resolvable_hostname():
                # not resolvable, just use hostname output through appliance_console_cli to modify
                cli_hostname = ssh_client.run_command('hostname').output.rstrip('\n')
                logger.warning('Unable to resolve hostname, using `hostname`: %s', cli_hostname)
                appliance.appliance_console_cli.set_hostname(cli_hostname)

            if ssh_client.run_command('grep $(hostname) /etc/hosts').failed:
                logger.error('Failed to mangle /etc/hosts')
