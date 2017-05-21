#!/usr/bin/python
# -*- coding: utf-8 -*-


from .sshtools import Ssh
from . import p2v_xen_host
import os, re

class GenConfNetwork(object):
  def __init__(self):
    self.xen_host = p2v_xen_host.xen_host()

  def get_file_network(self):
    self.ssh.get_file("/etc/network/interfaces", "%s/interfaces" % self.LocalDir)
    if os.path.isfile("%s/interfaces" % self.LocalDir):
      self.xen_host.exec_cmd("cp %s/interfaces %s/interfaces.pre.p2v" % (self.LocalDir,self.LocalDir))
    
  def put_file_network(self):
    self.ssh.put_file("%s/interfaces.pre.p2v" % self.LocalDir, "/etc/network/")
  
  def remplace(self,file_pattern,pattern,value):
    result = file(file_pattern,"r").read().replace(pattern,value,1)
    file(file_pattern,"w").write(result)
  
  def DeleteLineInFile(self,file_pattern,pattern):
    self.xen_host.exec_cmd("cp %s %s.old" % (file_pattern,file_pattern))
    ligne = file(file_pattern + ".old","r").readlines()
    for elt in enumerate(ligne):
      if pattern in elt[1]:
        del ligne[elt[0]]
    fichier = open(file_pattern,"w")
    for i in ligne:
      fichier.write(i)
    fichier.close()

  def GenerateFileNetwork(self):
    self.ssh = Ssh(self.ip_physique)
    self.get_file_network()
    line = open("%s/interfaces" % self.LocalDir , "r").read()
    for i in self.xen_host.tri_inverse(self.interfaces):
      chaine_local_eth = "%s" % self.interfaces[i]["LOCAL_INTERFACE"]
      chaine_new_eth = "%s" % i
      print("remplace %s par %s" % (chaine_local_eth, chaine_new_eth))
      line = line.replace(chaine_local_eth,chaine_new_eth)
      device_vlan = "vlan-raw-device" 
      self.DeleteLineInFile("%s/interfaces.pre.p2v" % self.LocalDir,device_vlan)
    fichier = open("%s/interfaces.pre.p2v" % self.LocalDir , "w")
    fichier.write(line)
    fichier.close()
    self.put_file_network()
  
 # def GenerateFileNetwork(self):
 #   self.ssh = Ssh(self.ip_physique)
 #   self.get_file_network()
 #   for i in self.xen_host.tri(self.interfaces):
 #     print i
 #     fichier = open("%s/interfaces" % self.LocalDir , "r")
 #     chaine_eth = "iface %s " % i
 #     chaine_vlan = "iface vlan%s " % self.interfaces[i]["VLAN"]
 #     auto_eth = "auto %s" % i
 #     auto_vlan = "auto vlan%s" % self.interfaces[i]["VLAN"]
 #     num_vlan = "vlan%s" % self.interfaces[i]["VLAN"]
 #     device_vlan = "vlan-raw-device" 
 #     self.DeleteLineInFile("%s/interfaces.pre.p2v" % self.LocalDir,device_vlan)
 #     for ligne in fichier:
 #       if chaine_eth in ligne:
 #         print "%s deja present" % i
 #       else:
 #         if chaine_vlan in ligne:
 #           print ligne
 #           self.remplace("%s/interfaces.pre.p2v" % self.LocalDir, chaine_vlan, chaine_eth)
 #           self.remplace("%s/interfaces.pre.p2v" % self.LocalDir, auto_vlan, auto_eth)
 #           self.remplace("%s/interfaces.pre.p2v" % self.LocalDir, num_vlan, i)
 #           print "vlan %s trouvé, puis modifié en %s" % (self.interfaces[i]["VLAN"],i)
 #   self.put_file_network()