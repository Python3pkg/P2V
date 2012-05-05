#!/usr/bin/python


#from dialog  import *

from p2v import xen_host
import os,sys,shutil

from optparse import OptionParser


def P2V_HVM_PHASE_1(PHYSICAL_NAME,VM_NAME):
  if PHYSICAL_NAME != VM_NAME:
    print "LE FQDN ne corresponds pas."
    sys.exit()

  print "#### PHASE 1/2 ####"
  hote_xen.get_info_srv_physique()
  print hote_xen.affiche_rapport()
  
  hote_xen.generation_fichier_p2v()
  print hote_xen.endphase()

def P2V_HVM_PHASE_2(VM):
  print "#### PHASE 2/2 ####"
  if hote_xen.is_livecd() == "true":
    hote_xen.import_all_variables(VM)
    hote_xen.exec_cmd_p2v() 
    hote_xen.post_install()
  else:
    print "Erreur !!! Il faut que le LiceCD Slax soit present"
    sys.exit()


def analyse_commande():
  parser = OptionParser(usage="%xenmgt-p2v-console.py -f <FQDN>  [-i <IP>] | [-v <Num_VLAN>]", version="%prog 1.0")
  parser.add_option("-f","--fqdn", action="store", type="string", dest="vm_name",help="FDQN du serveur physique a virtualiser", metavar="FQDN" )
  parser.add_option("-i", "--ip", action="store", type="string", dest="physique_name",default="1.1.1.2",help="IP de communication entre le xen0 et le serveur physique, defaut: 1.1.1.2", metavar="IP")
  parser.add_option("-v","--vlan", action="store", type="string", dest="vlan",help="VLAN Commun entre le xen et le serveur physique", metavar="Num VLAN")
  parser.set_defaults(PHY_NAME="1.1.1.2")

  (options, args) = parser.parse_args()
  if options.vm_name == None:
    print "Option manquante"
    sys.exit()
  return (options, args)


if __name__ == "__main__":

  "Analyse des parametres de la ligne de commande"
  (options, args) = analyse_commande()

  PHY_IP = options.physique_name
  VM_NAME = options.vm_name

  hote_xen = xen_host(ip_srv_phy=PHY_IP)

  #hote_xen.get_name_srv_source(PHY_IP)
  #PHYSICAL_NAME = hote_xen.get_name_vm_dest(PHY_IP)
  PHYSICAL_NAME = hote_xen.get_name_vm_dest()
  print PHYSICAL_NAME

  MENU_P2V = "PARA"

  if MENU_P2V == "PARA":
    hote_xen.type_p2v(MENU_P2V)
    if hote_xen.is_created_cfg(VM_NAME):
      P2V_HVM_PHASE_2(VM_NAME)
    else:
      P2V_HVM_PHASE_1(PHYSICAL_NAME,VM_NAME)
