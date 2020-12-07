# Clean prevous builds
rm -fr ./$IMAGE_OS$OVF_VERSION/output; rm -fr ./$IMAGE_OS$OVF_VERSION/mnt; docker container rm vmimage; docker image rm vmimage:latest; mkdir ./$IMAGE_OS$OVF_VERSION/output
# Docker Build OS Image
docker build -t vmimage:latest ./$IMAGE_OS$OVF_VERSION/
docker create --name=vmimage vmimage:latest
docker export vmimage -o ./$IMAGE_OS$OVF_VERSION/output/linux.tar

# Jump into linux shell to create block device and enable boot
docker run -it -v `pwd`/$IMAGE_OS$OVF_VERSION:/os:rw --cap-add SYS_ADMIN --privileged -v /dev:/dev \
  $IMAGE_OS:$IMAGE_RELEASE sh -c '/os/create_disk_image.sh'

## Convert VM to VMDK OVA
docker run -it -v `pwd`:/os:rw  \
  -e IMAGE_OS=$IMAGE_OS \
  -e IMAGE_RELEASE=$IMAGE_RELEASE \
  -e OVF_ID=$OVF_ID \
  -e OVF_NAME="$OVF_NAME" \
  -e OVF_VERSION=$OVF_VERSION \
  -e OVF_TYPE=$OVF_TYPE \
  -e VMX=14 \
  $IMAGE_OS:$IMAGE_RELEASE  sh -c 'yum -y install qemu-img python3 && python3 /os/img-to-ova.py'
