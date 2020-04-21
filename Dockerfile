FROM centos:7.7.1908
RUN yum -y update
RUN echo "exclude=iwl* alsa-* ivtv-* aic94xx-firmware*" >> /etc/yum.conf
RUN yum -y group install "Minimal Install"

## Add filesystems packages
RUN yum -y install \
    grub2 \
    grub2-tools \
    e2fsprogs

## Add Hypervisor drivers
RUN yum -y install open-vm-tools

## Add cloud-init dependancies
RUN yum -y install \
    cloud-init \
    cloud-utils-growpart \
    gdisk \
    python-configobj \
    python-oauthlib \
    python-six \
    PyYAML \
    python-jsonpatch \
    python-jinja2 \
    python-jsonschema \
    python-requests \
    perl

# SysPrep Image
RUN systemctl disable firewalld && systemctl disable postfix
RUN sed -i 's/SELINUX=enforcing/SELINUX=permissive/g' /etc/selinux/config
RUN echo "root:pleasechangeme" | chpasswd
RUN yum clean all && \
    rm -rf /var/cache/yum/* /tmp/* /var/tmp/* /anaconda-post.log && \
    cat /dev/null > /etc/machine-id && \
    cat /dev/null > /var/log/audit/audit.log && \
    cat /dev/null > /var/log/wtmp && \
    cat /dev/null > /var/log/lastlog && \
    history -w && \
    history -c