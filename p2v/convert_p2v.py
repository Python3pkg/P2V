#!/usr/bin/env python
# -*- coding: utf-8 -*-

from p2v_xen_host import xen_host
from pxe_server import pxe
import os,sys,shutil

from optparse import OptionParser

class convert_p2v(object):
  def __init__(self):
    pass

  def boot_pxe(self):
      if not hasattr(self.hote_xen, 'mac_addr'):
        mac_addr = self.hote_xen.mac_addr_v2p
        if mac_addr == "":
          print "il manque la directive (MAC_ADDR = \"AA:BB:CC:DD:EE:FF\") dans le fichier de config pour %s . Cette directive est specifique pour demarrer que le PXE" % self.hote_xen.vmnamecfengine
          sys.exit()
      else:
        mac_addr = self.hote_xen.mac_addr

      if self.pxe.is_pxe(self.hote_xen.ip_pxe, self.hote_xen.vlan) == False:
        self.pxe.install_pxe(self.hote_xen.vlan, self.hote_xen.vgname, self.hote_xen.ip_pxe, self.hote_xen.ip_physique, self.hote_xen.ip_xen, self.hote_xen.vmnamecfengine, mac_addr, self.hote_xen.bridge_prefix)
        self.pxe.waiting_cnx_pxe(self.hote_xen.ip_pxe)
        self.pxe.add_filter_dhcpd(self.hote_xen.ip_pxe, self.hote_xen.vmnamecfengine, mac_addr, self.hote_xen.ip_physique,self.hote_xen.vlan)
        self.pxe.add_lock_dhcpd(self.hote_xen.ip_pxe, self.hote_xen.vmnamecfengine)
      else:
        self.pxe.add_filter_dhcpd(self.hote_xen.ip_pxe, self.hote_xen.vmnamecfengine, mac_addr, self.hote_xen.ip_physique,self.hote_xen.vlan)
        self.pxe.add_lock_dhcpd(self.hote_xen.ip_pxe, self.hote_xen.vmnamecfengine)


  def P2V_PHASE_POSTINSTALL(self):
    self.hote_xen.import_all_variables(self.VM_NAME)
    self.hote_xen.post_install()

  def P2V_PHASE_ELIGIBILITY(self):
    self.hote_xen.check_vgname()
    if self.hote_xen.get_name_vm_dest() != self.VM_NAME:
      print "LE FQDN ne corresponds pas."
      sys.exit() 
 
    print "#### PHASE ELIGIBILITY ####"
    self.hote_xen.get_eligibility()
    self.hote_xen.rapport_eligibility()
    sys.exit()
  
  def P2V_PHASE_1(self):
    self.hote_xen.check_vgname()
    if self.hote_xen.get_name_vm_dest() != self.VM_NAME:
      print "LE FQDN ne corresponds pas."
      sys.exit()

    print "#### PHASE 1/3 ####"
    self.hote_xen.get_info_srv_physique()
    print self.hote_xen.affiche_rapport()
  
    self.hote_xen.generation_fichier_p2v()
    print self.hote_xen.endphase()

  def P2V_PHASE_2(self):
    if self.hote_xen.is_livecd() == "True":
      print "#### PHASE 3/3 ####"
      self.hote_xen.import_all_variables(self.VM_NAME)
      self.hote_xen.exec_cmd_p2v()
      self.hote_xen.post_install()
    else:
      if self.hote_xen.no_pxe == False:
        print "#### PHASE 2/3 ####"
        print "Installation / Configuration du Serveur PXE"
      else:
        print "#### PHASE 2/3 ####"
        print "!!! ATTENTION L'OPTION 'SERVEUR PXE' A ETE DESACTIVE AFIN DE PASSER PAR UN LIVECD DANS LE CDROM !!!"
        print "Installation / Configuration du Serveur PXE avec le DHCP uniquement"
      self.boot_pxe()

      if self.hote_xen.no_pxe == False:
        print "\n\n!!! IMPORTANT AVANT DE POURSUIVRE !!! \n Le serveur PXE est démarré.\n Veuillez au paravant UnTagger le port du switch avec le vlan %s\n puis redemarrer votre serveur physique afin que celui ci boot en PXE.\n\n Une fois ces actions effectuées, relancer le p2v" % self.hote_xen.vlan
      else:
        print "\n\n!!! IMPORTANT AVANT DE POURSUIVRE !!! \n Le serveur DHCP est démarré.\n Veuillez au paravant UnTagger le port du switch avec le vlan %s\n, puis inserer votre CD (LiveCD), redémarrer sur le CD, puis relancer le p2v" % self.hote_xen.vlan
        print "Assurez vous que : "
        print "   - Le port du switch soit bien UnTaggé avec le vlan %s" % self.hote_xen.vlan
        print "   - Le paquet 'dcfldd' soit installé sur le livecd"
        print "Votre LiveCD aura l'IP suivante : %s " % self.hote_xen.ip_physique
      sys.exit()

  def analyse_commande(self):
    parser = OptionParser(usage="%convert-p2v-xen -f <FQDN>  --projet=<PROJET> | [-v <VG_NAME>] | [--bridge=<Prefix_Bridge>] | [-k] |[-s <Num_Demande_Sysadmin>] | [-e] | [-p]", version="%prog 3.2.1")
    parser.add_option("-f","--fqdn", action="store", type="string", dest="vm_name",help="FDQN du serveur physique a virtualiser", metavar="FQDN" )
    parser.add_option("-t","--type", action="store", type="string", dest="type", default="PARA", help="Type de P2V (HVM ou PARA), default : PARA", metavar="TYPE")
    parser.add_option("-v","--vg", action="store", type="string", dest="vg_name",default="LVM_XEN",help="Nom du VG sur le serveur xen, defaut : LVM_XEN", metavar="VG")
    parser.add_option("-b","--bridge", action="store", type="string", dest="bridge_prefix",default="xenbr",help="Prefixe du bridge, defaut : xenbr", metavar="BRIDGE")
    parser.add_option("-r","--projet", action="store", type="string", dest="projet_name",help="Nom du projet P2V", metavar="PROJET")
    parser.add_option("-k","--keep-mac-addr", action="store_true", dest="keep_mac_addr", default = False ,help="conserve les adresses mac")
    parser.add_option("-l","--no-pxe", action="store_true", dest="no_pxe", default = False ,help="Desactive la serveur PXE, afin de passer par l'insertion d'un liveCD")
    parser.add_option("-s","--sysadmin", action="store", type="string", dest="dem_sysadmin",default="",help="Numero de demande sysadmin", metavar="Num DS")
    parser.add_option("-e","--eligibility", action="store_true", dest="eligibility",help="test d eligibilite, permettant de verifier si le serveur physique est eligible pour le P2V")
    parser.add_option("-p","--postinstall", action="store_true", dest="postinstall",help="rejoue la post installation (copie des modules, modification du fstab, etc..")
    parser.add_option("--pxe", action="store_true", dest="pxe",help="Permet de demarrer que le PXE")
    parser.set_defaults(PHY_NAME="1.1.1.2")

    (options, args) = parser.parse_args()
    if options.vm_name == None or options.projet_name == None:
      print "Option manquante\n"
      os.system("convert-p2v-xen --help")
      sys.exit()
    return (options, args)


