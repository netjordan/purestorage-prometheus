# __main__.py
# Import Python modules
import argparse
import time
import socket
import os
import yaml
import sys
import logging

# Import third party modules
from prometheus_client import Info, REGISTRY
import purestorage

# Import purestoragefa_exporter
import purestoragefa_exporter
from purestoragefa_exporter import pure_collector


def arg_parser():
    '''(None) -> str
    It parses the script arguments
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', required=True,
                        help='username to access the array')
    parser.add_argument('-f', '--file', required=True,
                        help='the inventory file for the arrays')
    parser.add_argument('-p', '--port', required=True,
                        help='port for the webserver scraped by Prometheus')
    parser.add_argument('-s', '--http_server', required=False,
                        default='twisted',
                        help='webserver name: twisted')
    opts = parser.parse_args()
    return(opts)


def get_fas(config_file):
    """ (Str) -> list
    Returns a list of dictionaries storing device inventory information.
    Parameters:
      config_file: The YAML formatted inventory file, see the
                   pure-inventory.yaml as eample
    """
    try:
        with open(config_file) as f:
            fy = yaml.load(f)
        return fy['device_inventory']
    except TypeError as te:
        print(f'The inventory file cannot be parsed: {te}')
        sys.exit(1)
    except FileNotFoundError as fe:
        print(f'The inventory file was not found: {fe}')
        sys.exit(127)


def init_prom(port, http_server):
    """ (Str) -> None
    Initialize Prometheus exporter and start the http server exposing
    the metrics.
    Parameters:
      port: The http port for the client
      http_sever: for the moment only twisted
    """
    if http_server == 'twisted':
        # start the exporter http server with twisted
        from prometheus_client import start_http_server
        start_http_server(int(port))
    else:
        print(f'{http_server} is not supoorted. supported: twisted')
        sys.exit(1)
    i = Info('purestorage_exporter',
             'Purestorage Flasharray Prometheus exporter')
    i.info({'version': purestoragefa_exporter.__version__,
            'running_on': socket.gethostname()})


def connect_to_fas(model, fqdn, pwd):
    """(Str, Str, Str) -> cls
    It opens an API session with the given device and returns the storage
    object if the model is of type flasharray
    Parameters:
      model: the model of the storage array
      fqdn: the fqdn of the Purestorage array
      pwd: the API token to establish a session with the Purestorage array
    """
    if model == 'flasharray':
        return(purestorage.FlashArray(fqdn, api_token=pwd,
               verify_https=False, request_kwargs={'timeout': 15}))
    elif model is None:
        print(f'No model has been specified for {fqdn}')
        sys.exit(1)
    else:
        print(f'Not implemented for storage model {model}')
        sys.exit(1)


class CollectMany:
    """
    This class allows to run one exporter for multiple Purestorage Flasharrays
    instead of having to run one purestoragefa_exporter for each.
    The class will be registered with prometheus_client.REGISTRY
    Parameters:
        collectors: a list of instantiated PurestorageCollector
    """
    def __init__(self, collectors):
        self.collectors = collectors

    def collect(self):
        """
        This method is required by prometheus_client.Registry, it must have
        the name collect
        """
        for c in self.collectors:
            yield from c.collect()


def main():
    """Start PurestorrageFa Prometheus exporter"""
    try:
        # get pid for logging and also quit if already tunning
        collector_pid = os.getpid()
        pid_file = '/var/run/purestorage-exporter.pid'
        if os.path.isfile(pid_file):
            print('Existing pid file is present, not running')
            sys.exit(1)
        logger = logging.getLogger('PurestorageFlashArrayExporter')
        # msg will be present in the exception logged
        msg = 'Collector could not run'
        # get user arguments
        opts = arg_parser()
        # parse the inventory file
        fas = get_fas(opts.file)
        # initilize Prometheus client and the http server
        init_prom(int(opts.port), opts.http_server)
        # create a list for my instantiated PurestorageCollector
        collectors = []
        for fa in fas:
            if fa['collector']['enabled'] is False:
                continue
            logging.basicConfig(
                filename=fa['collector']['logs'],
                level=fa['collector']['debug_level'],
                format='%(asctime)s %(levelname)s %(process)d %(message)s'
            )
            logger.info(
                'Starting FlashArrayExporter for %s PID %s',
                fa['fqdn'], collector_pid
            )
            # create API session with Flasharray
            logger.debug('Creating API session for %s', fa['fqdn'])
            # open an API session with Purestorage Flasharray
            session = connect_to_fas(
                fa['model'], fa['fqdn'], fa['usernames'][opts.user])
            logger.debug('API session for %s created, instantiating'
                         'PurestorageCollector', fa['fqdn'])
            # populate my list of PurestorageCollectors
            collectors.append(pure_collector.PurestorageCollector(session))
            # get array name
            logger.info('Instantiated PurestorageCollector for %s'
                        'Exporting...', fa['fqdn'])
            # Register the collectors with Prometheus client
            REGISTRY.register(CollectMany(collectors))
            # Keep it running otherwise http server won't be always up
            logger.info('Exporting completed for %s.', fa['fqdn'])
            # invalidate API session cookies with Flasharray
            session.invalidate_cookie()
            logger.info('API session closed for %s.', fa['fqdn'])
            while True:
                # It doesn't matter how long i sleep
                time.sleep(300)
    except ValueError as ve:
        logger.exception(msg, ve)
    except ImportError as ie:
        logger.exception(msg, ie)
    except AttributeError as ae:
        logger.exception(msg, ae)
    except purestorage.purestorage.PureHTTPError as ps:
        logger.exception(msg, ps)
    except purestorage.purestorage.PureError as pe:
        logger.exception(msg, pe)
    except PermissionError as pe:
        logger.exception(msg, pe)
        print(msg, pe)
        sys.exit(1)


if __name__ == "__main__":
    main()
