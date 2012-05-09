#!/usr/bin/python


import os,re
from sshtools import Ssh


class physical_host:

  def __init__(self,server):
    self.server = server
    self.ssh = Ssh(self.server)

  def exec_cmd_ssh(self,cmd=''):
    result = self.ssh.exec_cmd(cmd)
    return result
 
  def get_memory(self):
    liste = self.exec_cmd_ssh('dmidecode -t memory | grep Size | grep MB')
    somme=0
    for i in liste:
      val = i.split(":")[1].strip().split()[0]
      somme = int(somme) + int(val)
    return somme

  def get_memory_swap(self):
    liste = self.exec_cmd_ssh('free -b | grep -i swap ')
    memory_swap = liste[0].split()[1]
    return memory_swap
  
  def get_memory1(self):
    liste = self.exec_cmd_ssh('free -m | grep -i Mem ')
    memory_swap = liste[0].split()[1]
    return memory_swap

  def get_mac_addr(self,interface):
    cmd = "ifconfig %s | grep HWaddr" % interface
    liste = self.exec_cmd_ssh(cmd)
    for i in liste:
      mac_addr = i.split()[4]
    return mac_addr

  def get_interfaces(self):
    liste = self.exec_cmd_ssh("cat /proc/net/dev | sed '1,2'd | grep eth")
    INTERFACE={}
    for i in liste:
      NOM_INTERFACE = i.split(":")[0].strip()
      MAC_ADDR = self.get_mac_addr(NOM_INTERFACE)
      INTERFACE[NOM_INTERFACE] = MAC_ADDR
    return INTERFACE

  def get_cpu(self):
    line = self.exec_cmd_ssh('cat /proc/cpuinfo | grep processor | wc -l')
    nb_cpu = line[0].strip()
    return nb_cpu

  def is_livecd(self):
    liste = self.exec_cmd_ssh('cat /etc/issue | grep -i slax | wc -l')
    if int(liste[0].strip()) >= 1:
	  return "true"
    else:
	  return "false"

  def get_idev(self):
    version = self.get_version_os()
    if version[0] == "CentOS":
      self.idev="cvda"
    if version[0] == "Ubuntu":
      self.idev="xvda"
    if version[0] == "Debian":
      self.idev="hda"
    return self.idev

  def get_partitions_para(self):
    self.get_idev()
    liste = self.exec_cmd_ssh('cat /etc/fstab | grep ^/dev | grep -v iso9660 | grep -v floppy | grep -v vfat')
    PARTITIONS={}
    cpt=1
    for i in liste:
      nom_device = i.split()[0].strip()
      fs = i.split()[2].strip()
      nom_part = i.split()[1].strip()
      taille = self.taille_part(nom_device,fs)
      if fs != "swap": 
        if cpt == 4:
          cpt=5
        nom_device_para="%s%s" % (self.idev,cpt)
        PARTITIONS[nom_device_para] = (nom_device,fs,taille,nom_part)
        cpt=(cpt + 1)
    for i in liste:
      nom_device = i.split()[0].strip()
      fs = i.split()[2].strip()
      if fs == "swap":
        nom_device_para="%s%s" % (self.idev,cpt)
        taille_swap = self.get_memory_swap()
        PARTITIONS[nom_device_para] = (nom_device,fs,taille_swap,nom_part)
    return PARTITIONS

  def taille_part(self,partition,filesystem):
    if (filesystem == "ext2") or (filesystem == "ext3") or (filesystem == "ext4"):
      return self.taille_part_ext(partition)
  
  def taux_occupation(self,partition,filesystem):
    if (filesystem == "ext2") or (filesystem == "ext3") or (filesystem == "ext4"):
      return self.taux_occupation_ext(partition)


  ######################################################################################
  ###################  FONCTIONS RESERVER POUR FILESYSTEM EXT   ########################
  ######################################################################################
  def taille_part_ext(self,partition):
    Bl_count = self.exec_cmd_ssh('tune2fs -l '+ partition +' | grep "Block count"')
    Bl_size = self.exec_cmd_ssh('tune2fs -l '+ partition +' | grep "Block size"')
    Bloc_count = Bl_count[0].split(":")[1].strip()
    Bloc_size = Bl_size[0].split(":")[1].strip()
    Taille = (int(Bloc_count) * int(Bloc_size))
    return Taille
  
  def taille_part_free_ext(self,partition):
    Bl_free = self.exec_cmd_ssh('tune2fs -l '+ partition +' | grep "Free blocks"')
    Bl_size = self.exec_cmd_ssh('tune2fs -l '+ partition +' | grep "Block size"')
    Bloc_free = Bl_free[0].split(":")[1].strip()
    Bloc_size = Bl_size[0].split(":")[1].strip()
    Taille_free = (int(Bloc_free) * int(Bloc_size))
    return Taille_free

  def taux_occupation_ext(self,partition):
    taille_total = self.taille_part_ext(partition)
    taille_libre = self.taille_part_free_ext(partition)
    tx_occup = (taille_libre * 100) / taille_total
    return tx_occup







  def get_all_partitions(self):
    ALL_PARTITIONS={}
    ALL_PARTITIONS["PARA"] = (self.get_partitions_para())
    ALL_PARTITIONS["HVM"] = (self.get_partitions_hvm())
    return ALL_PARTITIONS

  def get_partitions_hvm(self):
    #self.detect_lvm()
    cpt='`'
    liste = self.exec_cmd_ssh('LANG=POSIX fdisk -l /dev/cciss/c0d0 2> /dev/null | grep "^Disk /dev" | grep -v "mapper" | sed "s/Disk//" | sed "s#/dev/##"')
    PARTITION={}
    for i in liste:
       nom_part = i.split(":")[0].strip()
       nom_part_hvm = "hd%s" % chr(ord(cpt) + 1)
       taille = i.split(",")[1].split()[0]
       PARTITION[nom_part] = (nom_part_hvm,taille)
    return PARTITION
    # {'cciss/c0d0': ('hda', '120034123776'),'cciss/c0d1': ('hdb', '120034123776')}

  def detect_lvm(self):
    detect_lvm = "0"
    nb_lv = self.exec_cmd_ssh('LANG=POSIX fdisk -l 2> /dev/null| grep "^Disk /dev" | grep mapper | wc -l')
    if  nb_lv[0].strip() >= 1:
      detect_lvm = "1"
    if detect_lvm == "1": 
      print "LVM detecte, en mode HVM, le LVM sera fait dans la VM."
 
  def is_lv(self,fs):
    check_is_lv = self.exec_cmd_ssh('lvdisplay | grep \"%s\" | wc -l' % fs)
    if check_is_lv[0] >= 1:
      return 1
    else:
      return 0
 
  def get_version_os(self):
    liste = self.exec_cmd_ssh('cat /etc/issue')
    os_version=[]
    if liste[0].split()[0] == "CentOS":
      os_version = [liste[0].split()[0],liste[0].split()[2]]
    if liste[0].split()[0] == "Ubuntu":
      os_version = [liste[0].split()[0],liste[0].split()[1]]
    if liste[0].split()[0] == "Debian":
      os_version = [liste[0].split()[0],liste[0].split()[2]]
    return os_version

