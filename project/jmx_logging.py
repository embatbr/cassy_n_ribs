#!/usr/bin/env python

"""Code to solve the exercise.
Do NOT forget to activate the virtual environment (or have the module 'cassandra'
installed in the root Python).
"""


from cassandra.cluster import Cluster, NoHostAvailable
import logging
import numpy as np
import os
import pylab as pl
import re
import subprocess
import sys
import threading
import time


# default paths (change to the path of your installation)
CASSANDRA_DIR_PATH = './cassandra'
JMXTERM_PATH = './lib/jmxterm.jar'


# hosts and ports

LOCALHOST = '127.0.0.1'

SSH_PORT = 22
OPS_CENTER_PORT = 8888

INTER_NODE = 7000
INTER_NODE_SSL = 7001
JMX_PORT = 7199

CLIENT_PORT = 9042
CLIENT_THRIFT_PORT = 9160


LOG_FILENAME = 'jmx.log'
JMX_TIME_INTERVAL = 1
STRESS_AFTER_TIME = 5
METRICS = ['LiveSSTableCount', 'AllMemtablesLiveDataSize', 'Latency']


def config_log(filename=LOG_FILENAME):
    """Configures the log.
    """
    logging.basicConfig(
        filename=filename,
        filemode='w',
        format='%(asctime)s %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO
    )

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logging.getLogger('').addHandler(handler)


