#!/usr/bin/python


import os,re
from operator import itemgetter
import shutil
from  p2v_physical_host import physical_host
from sshtools import Ssh


class xen_host:
 
  def __init__(self,ip_srv_phy="",xenmgtconf=""):
    xenmgtconf={}
    template_hvm={}
    execfile("/etc/xen/xenmgt-p2v.conf",xenmgtconf)
    execfile(xenmgtconf["TEMPLATE_HVM"],template_hvm)
    self.xenmgtconf = xenmgtconf
    self.template_hvm = template_hvm
    self.bs=self.xenmgtconf["DD_BS"]
    self.P = physical_host(ip_srv_phy)
    self.ip_srv_phy = ip_srv_phy
    self.ssh = Ssh(self.ip_srv_phy)

  def exec_cmd(self,cmd=''):
    CMD = os.popen(cmd,"r")
    ret = CMD.readlines()
    return ret

  def type_p2v(self,type):
    self.type_p2v = type
  
  def get_os_version(self):
    self.version_os = self.P.get_version_os()
    return self.version_os

  def get_vgname(self):
    liste = self.exec_cmd('vgdisplay | grep Name')
    for i in liste:
      vgname = i.split()[-1].strip()
    self.vgname = vgname

  def get_name_vm_dest(self):
    self.ssh.del_keyfile()
    self.ssh.copy_id()
    #self.exec_cmd("ssh-copy-id %s" % self.ip_srv_phy)
    #name_vm_dest = self.exec_cmd("ssh root@%s hostname" % self.ip_srv_phy)
    name_vm_dest = self.ssh.exec_cmd("hostname")
    self.name_vm_dest = name_vm_dest[0].strip()
    self.new_name_vm_ip = self.ip_srv_phy
    return self.name_vm_dest
    
  #def get_name_srv_source(self,name_srv_source):
  #  self.name_srv_source = name_srv_source

  def get_interfaces(self):
    self.interfaces = self.P.get_interfaces()

  def get_memory(self):
    self.memory = self.P.get_memory1()

  def get_partitions(self):
    self.partitions = self.P.get_all_partitions()
  
  def get_cpu(self):
    self.cpu = self.P.get_cpu()

  def get_info_srv_physique(self):
    self.get_os_version()
    self.get_memory()
    self.get_interfaces()
    self.get_partitions()
    self.get_cpu()

  def is_livecd(self):
    self.is_livecd = self.P.is_livecd()
    return self.is_livecd




  #######################################################  
  ### DEBUT PREPARATION POUR LA GENERATION DU RAPPORT ###
  #######################################################
      
  def prep_affiche_os_version(self):
    AFFICHE_OS_VERSION = "OS : %s %s\n\n" % (self.version_os[0],self.version_os[1]) 
    return AFFICHE_OS_VERSION
  
  def prep_affiche_vm_name(self):
    AFFICHE_VM_NAME = "VM : %s\n" % self.name_vm_dest
    AFFICHE_VM_NAME += "IP LiveCD : %s\n\n" % self.new_name_vm_ip
    return AFFICHE_VM_NAME

  def prep_affiche_memory(self):
    AFFICHE_MEMORY = "MEMORY : %s Mo\n" % self.memory
    return AFFICHE_MEMORY

  def prep_affiche_cpu(self):
    AFFICHE_CPU = "CPU : %s \n\n" % self.cpu
    return AFFICHE_CPU

  def prep_affiche_network(self):
    AFFICHE_NETWORK = "NETWORK :   \n"
    for i in self.tri(self.interfaces):
      AFFICHE_NETWORK += " %s -> Mac address : %s\n" % (i,self.interfaces[i])
    AFFICHE_NETWORK += "\n"
    return AFFICHE_NETWORK

  def prep_affiche_partitions(self):
    AFFICHE_PARTITIONS = "PARTITIONS :\n"
    for i in self.tri(self.partitions[self.type_p2v]):
      if self.type_p2v == "HVM":
        AFFICHE_PARTITIONS += " %s -> taille : %s\n" % (self.partitions[self.type_p2v][i][0],self.partitions[self.type_p2v][i][1])
      if self.type_p2v == "PARA":
        AFFICHE_PARTITIONS += " %s %s %s %s\n" % (self.partitions[self.type_p2v][i][0],self.partitions[self.type_p2v][i][1], self.partitions[self.type_p2v][i][2],self.partitions[self.type_p2v][i][3])
    return AFFICHE_PARTITIONS

  def prep_cmd_create_partitions(self):
    self.get_vgname()
    AFFICHE_CREATE_LV = "\n"
    for i in self.tri(self.partitions[self.type_p2v]):
      if self.type_p2v == "HVM":
        nom_partition = i.replace('/','-')
        AFFICHE_CREATE_LV += "lvcreate -L %sB -n %s-%s %s\n" % (self.partitions[self.type_p2v][i][1],self.partitions[self.type_p2v][i][0],self.name_vm_dest,self.vgname)
      if self.type_p2v == "PARA":
        if self.partitions[self.type_p2v][i][3] == "/":
          nom_part = "root"
        elif self.partitions[self.type_p2v][i][1] == "swap":
          nom_part = "swap"
        else:
          nom_part = self.partitions[self.type_p2v][i][3].replace("/","-")[1:]
        AFFICHE_CREATE_LV += "lvcreate -L %sB -n %s-%s %s\n" % (self.partitions[self.type_p2v][i][2],nom_part,self.name_vm_dest,self.vgname)
    return AFFICHE_CREATE_LV

  def prep_cmd_copy_dd(self):
    AFFICHE_DD = "\n"
    for i in self.tri(self.partitions[self.type_p2v]):
      if self.type_p2v == "HVM":
        AFFICHE_DD += "ssh -c arcfour root@"+ self.new_name_vm_ip +" 'dcfldd status=on sizeprobe=if statusinterval=100 if=/dev/"+ i +"' bs="+ self.bs +" | dd of=/dev/"+ self.vgname +"/"+ self.partitions[self.type_p2v][i][0] +"-"+self.name_vm_dest+" bs="+ self.bs +"\n"
      if self.type_p2v == "PARA":
        if self.partitions[self.type_p2v][i][3] == "/":
          nom_part = "root"
        elif self.partitions[self.type_p2v][i][1] == "swap":
          nom_part = "swap"
        else:
          nom_part = self.partitions[self.type_p2v][i][3].replace("/","-")[1:]
        AFFICHE_DD += "echo \"Copie de la partition "+ self.partitions[self.type_p2v][i][3] +"\"\n"
        if self.partitions[self.type_p2v][i][3] == "swap":
          AFFICHE_DD += "mkswap -v1 /dev/"+ self.vgname +"/"+ nom_part +"-"+self.name_vm_dest+"\n"
        else:
          ############# DETECTION POUR REDUCTION LV ET RESIZE FS ##################
          if self.P.is_lv(self.partitions[self.type_p2v][i][0]):
            if self.partitions[self.type_p2v][i][0] > 10000000:
              if self.P.taux_occupation(self.partitions[self.type_p2v][i][0],self.partitions[self.type_p2v][i][1]) < 20:
                print "Elu pour la reduction"
                print "%s is LVM LV" % self.partitions[self.type_p2v][i][0]
                print self.P.taux_occupation(self.partitions[self.type_p2v][i][0],self.partitions[self.type_p2v][i][1])
          ############# FIN DETECTION POUR REDUCTION LV ET RESIZE FS ##################
          AFFICHE_DD += "ssh -c arcfour root@"+ self.new_name_vm_ip +" 'dcfldd status=on sizeprobe=if statusinterval=100 if="+ self.partitions[self.type_p2v][i][0] +"' bs="+ self.bs +" | dd of=/dev/"+ self.vgname +"/"+ nom_part +"-"+self.name_vm_dest+" bs="+ self.bs +"\n"
    return AFFICHE_DD

  def prep_cmd_ssh_key(self):
    AFFICHE_SSH = "\n"
    AFFICHE_SSH += "echo \"Password pour transfert de clefs ssh\"\n"
    AFFICHE_SSH += "ssh-keygen -R "+ self.new_name_vm_ip +"\n"
    AFFICHE_SSH += "ssh-copy-id "+ self.new_name_vm_ip +""
    return AFFICHE_SSH

  def affiche_rapport(self):
    affiche = "---------- RAPPORT ----------\n"
    affiche += self.prep_affiche_os_version()
    affiche += self.prep_affiche_vm_name()
    affiche += self.prep_affiche_memory()
    affiche += self.prep_affiche_cpu()
    affiche += self.prep_affiche_network()
    affiche += self.prep_affiche_partitions()
    return affiche

  #####################################################  
  ### FIN PREPARATION POUR LA GENERATION DU RAPPORT ###
  #####################################################


  def get_exec_cmd(self):
    ecrit_cmd = ""
    ecrit_cmd += self.prep_cmd_ssh_key()
    ecrit_cmd += self.prep_cmd_create_partitions()
    ecrit_cmd += self.prep_cmd_copy_dd()
    return ecrit_cmd



  #############################################################  
  ### DEBUT GENERATION DU FICHIER DE CONF XEN (HVM OU PARA) ###
  #############################################################

  def generate_conf_xen(self):
    if self.type_p2v == "HVM":
      GEN_CONF = self.generate_conf_xen_hvm()
    if self.type_p2v == "PARA":
      GEN_CONF = self.generate_conf_xen_para()
    return GEN_CONF

  def ecrit_conf_partitions(self):
    conf="["
    count = len(self.partitions[self.type_p2v].keys())
    cpt=1
    for i in self.tri(self.partitions[self.type_p2v]):
      if self.type_p2v == "HVM":
        conf += "'phy:/dev/%s/%s-%s,%s,w'" % (self.vgname,self.partitions[self.type_p2v][i][0],self.name_vm_dest,self.partitions[self.type_p2v][i][0])
      if self.type_p2v == "PARA":
        if self.partitions[self.type_p2v][i][3] == "/":
          nom_part = "root"
        elif self.partitions[self.type_p2v][i][1] == "swap":
          nom_part = "swap"
        else:
          nom_part = self.partitions[self.type_p2v][i][3].replace("/","-")[1:]
        conf += "'phy:/dev/%s/%s-%s,%s,w'" % (self.vgname,nom_part,self.name_vm_dest,i)
      if cpt != int(count):
        conf += ",\n\t"
      cpt = (int(cpt) + 1)
    conf += "]"
    return conf

  def ecrit_conf_interfaces(self):
    conf="["
    count = len(self.interfaces.keys())
    cpt=1
    for i in self.tri(self.interfaces):
      conf += "'mac=%s , bridge=xenbr2006'" % self.interfaces[i]
      if cpt != int(count):
        conf += ","
      cpt = (int(cpt) + 1)
    conf += "]"
    return conf


  def uuid_gen(self):
    uuid_gen = self.exec_cmd('uuidgen')
    return uuid_gen[0].strip()

  def generate_conf_xen_hvm(self):
    self.ecrit_conf_partitions()
    CONF_HVM = ""
    for i in self.template_hvm.keys():
      if i != "__builtins__":
        if i == "vif":
          CONF_HVM += ""+str(i)+" = "+ self.ecrit_conf_interfaces() +"\n"
        elif i == "disk":
          CONF_HVM += ""+str(i)+" = "+ self.ecrit_conf_partitions() +"\n"
        elif i == "uuid":
          CONF_HVM += ""+str(i)+" = \""+ self.uuid_gen() +"\"\n"
        elif i == "name":
          CONF_HVM += ""+str(i)+" = \""+ self.name_vm_dest +"\"\n"
        else:
          CONF_HVM += ""+str(i)+" = '"+ str(self.template_hvm[i]) +"'\n"
    return CONF_HVM

  def ecrit_memory(self):
    return self.memory

  def ecrit_maxmem(self):
    if self.memory < 4096:
      maxmem = 6144
    elif self.memory > 4096:
      maxmem = ((int(self.memory) / 2) + 8192)
    return maxmem

  def ecrit_vcpus(self):
    vcpus = "12"
    return vcpus

  def ecrit_vcpu_avail(self):
    if self.cpu == "1":
      vcpu_avail = "3"
    elif self.cpu == "2":
      vcpu_avail = "3"
    elif self.cpu == "3":
      vcpu_avail = "7"
    elif self.cpu == "4":
      vcpu_avail = "15"
    elif self.cpu == "5":
      vcpu_avail = "31"
    elif self.cpu == "6":
      vcpu_avail = "63"
    elif self.cpu == "7":
      vcpu_avail = "127"
    elif self.cpu == "8":
      vcpu_avail = "255"
    return vcpu_avail

  def ecrit_name_vm_dest(self):
    return self.name_vm_dest

  def ecrit_extra(self):
    extra = "console=xvc0 elevator=noop"
    return extra

  def ecrit_root_kernel(self):
   root=""
   for i in self.tri(self.partitions[self.type_p2v]):
     if self.partitions[self.type_p2v][i][3] == "/":
       root = i
   root_kernel = "/dev/%s ro" % root 
   return root_kernel

  def get_kernel(self):
    self.kernel_vm=[]
    if self.version_os[0] == "Ubuntu":
      kernel = self.xenmgtconf["KERNEL_UBUNTU"]
      initrd = self.xenmgtconf["INITRD_UBUNTU"]
    elif self.version_os[0] == "Debian":
      kernel = self.xenmgtconf["KERNEL_DEBIAN"]
      initrd = self.xenmgtconf["INITRD_DEBIAN"]
    else:
      kernel = self.xenmgtconf["KERNEL_CENTOS"]
      initrd = self.xenmgtconf["INITRD_CENTOS"]
    self.kernel_vm = [kernel,initrd]
    return self.kernel_vm

  def generate_conf_xen_para(self):
    self.get_kernel()
    CONF_PARA = ""
    CONF_PARA += "kernel = \""+ self.kernel_vm[0] +"\"\n"
    CONF_PARA += "ramdisk = \""+ self.kernel_vm[1] +"\"\n"
    CONF_PARA += "memory = "+ str(self.ecrit_memory()) +"\n"
    CONF_PARA += "maxmem = "+ str(self.ecrit_maxmem()) +"\n\n"
    CONF_PARA += "vcpus = "+ self.ecrit_vcpus() +"\n"
    CONF_PARA += "vcpu_avail = "+ self.ecrit_vcpu_avail() +"\n\n"
    CONF_PARA += "name = \""+ self.ecrit_name_vm_dest() +"\"\n\n"
    CONF_PARA += "vif = "+ self.ecrit_conf_interfaces() +"\n"
    CONF_PARA += "disk = "+ self.ecrit_conf_partitions() +"\n"
    CONF_PARA += "root = \""+ self.ecrit_root_kernel() +"\"\n"
    CONF_PARA += "extra = \""+ self.ecrit_extra() +"\"\n"
    return CONF_PARA


  ###########################################################  
  ### FIN GENERATION DU FICHIER DE CONF XEN (HVM OU PARA) ###
  ###########################################################

  def create_rep_p2v(self):
    if not os.path.isdir(self.rep_p2v):
      self.exec_cmd("mkdir -p %s" % self.rep_p2v)

  def check_rep_p2v(self):
    self.rep_p2v = "/etc/xen/P2V/"+ self.name_vm_dest +""
    self.create_rep_p2v()

  def set_fichier_p2v(self,ext="",contenu=""):
    fichier = "%s/%s.%s" % (self.rep_p2v,self.name_vm_dest,ext)
    fd = open(fichier,"w")
    fd.write(contenu)
    fd.close()

  def generation_fichier_p2v(self):
    self.check_rep_p2v()
    self.set_fichier_p2v("sh",self.get_exec_cmd())
    self.set_fichier_p2v("cfg",self.generate_conf_xen())
    self.set_fichier_p2v("var",self.export_variables())



  def endphase(self):
    AFFICHE = "\n\n"
    AFFICHE += "*****************************************************************\n"
    AFFICHE += "FIN de L'ETAPE 1/2\n\n"
    AFFICHE += "Pour passer a la 2eme Etape, il faut inserer\n"
    AFFICHE += "le LiveCD SLAX, rebooter, puis configurer le reseau de celui-ci\n\n"
    AFFICHE += "Commande pour activer le reseau :\n"
    AFFICHE += "# vconfig add eth0 <NUM_VLAN>\n"
    AFFICHE += "# ip addr add %s/<MASK> dev eth0.<NUM_VLAN>\n" % self.new_name_vm_ip
    AFFICHE += "*****************************************************************\n"
    return AFFICHE


  ##############################
  ###   DEBUT POST INSTALL   ###
  ##############################

  def export_variables(self):
    export_variable = ""
    export_variable += "partitions=%s\n" % self.partitions
    export_variable += "vgname=\"%s\"\n" % self.vgname
    export_variable += "type_p2v=\"%s\"\n" % self.type_p2v
    export_variable += "name_vm_dest=\"%s\"\n" % self.name_vm_dest
    export_variable += "version_os=%s\n" % self.version_os
    return export_variable

  def import_all_variables(self,VM):
    new_val={}
    execfile("/etc/xen/P2V/"+ VM +"/"+ VM +".var",new_val)
    self.new_variables=new_val
    for i in self.new_variables.keys():
      if i != "__builtins__":
        globals()[i] = self.new_variables[i]
     
 
  def mkdir_rep_vhosts_vm(self):
    """ Creation du repertoire /vhosts/vm
    """
    print "Creation du repertoire /vhosts/%s" % name_vm_dest
    self.rep_vhosts_vm = "/vhosts/"+ name_vm_dest +""
    self.exec_cmd("mkdir -p %s" % self.rep_vhosts_vm)
    #os.makedirs(self.rep_vhosts_vm)

  def modif_fstab(self):
    """ Genere le nouveau fichier fstab
    """
    print "preparation du fichier fstab"
    self.exec_cmd("cp %s/etc/fstab %s/etc/fstab.pre.p2v" % (self.rep_vhosts_vm,self.rep_vhosts_vm))
    line = open("/vhosts/"+ name_vm_dest +"/etc/fstab.pre.p2v","r").read()
    for i in self.tri(partitions[type_p2v]):
        line = line.replace(partitions[type_p2v][i][0],"/dev/%s" % i,1)
    fichier = open("/vhosts/"+ name_vm_dest +"/etc/fstab","w")
    fichier.write(line)
    fichier.close()

  def modif_network(self):
    """ Genere le nouveau fichier network (En cours)
    """
    print "preparation du fichier network interfaces"
    if version_os[0] == "CentOS":
      self.exec_cmd("cp %s/etc/sysconfig/network_scripts/ifcfg-eth0 %s/etc/sysconfig/network_scripts/ifcfg-eth0.pre.p2v" % (self.rep_vhosts_vm,self.rep_vhosts_vm))
    else:
      self.exec_cmd("cp %s/etc/network/interfaces %s/etc/network/interfaces.pre.p2v" % (self.rep_vhosts_vm,self.rep_vhosts_vm))

  def copie_modules(self):
    """ copie du module 2.6.37 ou 2.6.18.149
    """
    print "copie du module necessaire"
    if version_os[0] == "Ubuntu":
      self.exec_cmd("cp -rpdf /lib/modules/2.6.37* %s/lib/modules/" % self.rep_vhosts_vm)
    if version_os[0] == "Debian":
      self.exec_cmd("cp -rpdf /lib/modules/2.6.18-149* %s/lib/modules/" % self.rep_vhosts_vm)
    if version_os[0] == "CentOS":
      self.exec_cmd("cp -rpdf /lib/modules/2.6.18-149* %s/lib/modules/" % self.rep_vhosts_vm)

  def set_ntp_sysctl(self):
    """ Modifie le sysctl pour la correction du ntp
    """
    print "Modification du sysctl"
    self.exec_cmd("echo \"xen.independent_wallclock = 1\" >> %s/etc/sysctl.conf" % self.rep_vhosts_vm)
 
  def mount_root_vm(self):
    """ Monte la partition root de la VM afin d'effectuer la post_install
    """
    print "montage de la partition root de %s" % name_vm_dest
    self.exec_cmd("mount /dev/%s/root-%s %s" % (vgname, name_vm_dest, self.rep_vhosts_vm))

  def umount_root_vm(self):
    """ Monte la partition root de la VM afin d'effectuer la post_install
    """
    print "demontage de la partition root de %s" % name_vm_dest
    self.exec_cmd("umount %s" % self.rep_vhosts_vm)

  def set_console_xen(self):
    """ Configuration de la console xen pour la VM
    """
    print ""
    self.exec_cmd("echo \"xvc0\" >> %s/etc/securetty" % self.rep_vhosts_vm) 
    if os.path.isfile("%s/etc/inittab" % self.rep_vhosts_vm):
      self.exec_cmd("echo \"7:2345:respawn:/sbin/getty 38400 xvc0\" >> %s/etc/inittab" % self.rep_vhosts_vm) 

    if os.path.isfile("%s/etc/event.d/tty1" % self.rep_vhosts_vm):
      self.exec_cmd("cp %s/etc/event.d/tty1 %s/etc/event.d/xvc0" % (self.rep_vhosts_vm,self.rep_vhosts_vm))
      self.exec_cmd("sed -i \"s@tty1@xvc0@\" %s/etc/event.d/xvc0" % self.rep_vhosts_vm)
    
    if os.path.isfile("%s/etc/init/tty1.conf" % self.rep_vhosts_vm):
      self.exec_cmd("cp %s/etc/init/tty1.conf %s/etc/init/xvc0.conf" % (self.rep_vhosts_vm,self.rep_vhosts_vm))
      self.exec_cmd("sed -i \"s@tty1@xvc0@\" %s/etc/init/xvc0.conf" % self.rep_vhosts_vm)

  def set_modprobe(self):
    """ active le modules xennet pour les interfaces reseaux
    """
    if version_os[0] == "Debian":
      self.exec_cmd("echo \"alias eth0 xennet\" >> %s/etc/modprobe.d/aliases" % self.rep_vhosts_vm)
    else: 
      self.exec_cmd("echo \"alias eth0 xennet\" >> %s/etc/modprobe.d/aliases.conf" % self.rep_vhosts_vm)

  def copy_conf_to_xen(self):
    shutil.copy("/etc/xen/P2V/"+ name_vm_dest +"/"+ name_vm_dest +".cfg","/etc/xen/vm/"+ name_vm_dest +"")

  def post_install(self):
    self.copy_conf_to_xen()
    self.mkdir_rep_vhosts_vm()
    self.mount_root_vm()
    self.copie_modules()
    self.modif_fstab()
    self.modif_network()
    self.set_ntp_sysctl()
    self.set_console_xen()
    self.set_modprobe()
    self.umount_root_vm()
    self.auto_vm()

    
  ############################
  ###   FIN POST INSTALL   ###
  ############################


  def tri(self, dico):
    """ Permet de tirer un dictionnaire
    """
    return sorted(dico.keys(), key=str) 

  def copy_dd_bs(self,bs=''):
    self.bs = bs

  def check_vg_size(self,percent='10'):
    size_total=()
    size_dispo=()

  def auto_vm(self):
    self.exec_cmd("cd /etc/xen/auto ; ln -s /etc/xen/vm/"+ name_vm_dest +"")

  def exec_cmd_p2v(self):
    os.system("/bin/bash /etc/xen/P2V/"+ name_vm_dest +"/"+ name_vm_dest +".sh")

  def is_created_cfg(self,vm):
    return os.path.isfile("/etc/xen/P2V/"+ vm +"/"+ vm +".cfg")

