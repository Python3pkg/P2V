#!/usr/bin/python

from p2v_xen_host import xen_host
import os,sys,shutil

from optparse import OptionParser


def P2V_HVM_PHASE_1(PHYSICAL_NAME,VM_NAME):
  hote_xen.check_vgname()
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
  parser = OptionParser(usage="%convert-p2v.py -f <FQDN>  [-i <IP>] | [-v <VG_NAME>] | [-c <Num_Demande_Sysadmin>]", version="%prog 1.0")
  parser.add_option("-f","--fqdn", action="store", type="string", dest="vm_name",help="FDQN du serveur physique a virtualiser", metavar="FQDN" )
  parser.add_option("-i", "--ip", action="store", type="string", dest="physique_name",default="1.1.1.2",help="IP de communication entre le xen0 et le serveur physique, defaut: 1.1.1.2", metavar="IP")
  #parser.add_option("-v","--vlan", action="store", type="string", dest="vlan",help="VLAN Commun entre le xen et le serveur physique", metavar="Num VLAN")
  parser.add_option("-v","--vg", action="store", type="string", dest="vg_name",default="LVM_XEN",help="Nom du VG sur le serveur xen, defaut : LVM_XEN", metavar="VG")
  parser.add_option("-s","--sysadmin", action="store", type="string", dest="dem_sysadmin",default="",help="Numero de demande sysadmin", metavar="Num DS")
  parser.add_option("-e","--eligibility", action="store", type="string", dest="eligibility",default="",help="test d'eligibilité, permettant de verifier si le serveur physique est eligible pour le P2V", metavar="Eligibility")
  parser.set_defaults(PHY_NAME="1.1.1.2")

  (options, args) = parser.parse_args()
  if options.vm_name == None:
    print "Option manquante\n"
    os.system("./convert-p2v.py --help")
    sys.exit()
  return (options, args)


if __name__ == "__main__":

  "Analyse des parametres de la ligne de commande"
  (options, args) = analyse_commande()

  PHY_IP = options.physique_name
  VM_NAME = options.vm_name
  DS_SYSADMIN = options.dem_sysadmin
  VG_NAME = options.vg_name

  hote_xen = xen_host(ip_srv_phy=PHY_IP,ds=DS_SYSADMIN,vg_name=VG_NAME)

  PHYSICAL_NAME = hote_xen.get_name_vm_dest()
  print PHYSICAL_NAME

  if hote_xen.is_created_cfg(VM_NAME):
    P2V_HVM_PHASE_2(VM_NAME)
  else:
    P2V_HVM_PHASE_1(PHYSICAL_NAME,VM_NAME)
