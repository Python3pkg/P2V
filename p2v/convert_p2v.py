#!/usr/bin/env python

from p2v_xen_host import xen_host
import os,sys,shutil

from optparse import OptionParser

class convert_p2v(object):
  def __init__(self):
    pass

  def P2V_PHASE_POSTINSTALL(self):
    self.hote_xen.import_all_variables(self.VM_NAME)
    self.hote_xen.post_install()

  def P2V_PHASE_ELIGIBILITY(self):
    self.hote_xen.check_vgname()
    if self.PHYSICAL_NAME != self.VM_NAME:
      print "LE FQDN ne corresponds pas."
      sys.exit() 
 
    print "#### PHASE ELIGIBILITY ####"
    self.hote_xen.get_eligibility()
    self.hote_xen.rapport_eligibility()
    sys.exit()
  
  def P2V_PHASE_1(self):
    self.hote_xen.check_vgname()
    if self.PHYSICAL_NAME != self.VM_NAME:
      print "LE FQDN ne corresponds pas."
      sys.exit()

    print "#### PHASE 1/2 ####"
    self.hote_xen.get_info_srv_physique()
    print self.hote_xen.affiche_rapport()
  
    self.hote_xen.generation_fichier_p2v()
    print self.hote_xen.endphase()

  def P2V_PHASE_2(self):
    print "#### PHASE 2/2 ####"
    if self.hote_xen.is_livecd() == "true":
      self.hote_xen.import_all_variables(self.VM_NAME)
      self.hote_xen.exec_cmd_p2v() 
      self.hote_xen.post_install()
    else:
      print "Erreur !!! Il faut que le LiceCD Slax soit present"
      sys.exit()


  def analyse_commande(self):
    parser = OptionParser(usage="%convert-p2v-xen -f <FQDN>  [-i <IP>] | [-v <VG_NAME>] | [-s <Num_Demande_Sysadmin>] | [-e]", version="%prog 2.2.8")
    parser.add_option("-f","--fqdn", action="store", type="string", dest="vm_name",help="FDQN du serveur physique a virtualiser", metavar="FQDN" )
    parser.add_option("-i", "--ip", action="store", type="string", dest="physique_name",default="1.1.1.2",help="IP de communication entre le xen0 et le serveur physique, defaut: 1.1.1.2", metavar="IP")
    parser.add_option("-v","--vg", action="store", type="string", dest="vg_name",default="LVM_XEN",help="Nom du VG sur le serveur xen, defaut : LVM_XEN", metavar="VG")
    parser.add_option("-s","--sysadmin", action="store", type="string", dest="dem_sysadmin",default="",help="Numero de demande sysadmin", metavar="Num DS")
    parser.add_option("-e","--eligibility", action="store_true", dest="eligibility",help="test d eligibilite, permettant de verifier si le serveur physique est eligible pour le P2V")
    parser.add_option("-p","--postinstall", action="store_true", dest="postinstall",help="rejoue la post installation (copie des modules, modification du fstab, etc..")
    parser.set_defaults(PHY_NAME="1.1.1.2")

    (options, args) = parser.parse_args()
    if options.vm_name == None:
      print "Option manquante\n"
      os.system("convert-p2v-xen --help")
      sys.exit()
    return (options, args)


def main():
  H = convert_p2v() 
  "Analyse des parametres de la ligne de commande"
  (options, args) = H.analyse_commande()
  H.POSTINSTALL = options.postinstall
  H.ELIGIBILITY = options.eligibility
  H.PHY_IP = options.physique_name
  H.VM_NAME = options.vm_name
  H.DS_SYSADMIN = options.dem_sysadmin
  H.VG_NAME = options.vg_name

  H.hote_xen = xen_host(ip_srv_phy=H.PHY_IP,ds=H.DS_SYSADMIN,vg_name=H.VG_NAME)

  H.PHYSICAL_NAME = H.hote_xen.get_name_vm_dest()
  print H.PHYSICAL_NAME

  if H.ELIGIBILITY == True:
    H.P2V_PHASE_ELIGIBILITY()
  else:
    if H.POSTINSTALL == True:
      if (H.hote_xen.is_created_lv(H.VM_NAME) == "1") and H.hote_xen.is_created_cfg(H.VM_NAME):
        H.P2V_PHASE_POSTINSTALL()
        print "POST INSTALL"
        sys.exit()
      else:
        print "%s n est pas une VM, ou les fichiers /etc/xen/P2V/%s sont manquants" % (H.VM_NAME,H.VM_NAME)
        sys.exit()
    else:
      if H.hote_xen.is_created_cfg(H.VM_NAME):
        H.P2V_PHASE_2()
      else:
        H.P2V_PHASE_1()



if __name__ == '__main__':
  main()
