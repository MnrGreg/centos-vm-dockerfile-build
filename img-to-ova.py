#!/usr/bin/python

################################################################################
# usage: image-build-ova.py [FLAGS] ARGS
#  This program builds an OVA file from a VMDK and manifest file generated as a
#  result of a Packer build.
################################################################################

import argparse
import hashlib
import json
import os
import subprocess
from string import Template
import tarfile
import time
import datetime

def main():
    build_name = os.environ['IMAGE_OS']

    # Change the working directory if one is specified.
    os.chdir("/os/" + build_name + "/output")

    # Create stream-optimized versions of the VMDK files.
    stream_optimize_vmdk_files('disk.img')

    # Create the OVF file.
    ovf = "%s.ovf" % build_name
    create_ovf(ovf, {
        'BUILD_NAME': build_name,
        'BUILD_DATE': str(datetime.datetime.now()),
        'BUILD_TIMESTAMP': str(int(time.time())),
        'OS_NAME': os.environ['OVF_NAME'],
        'OS_TYPE': os.environ['OVF_TYPE'],
        'OS_ID': os.environ['OVF_ID'],
        'OS_VERSION': os.environ['OVF_VERSION'],
        'OS_RELEASE': os.environ['IMAGE_RELEASE'],
        'POPULATED_DISK_SIZE': os.path.getsize('disk.img'),
        'STREAM_DISK_SIZE': os.path.getsize('disk.ova.vmdk'),
        'VMX_VERSION': os.environ['VMX'],
    })

    # Create the OVA manifest.
    ova_manifest = "%s.mf" % build_name
    create_ova_manifest(ova_manifest, [ovf, 'disk.ova.vmdk'])

    # Create the OVA.
    ova = "%s.ova" % build_name
    create_ova(ova, [ovf, ova_manifest, 'disk.ova.vmdk'])

def sha256(path):
    m = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            m.update(data)
    return m.hexdigest()


def create_ova(path, infile_paths):
    print("image-build-ova: create ova %s" % path)
    with open(path, 'wb') as f:
        with tarfile.open(fileobj=f, mode='w|') as tar:
            for infile_path in infile_paths:
                tar.add(infile_path)

    chksum_path = "%s.sha256" % path
    print("image-build-ova: create ova checksum %s" % chksum_path)
    with open(chksum_path, 'w') as f:
        f.write(sha256(path))


def create_ovf(path, data):
    print("image-build-ova: create ovf %s" % path)
    with open(path, 'w') as f:
        f.write(Template(_OVF_TEMPLATE).substitute(data))


def create_ova_manifest(path, infile_paths):
    print("image-build-ova: create ova manifest %s" % path)
    with open(path, 'w') as f:
        for i in infile_paths:
            f.write('SHA256(%s)= %s\n' % (i, sha256(i)))

def stream_optimize_vmdk_files(infile):
    outfile = 'disk.ova.vmdk'
    if os.path.isfile(outfile):
        os.remove(outfile)
    args = [
        'qemu-img',
        'convert',
        '-o',
        'compat6,subformat=streamOptimized',
        '-f',
        'raw',
        '-O',
        'vmdk',
        infile,
        outfile
    ]
    print("image-build-ova: stream optimize %s --> %s (1-2 minutes)" % (infile, outfile))
    subprocess.check_call(args)

