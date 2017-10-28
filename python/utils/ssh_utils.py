#!/usr/bin/python

import subprocess
import sys
import time

def ssh_run(hostname,command,printstdout=True):
    ssh = subprocess.Popen(["ssh", "%s" % hostname, command],
                        shell=False,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
    while ssh.poll()==None:
        time.sleep(0.05)
    result = ssh.stdout.readlines()
    error = ssh.stderr.readlines()
    if result == []:
        if error != []:
            print >>sys.stderr, "ERROR: %s" % error
            exit(-1)
    elif printstdout==True:
        print 'STATUS: SSH {}:{}. output:'.format(hostname,command)
        print result
    return (result,error)

def scp_send(hostname,localfile,remotefile):
    scp_command(hostname,localfile,remotefile,True)
def scp_recv(hostname,localfile,remotefile):
    scp_command(hostname,localfile,remotefile,False)

def scp_command(hostname,localfile,remotefile,send=True):
    if send==True:
        l = ["scp",localfile,"{}:{}".format(hostname,remotefile)]
    else:
        l = ["scp","{}:{}".format(hostname,remotefile),localfile]
    scp = subprocess.Popen(l,
                        shell=False,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
    while scp.poll()==None:
        time.sleep(0.05)
    print 'STATUS: SCP output:'
    result = scp.stdout.readlines()
    error = scp.stderr.readlines()
    if result == []:
        if error != []:
            print >>sys.stderr, "ERROR: %s" % error
            exit(-1)
    else:
        print result
    return (result,error)
