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
    if version["OS"] == "CentOS":
      self.idev="xvda"
    if version["OS"] == "Ubuntu":
      self.idev="xvda"
    if version["OS"] == "Debian":
      self.idev="hda"
    return self.idev

  def copy_fstab(self):
    copy_file_fstab = self.exec_cmd_ssh('cp /etc/fstab /etc/fstab_without_uuid')

  def cible_link_uuid(self,uuid):
    nom_device = self.exec_cmd_ssh('readlink -f /dev/disk/by-uuid/%s' % uuid)
    return nom_device

  def get_fstab_without_uuid(self):
    self.copy_fstab()
    liste = self.exec_cmd_ssh('cat /etc/fstab | grep ^UUID')
    for i in liste:
      uuid = i.split()[0].split('=')[1]
      cible = self.cible_link_uuid(uuid)
      self.exec_cmd_ssh('sed -i s#UUID=%s#%s# /etc/fstab_without_uuid' % (uuid,cible[0].strip()))

  def get_partitions_para(self):
    self.get_idev()
    self.get_fstab_without_uuid()
    liste = self.exec_cmd_ssh('cat /etc/fstab_without_uuid | grep ^/dev | grep -v iso9660 | grep -v floppy | grep -v vfat | grep -v cdrom')
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
    tx_occup = 100 - ((taille_libre * 100) / taille_total)
    return tx_occup


  def Convert_to_octects(self,taille):
    """ converti Ko, Mo, Go  et To en octets """
    



  def get_all_partitions(self):
    ALL_PARTITIONS={}
    ALL_PARTITIONS["PARA"] = (self.get_partitions_para())
    return ALL_PARTITIONS

  def detect_lvm(self):
    detect_lvm = "0"
    nb_lv = self.exec_cmd_ssh('LANG=POSIX fdisk -l 2> /dev/null| grep "^Disk /dev" | grep mapper | wc -l')
    if  nb_lv[0].strip() >= 1:
      detect_lvm = "1"
    if detect_lvm == "1": 
      print "LVM detecte, en mode HVM, le LVM sera fait dans la VM."

  def detect_lvdisplay(self):
    detect = self.exec_cmd_ssh('which lvdisplay | wc -l')
    return detect[0]

 
  def is_lv(self,fs):
    if self.detect_lvdisplay() != 0:
      check_is_lv = self.exec_cmd_ssh('lvdisplay | grep \"%s\" | wc -l' % fs)
      if check_is_lv[0] >= 1:
        return 1
      else:
        return 0
    else:
      return 0
 
  def get_version_os(self):
    liste = self.exec_cmd_ssh('cat /etc/issue')
    os_version=[]
    if liste[0].split()[0] == "CentOS":
      os_version = {"OS":liste[0].split()[0],"VERSION":liste[0].split()[2]}
    if liste[0].split()[0] == "Ubuntu":
      os_version = {"OS":liste[0].split()[0],"VERSION":liste[0].split()[1]}
    if liste[0].split()[0] == "Debian":
      os_version = {"OS":liste[0].split()[0],"VERSION":liste[0].split()[2]}
    return os_version

  def get_eligibility_check_fstab(self):
    CHECK_LABEL = self.exec_cmd_ssh('less /etc/fstab | grep ^LABEL= | wc -l')
    CHECK_LABEL = CHECK_LABEL[0].strip()
    if CHECK_LABEL == "0":
      ret = 1
    else:
      ret = 0
    return ret

  def get_eligibility_check_fs_ext(self):
    CHECK_FS_EXT = self.exec_cmd_ssh('df -x tmpfs -x swap -x proc -x sys -x ext2 -x ext3 -x ext4 2>/dev/null | wc -l')
    CHECK_FS_EXT = CHECK_FS_EXT[0].strip()
    if CHECK_FS_EXT == "0":
      ret = 1
    else:
      ret = 0
    return ret

  def get_eligibility_check_network_file_p2v(self):
    CHECK_NETWORK_FILE_P2V = self.exec_cmd_ssh('ls /etc/network/interfaces.pre.p2v 2>/dev/null | wc -l')
    CHECK_NETWORK_FILE_P2V = CHECK_NETWORK_FILE_P2V[0].strip()
    if CHECK_NETWORK_FILE_P2V == "1":
      ret = 1
    else:
      ret = 0
    return ret
    
