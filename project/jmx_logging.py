#!/usr/bin/env python

"""Code to solve the exercise.
Do NOT forget to activate the virtual environment (or have the module 'cassandra'
installed in the root Python).

TODO study the package 'multiprocessing' and check if it's a good replacement to
'subprocess'.
"""


from cassandra.cluster import Cluster, NoHostAvailable
import logging
import os
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


LOG_FILENAME = 'jmx_test.log'
JMX_LOGFILENAME = 'jmx_metrics.csv'
JMX_TIME_INTERVAL = 2 # in seconds
STRESS_SLEEP_INTERVAL = 5 # in seconds
METRICS = ('LiveSSTableCount', 'AllMemTablesDataSize', '95thPercentile')


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
        self.metrics_writefile = open('metrics', 'ab')
        self.metrics_readfile = open('metrics', 'r')
        self.jmx_log_filename = JMX_LOGFILENAME
        self.jmx_log_file = None


    def run(self):
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

            self.start_jmx_logging()

            # starting stress test
            stress_thread = threading.Thread(target=self.cassandra_stress)
            stress_thread.start()

            # keep recording while stress_thread is running
            while stress_thread.isAlive():
                time.sleep(self.jmx_time_interval)
                self.log_JMX()

            self.stop_jmx_logging()

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
        # run java for self.host:self.jmx_port, in silent and non-interactive mode
        cmd_jmxterm = ['java', '-jar', self.jmxterm_path, '-n']
        #, '-l %s:%s' % (self.host,
        #self.jmx_port), '-v', 'silent', '-n']
        logging.info(' '.join(cmd_jmxterm))

        try:
            self.jmxterm_proc = subprocess.Popen(cmd_jmxterm,
                                                 stdin=subprocess.PIPE,
                                                 stdout=self.metrics_writefile,
                                                 stderr=self.metrics_writefile)
            # self.jmxterm_proc.wait()
            welcome_msg = ''
            while welcome_msg == '':
                time.sleep(sleeping_time)
                welcome_msg = self.metrics_readfile.readline().strip()
            self.jmxterm_proc.stdin.write(('open %s:%d\n' % (self.host, self.jmx_port)).encode())

            self.jmx_log_file = open(self.jmx_log_filename, 'w')
            self.jmx_log_file.write('%s,%s,%s\n' % (METRICS[0], METRICS[1], METRICS[2]))

        except subprocess.CalledProcessError as e:
            output = str(e.output).replace('\\n', '\n')[2 : -2]
            logging.error('%s\n' % output)
            sys.exit(1)


    def cassandra_stress(self, num_iter=50000, numthreads=4, sleeping_time=STRESS_SLEEP_INTERVAL):
        """The sleeping time is in seconds.
        """
        time.sleep(sleeping_time)
        logging.info('Stress test STARTED')
        cmd_stress = [self.stress_path, 'write', 'n=%d' % num_iter, '-rate threads=%d' %
                      numthreads]
        logging.info(' '.join(cmd_stress))

        try:
            output = subprocess.check_output(cmd_stress, stderr=subprocess.STDOUT)
            output = str(output).replace('\\n', '\n').replace('\\r', '\r')
            output = output.replace("\\'", "\'")[2 : -2]
            logging.info("%s" % output)

        except subprocess.CalledProcessError as e:
            logging.error('err_code: %d' % e.returncode)
            output = str(e.output)[2 : -2]
            logging.error(output)

        logging.info('Stress test STOPPED')
        time.sleep(sleeping_time)


    def log_JMX(self, sleeping_time=0.2):
        get_cf = r'get -s -b org.apache.cassandra.metrics:type=ColumnFamily,keyspace=keyspace1,scope=standard1,name=%s Value'
        getLiveSSTableCount = get_cf % 'LiveSSTableCount'
        getAllMemTablesDataSize = get_cf % 'AllMemTablesDataSize'
        get95thPercentile = r'get -s -b org.apache.cassandra.metrics:type=ClientRequest,scope=Write,name=Latency 95thPercentile'

        gets = [getLiveSSTableCount, getAllMemTablesDataSize, get95thPercentile]
        outputs = list()

        for get in gets:
            logging.info(get)
            self.jmxterm_proc.stdin.write(('%s\n' % get).encode())
            time.sleep(sleeping_time)
            output = self.metrics_readfile.readline().strip()
            output = 0 if output == '' else output
            outputs.append(output)

        print(outputs)

        self.jmx_log_file.write('%s,%s,%s\n' % (outputs[0], outputs[1], outputs[2]))
        logging.info('JMX metrics logged')


    def stop_jmx_logging(self):
        logging.info('JMX recording STOPPED')
        self.jmxterm_proc.stdin.write(('exit\n').encode())
        self.metrics_writefile.close()
        self.metrics_readfile.close()
        pass


if __name__ == '__main__':
    config_log()

    jmx_logger = JMX_Logger()
    jmx_logger.run()