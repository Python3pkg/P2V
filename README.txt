


Outils permettant de convertir un serveur physique en serveur virtuel xen.

Actuellement l'outils ne converti que des serveurs ubuntu et debian.

Usage: %convert-p2v -f <FQDN>  [-i <IP>] | [-v <VG_NAME>] | [-s <Num_Demande_Sysadmin>] | [-e]

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -f FQDN, --fqdn=FQDN  FDQN du serveur physique a virtualiser
  -i IP, --ip=IP        IP de communication entre le xen0 et le serveur
                        physique, defaut: 1.1.1.2
  -v VG, --vg=VG        Nom du VG sur le serveur xen, defaut : LVM_XEN
  -s Num DS, --sysadmin=Num DS
                        Numero de demande sysadmin
  -e, --eligibility     test d eligibilite, permettant de verifier si le
                        serveur physique est eligible pour le P2V
  -p, --postinstall     rejoue la post installation (copie des modules,
                        modification du fstab, etc..

