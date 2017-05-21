#!/usr/bin/python
# -*- coding: utf-8 -*-


import os,sys, re, time
#from p2v_xen_host import xen_host
from .sshtools import Ssh
from xen.xm.XenAPI import Session


class pxe :
  #def __init__(self):
    #self.pxe = xen_host()


  def install_pxe(self,vlan,vgname,ip_pxe,ip_vm,ip_xen,vm_name,mac_addr,bridge):
    print("\n ----- Création des LVM : -----\n")
    os.system("lvcreate -L3G -n PXESERVER-VLAN%s %s" % (vlan,vgname))
    os.system("lvcreate -L256 -n PXESERVER-VLAN%s-swap %s" % (vlan,vgname))

    print("\n ----- Création du FileSystem : -----\n")
    os.system("mkfs.ext3 -q -j /dev/%s/PXESERVER-VLAN%s" % (vgname,vlan))
    os.system("mkswap -v1 /dev/%s/PXESERVER-VLAN%s-swap" % (vgname,vlan))

    print("\n ----- Création et montage de PXE : -----\n")
    os.system("mkdir /vhosts/PXESERVER-VLAN%s" % vlan)
    os.system("mount /dev/%s/PXESERVER-VLAN%s /vhosts/PXESERVER-VLAN%s" % (vgname,vlan,vlan))

    print("\n ----- Décompression de l'archive : -----\n")
    os.system("tar jxf /etc/xen/P2V/lib/Serveur_pxe.tar.bz2 -C /vhosts/PXESERVER-VLAN%s" % vlan)
    
    print("\n ----- Démontage du PXE : -----\n")
    os.system("umount /vhosts/PXESERVER-VLAN%s" % vlan)
    
    print("\n ----- Check du FileSystem : -----\n")
    os.system("fsck.ext3 -f -y /dev/%s/PXESERVER-VLAN%s" % (vgname,vlan))
    
    result=""
    rep_mount = "/vhosts/PXESERVER-VLAN%s" % vlan 
    
    print("\n ----- Montage du PXE : -----\n")
    os.system("mount /dev/%s/PXESERVER-VLAN%s /vhosts/PXESERVER-VLAN%s" % (vgname,vlan,vlan))
    
    print("\n ----- Configuration du PXE : -----\n")
    #### FICHIER NETWORK ####
    fic_network = rep_mount + "/etc/sysconfig/network"
    fic_network_tpl = rep_mount + "/etc/sysconfig/network.template"
    result = file(fic_network_tpl,"r").read().replace("<ID_VLAN>",str(vlan))
    file(fic_network,"w").write(result)
    #### FICHIER NETWORK IFCFG_ETH0 #####
    fic_network_eth0 = rep_mount + "/etc/sysconfig/network-scripts/ifcfg-eth0"
    fic_network_eth0_tpl = rep_mount + "/etc/sysconfig/network-scripts/ifcfg-eth0.template"
    result = file(fic_network_eth0_tpl,"r").read().replace("<IP_PXE>",ip_pxe).replace("<IP_XEN>",ip_xen)
    file(fic_network_eth0,"w").write(result)
    #### FICHIER DHCPD.CONF #####
    fic_dhcpd_conf = rep_mount + "/etc/dhcpd.conf"
    fic_dhcpd_conf_tpl = rep_mount + "/etc/dhcpd.conf.template"
    ip_network = ip_pxe.rsplit(".",1)[0]
    result = file(fic_dhcpd_conf_tpl,"r").read().replace("<IP_NETWORK>",ip_network).replace("<IP_PXE>",ip_pxe).replace("<ID_VLAN>",str(vlan))
    file(fic_dhcpd_conf,"w").write(result)
    #### FICHIER DHCPD VLAN ####
    fic_dhcpd_vlan = rep_mount + "/etc/dhcpd/conf/vlan" + str(vlan)
    fic_dhcpd_vlan_tpl = rep_mount + "/etc/dhcpd/conf/vlan.template"
    result = file(fic_dhcpd_vlan_tpl,"r").read().replace("<VM_NAME>",vm_name).replace("<MAC_ADDR>",mac_addr).replace("<IP_VM>",ip_vm)
    file(fic_dhcpd_vlan,"a").write(result)
    #### FICHIER PXELINUX.CFG default ####
    fic_pxelinux = rep_mount + "/tftpboot/pxelinux.cfg/default"
    fic_pxelinux_tpl = rep_mount + "/tftpboot/pxelinux.cfg/default.template"
    result = file(fic_pxelinux_tpl,"r").read().replace("<IP_PXE>",ip_pxe)
    file(fic_pxelinux,"w").write(result)
    
    print("\n ----- Copie de la clef public dans LiveCD : -----\n")
    #os.system("cp "+ rep_mount +"/root/.ssh/authorized_keys "+ rep_mount +"/tftpboot/images/slax/slax/rootcopy/root/.ssh/")
    #### FICHIER AUTORUN SYSRESCUECD pour deployer clef public ssh ####
    fic_autorun = rep_mount + "/tftpboot/images/sysrescue/script/autorun"
    result = file(fic_autorun,"r").read().replace("169.254.1.254",ip_pxe)
    file(fic_autorun,"w").write(result)

    print("\n ----- Démontage du PXE : -----\n")
    os.system("umount /vhosts/PXESERVER-VLAN%s" % vlan)

    print("\n ----- Préparation de conf xen PXE : -----\n")
    #### FICHIER CONF XEN VM PXE ####
    fic_xen_vm_pxe = "/etc/xen/vm/PXESERVER-VLAN%s" % vlan
    fic_xen_vm_pxe_tpl = "/etc/xen/P2V/lib/PXESERVER-VLAN.template"
    result = file(fic_xen_vm_pxe_tpl,"r").read().replace("<ID_VLAN>",str(vlan)).replace("<BRIDGE>",bridge).replace("<VG>",vgname)
    file(fic_xen_vm_pxe,"w").write(result)


    print("\n ----- Démarrage de la VM PXE : -----\n")
    os.system("cd /etc/xen/auto ; ln -s /etc/xen/vm/PXESERVER-VLAN%s" % vlan)
    os.system("cd /etc/xen/vm ; xm create PXESERVER-VLAN%s" % vlan)



  def add_filter_dhcpd(self,ip_pxe,vm_name,mac_addr,ip_vm,vlan):
    print("Ajout du filtre dhcp  -> '%s, %s, %s, %s'" % (vm_name,mac_addr,ip_vm,vlan))
    ssh_pxe = Ssh(ip_pxe)
    ssh_pxe.exec_cmd("pxe_AddFilterDhcpd %s %s %s %s" % (vm_name,mac_addr,ip_vm,vlan))


  def waiting_cnx_pxe(self,ip_pxe,timeout=60):
    compteur = 0
    print("Attente de connexion avec le serveur PXE ...")

    while 1:
      compteur += 1
      time.sleep(1)
      P = os.system("ping -c 1 -i 1 %s > /dev/null" % ip_pxe)
      if P == 0:
        time.sleep(15)
        print("Serveur PXE est démarré")
        break
      if compteur == timeout:
        sys.exit()

  def add_lock_dhcpd(self,ip_pxe,vm_name):
    ssh_pxe = Ssh(ip_pxe)
    ssh_pxe.exec_cmd("pxe_AddLockDhcpd %s" % vm_name)



  def del_lock_dhcpd(self,ip_pxe,vm_name):
    ssh_pxe = Ssh(ip_pxe)
    ssh_pxe.exec_cmd("pxe_DelLockDhcpd %s" % vm_name)
 


  def is_pxe(self, ip_pxe,vlan,timeout=10):
    compteur = 0
    print("Attente de connexion avec un serveur PXE existant ...")
    
    bool = False
    
    while 1:
      compteur += 1
      time.sleep(1)
      P = os.system("ping -c 1 -i 1 %s > /dev/null" % ip_pxe)
      if P == 0:
        print("Un Serveur PXE pour le vlan %s existe déjà." % vlan)
        bool = True
        break
      if compteur == timeout:
        bool = False
        break
    return bool

            
  #def is_pxe(self, vlan):
  #  session = Session('httpu:///var/run/xend/xen-api.sock')
  #  session.xenapi.login_with_password('', '')
  #  
  #  bool = False
  #
  #  VM_PXE_ID = session.xenapi.VM.get_by_name_label('PXESERVER-VLAN%s' % vlan)
  #
  #  for vm in VM_PXE_ID:
  #    record = session.xenapi.VM.get_record(vm)
  #    if record["power_state"] == "Running":
  #      bool = True
  #    else:
  #      print "VM PXESERVER-VLAN%s n'est pas démarrée" % vlan
  #      bool = False
  #  return bool
