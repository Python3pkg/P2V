#!/usr/bin/python


import os

class Ssh:
  def __init__(self,server):
    self.server = server

  def del_keyfile(self):
     os.popen("ssh-keygen -R %s" % self.server,"r")

  def copy_id(self):
     print "### Copie des clefs : ###\n"
     os.popen("ssh-copy-id %s" % self.server,"r")

  def exec_cmd(self,cmd=''):
    self.del_keyfile()
    CMD = os.popen("ssh -o 'StrictHostKeyChecking=no' root@%s '%s'" % (self.server,cmd),"r")
    ret = CMD.readlines()
    return ret

