FROM centos:7.8.2003

#RUN rm -rf /etc/yum.repos.d/*.repo
ADD ./yumrepos/*.repo /etc/yum.repos.d/

## Update packages and install kernel
RUN yum -y update
RUN echo "exclude=iwl* alsa-* ivtv-* aic94xx-firmware*" >> /etc/yum.conf
RUN yum -y group install "Minimal Install" && yum -y install kernel

## Add filesystems packages
RUN yum -y install \
    grub2 \
    grub2-tools \
    e2fsprogs

## Add Hypervisor drivers
RUN yum -y install open-vm-tools

## Add cloud-init dependancies
RUN yum -y install \
    cloud-utils-growpart \
    gdisk \
    cloud-init

# SysPrep Image
RUN systemctl disable firewalld && systemctl disable postfix && systemctl disable remote-fs.target
RUN sed -i 's/SELINUX=enforcing/SELINUX=permissive/g' /etc/selinux/config
RUN echo "root:plschangeme" | chpasswd
RUN yum clean all && \
    rm -rf /var/cache/yum/* /tmp/* /var/tmp/* /anaconda-post.log && \
    cat /dev/null > /etc/machine-id && \
    cat /dev/null > /var/log/audit/audit.log && \
    cat /dev/null > /var/log/wtmp && \
    cat /dev/null > /var/log/lastlog && \
    history -w && \
    history -c
