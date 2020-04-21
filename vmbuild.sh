
# Clean prevous builds
rm -fr ./output && mkdir ./output
# Docker Build OS Image
docker build -t centos-vm:7 .
docker container rm centos-vm 
docker create --name=centos-vm centos-vm:7
docker export centos-vm -o ./output/linux.tar

# Jump into linux shell to create block device and enable boot
docker run -it -v `pwd`:/os:rw --cap-add SYS_ADMIN --privileged -v /dev:/dev \
  centos:7 sh -c 'yum -y install e2fsprogs gdisk && /os/scripts/create_disk_image.sh'

## Convert VM to VMDK OVA
mv ./output/disk.img ./output/CentOS-7-x86_64-Minimal-1908.img
cat <<EOF > ./output/packer-manifest.json
{
  "builds": [
    {
      "name": "CentOS-7-x86_64-Minimal-1908",
      "artifact_id": "VM",
      "files": [
        {
          "name": "CentOS-7-x86_64-Minimal-1908.img",
          "size": 4194296
        }
      ],
      "custom_data": {
        "build_date": "2020-04-13T04:05:53Z",
        "build_timestamp": "1586750752",
        "iso_checksum": "9a2c47d97b9975452f7d582264e9fc16d108ed8252ac6816239a3b58cef5c53d",
        "iso_checksum_type": "sha256",
        "iso_url": "http://sjc.edge.kernel.org/centos/7.7.1908/isos/x86_64/CentOS-7-x86_64-Minimal-1908.iso",
        "os_id": "107",
        "os_name": "CentOS 7",
        "os_version": "7",
        "os_type": "centos7_64Guest"
      }
    }
  ]
}
EOF
docker run -it -v `pwd`:/os:rw  \
  centos:7 sh -c 'yum -y install qemu-img && python /os/scripts/image-build-ova.py --vmx 13 /os/output/'

