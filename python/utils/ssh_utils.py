#!/usr/bin/python

import subprocess
import sys
import time

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
        print 'STATUS: SSH {}:{}. output:'.format(hostname,command)
        for line in result:
            print '{}|out>'.format(hostname),line,
        for line in error:
            print '{}|err>'.format(hostname),line,
    if result ==[] and error != []:
        print >>sys.stderr, "ERROR: %s" % error
        exit(-1)
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
    print 'STATUS: running SCP command:',' '.join(l)
    scp = subprocess.Popen(l,
                        shell=False,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
    while scp.poll()is None:
        time.sleep(0.05)
    print 'STATUS: SCP output:'
    result = scp.stdout.readlines()
    for line in result:
        print line
    error = scp.stderr.readlines()
    if error != []:
        print error
        exit(-1)
    return (result,error)