class JMX_Logger(object):
    def __init__(self, cassandra_dir_path=CASSANDRA_DIR_PATH, jmxterm_path=JMXTERM_PATH,
                 host=LOCALHOST, jmx_port=JMX_PORT, client_port=CLIENT_PORT):
        self.cassandra_dir_path = os.path.abspath(cassandra_dir_path)
        self.jmxterm_path = os.path.abspath(jmxterm_path)
        self.host = host
        self.jmx_port = jmx_port
        self.client_port = client_port

        self.nodetool_path = '%s/bin/nodetool' % self.cassandra_dir_path
        self.stress_path = '%s/tools/bin/cassandra-stress' % self.cassandra_dir_path

        self.pid = None
        self.version = None

        self.jmxterm_proc = None
        self.jmx_time_interval = JMX_TIME_INTERVAL
        self.stress_after_time = STRESS_AFTER_TIME
        self.metrics_logfile = None
        self.metrics_gets = dict()
        self.metrics = dict()


    def run(self, run_stress=True, check_metrics=True):
        """Executes the monitoring of the Cassandra instance running in a node,
        using JMX.
        """
        logging.info('Cassandra directory: %s' % self.cassandra_dir_path)
        logging.info('JMXTerm directory: %s' % self.jmxterm_path)
        logging.info('Host: %s\n' % self.host)

        if self.is_cassandra_running():
            self.get_pid()
            self.get_version()
            logging.info('Cassandra is RUNNING version %s with PID %d\n' %
                         (self.version, self.pid))

            if run_stress:
                self.start_jmx_logging()

                # starting stress test
                stress_thread = threading.Thread(target=self.cassandra_stress)
                stress_thread.start()

                # keep recording while stress_thread is running
                while stress_thread.isAlive():
                    time.sleep(self.jmx_time_interval)
                    self.log_metrics()

                self.stop_jmx_logging()

            if check_metrics:
                self.read_metrics_log()
                self.assert_metrics()
                self.plot_metrics()

            # TODO put into a Cassandra table
            # TODO plot

        else:
            logging.info('No Cassandra instance found')
            logging.info('Exiting program with errors')
            sys.exit(1)


    def is_cassandra_running(self):
        """Checks (through JMX port) if there's a Cassandra instance running.
        """
        logging.info('Checking JMX connection to %s:%d' % (self.host, self.jmx_port))
        cmd_status = [self.nodetool_path, 'status', '-h %s' % self.host, '-p %d' % self.jmx_port]
        logging.info(' '.join(cmd_status))

        try:
            output = subprocess.check_output(cmd_status, stderr=subprocess.STDOUT)
            output = str(output).replace('\\n', '\n').replace('\\r', '\r')[2 : -2]
            logging.info('%s\n' % output)
            return True

        except subprocess.CalledProcessError as e:
            output = str(e.output).replace('\\n', '\n').replace('\\r', '\r')
            logging.error('%s\n' % output)
            return False


    def get_pid(self):
        """Gets the process ID.
        """
        try:
            cmd_pid = 'ps aux | grep cassandra | grep -v grep | awk \'{print $2}\''
            logging.info(cmd_pid)
            pid_sh = subprocess.check_output(cmd_pid, stderr=subprocess.STDOUT,
                                             shell=True)
            self.pid = int(re.sub(r'[^0-9]', '', str(pid_sh)))

        except subprocess.CalledProcessError as e:
            output = str(e.output).replace('\\n', '\n').replace('\\r', '\r')
            logging.error('%s\n' % output)
            sys.exit(1)


    def get_version(self):
        """Gets the version of the Cassandra instance running.
        """
        try:
            cmd_version = [self.nodetool_path, 'version', '-h %s' % self.host,
                           '-p %d' % self.jmx_port]
            logging.info(' '.join(cmd_version))
            version_sh = subprocess.check_output(cmd_version, stderr=subprocess.STDOUT)
            version_sh = str(version_sh).replace('\\n', '\n')[2 : -2]
            self.version = version_sh.replace('ReleaseVersion:', '').strip() # meio pog

        except subprocess.CalledProcessError as e:
            output = str(e.output).replace('\\n', '\n').replace('\\r', '\r')
            logging.error('%s\n' % output)
            sys.exit(1)


    def start_jmx_logging(self, sleeping_time=1):
        logging.info('JMX Recording STARTED')
        cmd_jmxterm = ['java', '-jar', self.jmxterm_path, '-n']
        logging.info(' '.join(cmd_jmxterm))
        self.metrics_logfile = open('metrics.log', 'wb')

        try:
            self.jmxterm_proc = subprocess.Popen(cmd_jmxterm,
                                                 stdin=subprocess.PIPE,
                                                 stdout=self.metrics_logfile,
                                                 stderr=self.metrics_logfile)

            cmd_open = 'open %s:%d\n' % (self.host, self.jmx_port)
            self.jmxterm_proc.stdin.write(cmd_open.encode())

            self.metrics_gets[METRICS[0]] = 'get -s -b org.apache.cassandra.metrics:\
type=ColumnFamily,keyspace=keyspace1,scope=standard1,name=%s Value' % METRICS[0]
            self.metrics_gets[METRICS[1]] = 'get -s -b org.apache.cassandra.metrics:\
type=ColumnFamily,keyspace=keyspace1,scope=standard1,name=%s Value' % METRICS[1]
            self.metrics_gets[METRICS[2]] = 'get -s -b org.apache.cassandra.metrics:\
type=ClientRequest,scope=Write,name=%s 95thPercentile' % METRICS[2]

        except subprocess.CalledProcessError as e:
            output = str(e.output).replace('\\n', '\n')[2 : -2]
            logging.error('%s\n' % output)
            sys.exit(1)


    def cassandra_stress(self, num_iter=1000000, num_threads=10):
        """The sleeping time is in seconds.
        """
        logging.info('Stress test STARTED')
        cmd_stress = [self.stress_path, 'write', 'no-warmup', 'n=%d' % num_iter,
                      '-rate threads=%d' % num_threads]
        logging.info(' '.join(cmd_stress))

        try:
            output = subprocess.check_output(cmd_stress, stderr=subprocess.STDOUT)
            output = str(output).replace('\\n', '\n').replace('\\r', '\r')
            output = output.replace("\\'", "\'")[2 : -2]
            logging.info("%s" % output)
            time.sleep(self.stress_after_time)

        except subprocess.CalledProcessError as e:
            logging.error('err_code: %d' % e.returncode)
            output = str(e.output).replace('\\n', '\n').replace('\\r', '\r')
            output = output.replace("\\'", "\'")[2 : -2]
            logging.error(output)

        logging.info('Stress test STOPPED')


    def log_metrics(self):
        for key in self.metrics_gets.keys():
            get = self.metrics_gets[key]
            logging.info(get)
            self.jmxterm_proc.stdin.write(('%s\n' % get).encode())


    def stop_jmx_logging(self):
        logging.info('JMX recording STOPPED\n')
        self.jmxterm_proc.stdin.write(('exit\n').encode())
        self.metrics_logfile.close()


    def read_metrics_log(self):
        for METRIC in METRICS:
            self.metrics[METRIC] = list()

        self.metrics_logfile = open('metrics.log')
        lines = self.metrics_logfile.readlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            i = i + 1

            if line.startswith('#mbean'):
                result = re.search('name=', line)

                if not result is None:
                    end_pos = result.span()[1]
                    key = line[end_pos : -1]
                    line = lines[i].strip()
                    i = i + 1

                    line = float(line) if key == 'Latency' else int(line)
                    self.metrics[key].append(line)

        for METRIC in METRICS:
            self.metrics[METRIC] = np.array(self.metrics[METRIC])


    def assert_metrics(self):
        logging.info('Asserting metrics')

        for METRIC in METRICS:
            metrics = self.metrics[METRIC]

            if np.sum(metrics) == 0.0:
                logging.info('%s has ALL its elements with value ZERO' % METRIC)
            elif len(metrics[metrics == 0]) > 0:
                logging.info('%s has ZEROS' % METRIC)

            if len(metrics[metrics < 0]) > 0:
                logging.info('%s has NEGATIVE values' % METRIC)


    def plot_metrics(self):
        logging.info('Plotting metrics')

        kwargs = ['ro-', 'go-', 'bo-']
        position = 1
        for (METRIC, kwarg) in zip(METRICS, kwargs):
            metrics = self.metrics[METRIC]
            pl.subplot(3, 1, position)
            pl.grid(True)
            pl.plot(metrics, kwarg)
            pl.ylabel(METRIC)

            position = position + 1

        pl.show()


if __name__ == '__main__':
    config_log()

    jmx_logger = JMX_Logger()
    jmx_logger.run()