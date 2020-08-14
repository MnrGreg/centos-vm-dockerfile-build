# Create block disk
IMG_SIZE=$(expr 2048 \* 1024 \* 1024)
dd if=/dev/zero of=/os/output/disk.img bs=${IMG_SIZE} count=1
sgdisk -n 0:0:+2M -t 0:ef02 -c 0:"boot" /os/output/disk.img
sgdisk -n 0:0:0 -t 0:8300 -c 0:"linux" /os/output/disk.img
# Mount partitions and create filesystems
losetup -v -fP --show /os/output/disk.img
mkfs.ext4 -L SLASH /dev/loop0p2
mkdir -p /os/mnt/
mount -t ext4 /dev/loop0p2 /os/mnt/
# Mount filesystem and copy Container Image
tar -xvf /os/output/linux.tar -C /os/mnt/
# Autoconfig the grub2.cfg
mount --bind /dev /os/mnt/dev
mount --bind /dev/pts /os/mnt/dev/pts
mount --bind /proc /os/mnt/proc  # check if reuired
mount --bind /sys /os/mnt/sys
mount --bind /run /os/mnt/run
# Set Grub2 defaults file
cat << EOF > /os/mnt/etc/default/grub
GRUB_TIMEOUT=5
GRUB_DISTRIBUTOR="$(sed 's, release .*$,,g' /etc/system-release)"
GRUB_DEFAULT=saved
GRUB_DISABLE_SUBMENU=true
GRUB_TERMINAL_OUTPUT="console"
GRUB_CMDLINE_LINUX="console=ttysS0 console=tty1 earlyprintk=ttyS0 elevator=noop"
GRUB_DISABLE_RECOVERY="true"
GRUB_DISABLE_LINUX_UUID=true
GRUB_ENABLE_LINUX_LABEL=true
GRUB_DEVICE=LABEL=SLASH
EOF
export uuid=$(blkid /dev/loop0p2 -sUUID -ovalue)
cat << 'EOF' | chroot /os/mnt/
rm -f /.dockerenv
echo "LABEL=SLASH  /       ext4  defaults   1   1" > /etc/fstab
grub2-install -v --no-floppy --target=i386-pc /dev/loop0
grub2-mkconfig -o /boot/grub2/grub.cfg
sed -i 's/linuxefi/linux/g' /boot/grub2/grub.cfg
sed -i 's/initrdefi/initrd/g' /boot/grub2/grub.cfg
chmod og-rwx /boot/grub2/grub.cfg
cat << EOT > /etc/dracut.conf
add_drivers+="vmxnet3 vmw_pvscsi vmw_vmci vmw_balloon vmwgfx mptspi mptscsih mptbase"
hostonly="no"
use_fstab="yes"
add_fstab+="/etc/fstab"
EOT
dracut -v -f /boot/initramfs-$(basename $(ls -dt /lib/modules/*)).img $(basename $(ls -dt /lib/modules/*))
EOF
umount /os/mnt/run
umount /os/mnt/sys
umount /os/mnt/proc
umount /os/mnt/dev/pts
umount /os/mnt/dev
umount /os/mnt
losetup -D