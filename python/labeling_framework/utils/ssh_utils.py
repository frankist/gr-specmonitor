#!/usr/bin/python

import subprocess
import sys
import time
from . import logging_utils
logger = logging_utils.DynamicLogger(__name__)

def ssh_run(hostname,command,printstdout=True,logfilename=None):
    ssh = subprocess.Popen(["ssh", "%s" % hostname, command],
                        shell=False,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
    while ssh.poll() is None:
        time.sleep(0.05)
    result = ssh.stdout.readlines()
    error = ssh.stderr.readlines()
    if logfilename is not None: # write to a fine
        r= 'out> '.join(result)
        e= 'err> '.join(error)
        with open(logfilename,'w') as f:
            f.write(r)
            f.write(e)
    if printstdout:
        logger.info('SSH {}:{}. output:'.format(hostname,command))
        for line in result:
            logger.info('{}|out> {}'.format(hostname,line))
        for line in error:
            logger.info('{}|err> {}'.format(hostname,line))
    if result ==[] and error != []:
        logger.exception('Remote {} has failed with error: {}'.format(hostname,error))
        raise AssertionError()
    return (result,error)

def scp_send(hostname,localfile,remotefile,folder=False):
    return scp_command(hostname,localfile,remotefile,True,folder)
def scp_recv(hostname,localfile,remotefile,folder=False):
    return scp_command(hostname,localfile,remotefile,False,folder)

def scp_command(hostname,localfile,remotefile,send=True,folder=False):
    l = ['scp']
    if folder==True:
        l.append('-r')
    if send==True:
        l.append(localfile)
        l.append("{}:{}".format(hostname,remotefile))
    elif send==False:
        l.append("{}:{}".format(hostname,remotefile))
        l.append(localfile)
    logger.debug('Running SCP command: {}'.format(' '.join(l)))
    scp = subprocess.Popen(l,
                        shell=False,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
    while scp.poll()is None:
        time.sleep(0.05)
    logger.info('SCP output:')
    result = scp.stdout.readlines()
    for line in result:
        logger.info('> '+line)
    error = scp.stderr.readlines()
    if error != []:
        logger.exception('Could not transfer file. Got error: {}'.format(error))
        raise AssertionError()
    return (result,error)
