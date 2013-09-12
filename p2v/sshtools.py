#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

class Ssh:
  def __init__(self,server):
    self.server = server

  def del_keyfile(self):
     os.popen("ssh-keygen -R %s 2>/dev/null" % self.server,"r")
     
  def del_keyfile_client(self, srv):
     os.popen("ssh-keygen -R %s 2>/dev/null" % srv,"r")

  def copy_id(self):
     print "### Copie des clefs : ###\n"
     os.popen("ssh-copy-id -i /etc/xen/P2V/ssh/p2v.key.pub %s 2>/dev/null" % self.server,"r")

  def copy_id_client(self, srv):
     os.popen("ssh-copy-id -i /etc/xen/P2V/ssh/p2v.key.pub %s 2>/dev/null" % srv,"r")

  def exec_cmd(self,cmd=''):
    CMD = os.popen("ssh -i /etc/xen/P2V/ssh/p2v.key -o 'StrictHostKeyChecking=no' root@%s '%s'" % (self.server,cmd),"r")
    ret = CMD.readlines()
    return ret

  def put_file(self,local_file='',remote_dir=''):
    os.popen("scp -i /etc/xen/P2V/ssh/p2v.key -o 'StrictHostKeyChecking=no' %s root@%s:%s" % (local_file,self.server,remote_dir),"r")
  
  def get_file(self,remote_file='',local_dir=''):
    os.popen("scp -i /etc/xen/P2V/ssh/p2v.key -o 'StrictHostKeyChecking=no' root@%s:%s %s" % (self.server,remote_file,local_dir),"r")
    
