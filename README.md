## Automating OS Virtual Machine Templates builds

### 1. Install Docker

### 2. Update the respective OS Dockfile as required (./centos7/Dockerfile)

### 3. Execute the respective OS builds:

#### CentOS OVF attributes
```
export IMAGE_OS=centos
export IMAGE_RELEASE=7.8.2003
export OVF_ID=107
export OVF_NAME="CentOS 7"
export OVF_VERSION="7"
export OVF_TYPE="centos7_64Guest"
sh ./vmbuild.sh
```

#### RHEL OVF attributes
```
export IMAGE_OS=rhel
export IMAGE_RELEASE=7.8-356
export OVF_ID=80
export OVF_NAME="RHEL 7"
export OVF_VERSION="7"
export OVF_TYPE="rhel7_64Guest"
sh ./vmbuild.sh
```

#### PHOTON OVF attributes
```
export IMAGE_OS=photon
export IMAGE_RELEASE=3.0-20201201
export OVF_ID=36
export OVF_NAME="VMware Photon OS 64-bit"
export OVF_VERSION="3"
export OVF_TYPE="vmwarePhoton64Guest"
sh ./vmbuild.sh
```

### 5. Booting images locally for testing [needs qemu & change -accel kvm/hvf as needed]:
```shell
qemu-system-x86_64 -accel hvf -m 1G -drive file=./$IMAGE_OS$OVF_VERSION/output/disk.img,index=0,media=disk,format=raw
```