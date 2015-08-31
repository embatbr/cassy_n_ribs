#!/usr/bin/env python

"""
"""


import logging
import os
import re
import subprocess
import sys

from cassandra.cluster import Cluster, NoHostAvailable


# default paths

# change to the path of your installation
CASSANDRA_DIR = 'cassandra'
JMX_TERM_PATH = 'lib/jmxterm.jar'


# hosts and ports

LOCALHOST = '127.0.0.1'

SSH_PORT = 22
OPS_CENTER_PORT = 8888

INTER_NODE = 7000
INTER_NODE_SSL = 7001
JMX_PORT = 7199

CLIENT_PORT = 9042
CLIENT_THRIFT_PORT = 9160


LOG_FILENAME = 'stress_test.log'


def config_log():
    """Configures the log.
    """
    logging.basicConfig(
        filename=LOG_FILENAME,
        filemode='w',
        format='%(asctime)s %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO
    )

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logging.getLogger('').addHandler(handler)


class JMXLogger(object):
    def __init__(self, cassandra_dir=CASSANDRA_DIR, jmx_term_path=JMX_TERM_PATH,
                 host=LOCALHOST, jmx_port=JMX_PORT, client_port=CLIENT_PORT):
        self.cassandra_dir = cassandra_dir
        self.jmx_term_path = jmx_term_path
        self.host = host
        self.jmx_port = jmx_port
        self.client_port = client_port

        self.nodetool = '%s/bin/nodetool' % cassandra_dir
        self.stress = '%s/tools/bin/cassandra-stress' % cassandra_dir

        self.pid = None
        self.cluster = None
        self.session = None


    def run(self):
        """Executes the monitoring of the Cassandra instance using JMX.
        """
        if self.is_cassandra_running():
            logging.info('Cassandra is RUNNING with PID %d\n' % self.pid)

            logging.info('Stress test STARTED')
            self.start_jmx_logging()

            # TODO create a process to run the stress test and keep a track

            self.stop_jmx_logging()
            logging.info('Stress test STOPPED')

            # TODO put into a Cassandra table and plot


    def is_cassandra_running(self):
        """Checks if JMX port is available and if there's a Cassandra instance
        running.
        """
        cmd_status = [self.nodetool, 'status', '-h %s' % self.host, '-p %d' % self.jmx_port]
        logging.info('Checking JMX connection to %s:%d' % (self.host, self.jmx_port))
        logging.info(' '.join(cmd_status))

        try:
            output = subprocess.check_output(cmd_status, stderr=subprocess.STDOUT)
            logging.info('%s\n' % output)

            self.pid = subprocess.check_output('ps aux | grep cassandra | grep \
                -v grep | awk \'{print $2}\'', shell=True)
            self.pid = int(re.sub(r'[^0-9]', '', str(self.pid)))

            return True

        except subprocess.CalledProcessError as e:
            logging.error(e.output)

            return False


    def start_jmx_logging(self):
        # cmd_jmxterm = ['java', '-jar']
        pass


    def stop_jmx_logging(self):
        # cmd_jmxterm = ['java', '-jar']
        pass


    def connect_to_cassandra(self):
        try:
            self.cluster = Cluster([self.host], self.client_port, protocol_version=3)
            self.session = self.cluster.connect()
            logging.info('Client connected to %s:%d\n' % (self.host, self.client_port))

            return

        except NoHostAvailable as e:
            logging.error(e.errors)

        sys.exit(1)


if __name__ == '__main__':
    # initialization
    config_log()

    jmxlogger = JMXLogger()
    jmxlogger.run()