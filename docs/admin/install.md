# Installation Guide

This document describes how to install a StashCache cache, a server that caches files locally rather than serving files to the StashCache federation. The installation utilizes XRootD and HTCondor for file storage and monitoring, respectively.

---

## Installation pre-requisities

Before starting the installation process, consider the following mandatory points:

* __User IDs:__ If they do not exist already, the installation will create the Linux user IDs condor and xrootd
* __Service certificate:__ The StashCache service uses a host certificate at `/etc/grid-security/host*.pem`
* __Network ports:__ The StashCache service must talk to:
   * the central collector on port `9619 (TCP)` 
   * XRootD service on port `1094 (TCP)`
   * and allow XRootD service over HTTP on port `8000 (TCP)`
* __Hardware requirements:__ We recommend that a StashCache server has at least 10Gbps connectivity, 1TB of disk space, and 8GB of RAM. 
   * More information about hardware and system configuration of existing caches you can find at [Upgrade status page](../ops/upgrades.md).

!!! Note:
:heavy_exclamation_mark: If installing authenticated StashCache, you need to do in addition following:
* __Service certificate:__ create copy of the certificate to `/etc/grid-security/xrd/xrd{cert,key}.pem`
   * set owner of the directory `/etc/grid-security/xrd/` to `xrootd:xrootd` user:
      ```
      $ chown -R xrootd:xrootd /etc/grid-security/xrd/
      ```
* __Network ports__: allow connections on port `8443 (TCP)` 

As with all OSG software installations, there are some one-time steps to prepare in advance:

* Ensure the host has [a supported operating system](https://twiki.grid.iu.edu/bin/view/Documentation/Release3/SupportedOperatingSystems)
* Obtain root access to the host
* Prepare [the required Yum repositories](https://twiki.grid.iu.edu/bin/view/Documentation/Release3/YumRepositories)
* Install [CA certificates](https://twiki.grid.iu.edu/bin/view/Documentation/Release3/InstallCertAuth)

## Installing the StashCache metapackage

The StashCache daemon consists of an XRootD server and an HTCondor-based service for collecting and reporting statistics about the cache. To simplify installation, OSG provides convenience RPMs that install all required software with a single command:

1. Clean yum cache:
```
   [root@client ~]$ yum clean all --enablerepo=*
```

2. Update software:
```
   [root@client ~]$ yum update
```
   This command will update all packages on your system.

3. Install the StashCache metapackage from OSG3.3 repository:
```
   [root@client ~]$ yum install stashcache-daemon fetch-crl stashcache-cache-{server || origin}
```

4. Mount the disk that will be used for the cache to */stash* and set owner of the directory to `*xrootd:xrootd*` user.

!!! Note: 
:heavy_exclamation_mark: If installing authenticated StashCache, you need additional packages to be installed:
```
   [root@client ~]$ yum install xrootd-lcmaps globus-proxy-utils
```