def main():
  H = convert_p2v() 
  "Analyse des parametres de la ligne de commande"
  (options, args) = H.analyse_commande()
  H.VM_NAME = options.vm_name

  H.hote_xen = xen_host()
  H.pxe = pxe()
  H.hote_xen.vmnamecfengine = H.VM_NAME
  H.hote_xen.projet_p2v = options.projet_name
  H.hote_xen.bridge_prefix = options.bridge_prefix
  H.hote_xen.sysadmin = options.dem_sysadmin
  H.hote_xen.vgname = options.vg_name
  H.hote_xen.type_p2v = options.type
  H.hote_xen.keep_mac_addr = options.keep_mac_addr
  
  H.hote_xen.no_pxe = options.no_pxe
  
  H.hote_xen.get_info_cfp2v()
  H.hote_xen.build_cnx()

  if options.pxe == True:
    H.hote_xen.build_cnx()
    H.pxe = pxe()
    H.boot_pxe()
    sys.exit()

  print H.hote_xen.get_name_vm_dest(),H.hote_xen.type_p2v

  if options.eligibility == True:
    H.P2V_PHASE_ELIGIBILITY()
  else:
    if options.postinstall == True:
      if (H.hote_xen.is_created_lv(H.VM_NAME) == "1") and H.hote_xen.is_created_cfg(H.VM_NAME):
        H.P2V_PHASE_POSTINSTALL()
        print "POST INSTALL"
        sys.exit()
      else:
        print "%s n'est pas une VM, ou les fichiers /etc/xen/P2V/%s sont manquants" % (H.VM_NAME,H.VM_NAME)
        sys.exit()
    else:
      if H.hote_xen.is_created_cfg(H.VM_NAME):
        if H.hote_xen.is_finish_p2v(H.VM_NAME) == "false":
          H.P2V_PHASE_2()
        else:
          print "Le P2V a déjà été effectué"
          sys.exit()
      else:
        H.P2V_PHASE_1()



if __name__ == '__main__':
  main()