_OVF_TEMPLATE = '''<?xml version='1.0' encoding='UTF-8'?>
<Envelope xmlns="http://schemas.dmtf.org/ovf/envelope/1" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1" xmlns:vmw="http://www.vmware.com/schema/ovf" xmlns:rasd="http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData" xmlns:vssd="http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_VirtualSystemSettingData">
  <References>
    <File ovf:id="file1" ovf:href="disk.ova.vmdk" ovf:size="${STREAM_DISK_SIZE}"/>
  </References>
  <DiskSection>
    <Info>List of the virtual disks</Info>
    <Disk ovf:capacity="20" ovf:capacityAllocationUnits="byte * 2^30" ovf:format="http://www.vmware.com/interfaces/specifications/vmdk.html#streamOptimized" ovf:diskId="vmdisk1" ovf:fileRef="file1" ovf:populatedSize="${POPULATED_DISK_SIZE}"/>
  </DiskSection>
  <NetworkSection>
    <Info>The list of logical networks</Info>
    <Network ovf:name="nic0">
      <Description>Please select a network</Description>
    </Network>
  </NetworkSection>
  <vmw:StorageGroupSection ovf:required="false" vmw:id="group1" vmw:name="vSAN Default Storage Policy">
    <Info>Storage policy for group of disks</Info>
    <vmw:Description>The vSAN Default Storage Policy storage policy group</vmw:Description>
  </vmw:StorageGroupSection>
  <VirtualSystem ovf:id="VM">
    <Info>A Virtual system</Info>
    <Name>VM</Name>
    <AnnotationSection>
      <Info>A human-readable annotation</Info>
      <Annotation>vSphere image - ${OS_NAME}</Annotation>
    </AnnotationSection>
    <OperatingSystemSection ovf:id="${OS_ID}" ovf:version="${OS_VERSION}" vmw:osType="${OS_TYPE}">
      <Info>The operating system installed</Info>
      <Description>${OS_NAME}</Description>
    </OperatingSystemSection>
    <VirtualHardwareSection>
      <Info>Virtual hardware requirements</Info>
      <System>
        <vssd:ElementName>Virtual Hardware Family</vssd:ElementName>
        <vssd:InstanceID>0</vssd:InstanceID>
        <vssd:VirtualSystemType>vmx-${VMX_VERSION}</vssd:VirtualSystemType>
      </System>
      <Item>
        <rasd:AllocationUnits>hertz * 10^6</rasd:AllocationUnits>
        <rasd:Description>Number of Virtual CPUs</rasd:Description>
        <rasd:ElementName>2 virtual CPU(s)</rasd:ElementName>
        <rasd:InstanceID>1</rasd:InstanceID>
        <rasd:ResourceType>3</rasd:ResourceType>
        <rasd:VirtualQuantity>2</rasd:VirtualQuantity>
        <vmw:CoresPerSocket ovf:required="false">2</vmw:CoresPerSocket>
      </Item>
      <Item>
        <rasd:AllocationUnits>byte * 2^20</rasd:AllocationUnits>
        <rasd:Description>Memory Size</rasd:Description>
        <rasd:ElementName>2048MB of memory</rasd:ElementName>
        <rasd:InstanceID>2</rasd:InstanceID>
        <rasd:ResourceType>4</rasd:ResourceType>
        <rasd:VirtualQuantity>2048</rasd:VirtualQuantity>
      </Item>
      <Item>
        <rasd:Address>0</rasd:Address>
        <rasd:Description>SCSI Controller</rasd:Description>
        <rasd:ElementName>SCSI Controller 1</rasd:ElementName>
        <rasd:InstanceID>3</rasd:InstanceID>
        <rasd:ResourceSubType>VirtualSCSI</rasd:ResourceSubType>
        <rasd:ResourceType>6</rasd:ResourceType>
        <vmw:Config ovf:required="false" vmw:key="slotInfo.pciSlotNumber" vmw:value="160"/>
      </Item>
      <Item>
        <rasd:Address>0</rasd:Address>
        <rasd:Description>SATA Controller</rasd:Description>
        <rasd:ElementName>SATA Controller 0</rasd:ElementName>
        <rasd:InstanceID>4</rasd:InstanceID>
        <rasd:ResourceSubType>vmware.sata.ahci</rasd:ResourceSubType>
        <rasd:ResourceType>20</rasd:ResourceType>
      </Item>
      <Item>
        <rasd:AddressOnParent>0</rasd:AddressOnParent>
        <rasd:ElementName>Hard Disk 1</rasd:ElementName>
        <rasd:HostResource>ovf:/disk/vmdisk1</rasd:HostResource>
        <rasd:InstanceID>5</rasd:InstanceID>
        <rasd:Parent>3</rasd:Parent>
        <rasd:ResourceType>17</rasd:ResourceType>
      </Item>
      <Item>
        <rasd:AddressOnParent>0</rasd:AddressOnParent>
        <rasd:AutomaticAllocation>false</rasd:AutomaticAllocation>
        <rasd:ElementName>CD/DVD Drive 1</rasd:ElementName>
        <rasd:InstanceID>6</rasd:InstanceID>
        <rasd:Parent>4</rasd:Parent>
        <rasd:ResourceSubType>vmware.cdrom.atapi</rasd:ResourceSubType>
        <rasd:ResourceType>15</rasd:ResourceType>
      </Item>
      <Item>
        <rasd:AddressOnParent>0</rasd:AddressOnParent>
        <rasd:AutomaticAllocation>true</rasd:AutomaticAllocation>
        <rasd:Connection>nic0</rasd:Connection>
        <rasd:ElementName>Network adapter 1</rasd:ElementName>
        <rasd:InstanceID>8</rasd:InstanceID>
        <rasd:ResourceSubType>VmxNet3</rasd:ResourceSubType>
        <rasd:ResourceType>10</rasd:ResourceType>
        <vmw:Config ovf:required="false" vmw:key="slotInfo.pciSlotNumber" vmw:value="192"/>
        <vmw:Config ovf:required="false" vmw:key="connectable.allowGuestControl" vmw:value="true"/>
        <vmw:Config ovf:required="false" vmw:key="wakeOnLanEnabled" vmw:value="false"/>
      </Item>
      <Item ovf:required="false">
        <rasd:ElementName>Video card</rasd:ElementName>
        <rasd:InstanceID>9</rasd:InstanceID>
        <rasd:ResourceType>24</rasd:ResourceType>
        <vmw:Config ovf:required="false" vmw:key="enable3DSupport" vmw:value="false"/>
        <vmw:Config ovf:required="false" vmw:key="graphicsMemorySizeInKB" vmw:value="262144"/>
        <vmw:Config ovf:required="false" vmw:key="useAutoDetect" vmw:value="false"/>
        <vmw:Config ovf:required="false" vmw:key="videoRamSizeInKB" vmw:value="4096"/>
        <vmw:Config ovf:required="false" vmw:key="numDisplays" vmw:value="1"/>
        <vmw:Config ovf:required="false" vmw:key="use3dRenderer" vmw:value="automatic"/>
      </Item>
      <vmw:Config ovf:required="false" vmw:key="flags.vbsEnabled" vmw:value="false"/>
      <vmw:Config ovf:required="false" vmw:key="cpuHotAddEnabled" vmw:value="false"/>
      <vmw:Config ovf:required="false" vmw:key="nestedHVEnabled" vmw:value="false"/>
      <vmw:Config ovf:required="false" vmw:key="virtualSMCPresent" vmw:value="false"/>
      <vmw:Config ovf:required="false" vmw:key="flags.vvtdEnabled" vmw:value="false"/>
      <vmw:Config ovf:required="false" vmw:key="cpuHotRemoveEnabled" vmw:value="false"/>
      <vmw:Config ovf:required="false" vmw:key="memoryHotAddEnabled" vmw:value="false"/>
      <vmw:Config ovf:required="false" vmw:key="bootOptions.efiSecureBootEnabled" vmw:value="false"/>
      <vmw:Config ovf:required="false" vmw:key="firmware" vmw:value="bios"/>
      <vmw:Config ovf:required="false" vmw:key="virtualICH7MPresent" vmw:value="false"/>
    </VirtualHardwareSection>
    <vmw:StorageSection ovf:required="false" vmw:group="group1">
      <Info>Storage policy group reference</Info>
    </vmw:StorageSection>
    <ProductSection>
      <Info>Information about the installed software</Info>
      <Product>${OS_NAME}</Product>
      <Vendor>custom-build</Vendor>
      <Version>${OS_RELEASE}</Version>
      <FullVersion>custom-build</FullVersion>
      <ProductUrl>https://github.wsgc.com/TS-ComputeServices/os-image-templates</ProductUrl>
      <Property ovf:userConfigurable="false" ovf:value="${BUILD_TIMESTAMP}" ovf:type="string" ovf:key="BUILD_TIMESTAMP"></Property>
      <Property ovf:userConfigurable="false" ovf:value="${BUILD_DATE}" ovf:type="string" ovf:key="BUILD_DATE"></Property>
    </ProductSection>
  </VirtualSystem>
</Envelope>
'''

if __name__ == "__main__":
    main()
