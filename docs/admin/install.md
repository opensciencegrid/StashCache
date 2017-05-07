# Installation Guide

This document describes how to install a StashCache cache, a server that caches files locally rather than serving files to the StashCache federation. The installation utilizes XRootD and HTCondor for file storage and monitoring, respectively.

---

Before starting the installation process, consider the following points:

* User IDs: If they do not exist already, the installation will create the Linux user IDs condor and xrootd
* Service certificate: The StashCache service uses a host certificate at /etc/grid-security/host*.pem
* Network ports: The StashCache service must talk to the central collector on port 9619 (TCP) and XRootD services on port 1094 (TCP)
* Hardware requirements: We recommend that a StashCache server has at least 10Gbps connectivity, 1TB of disk space, and 8GB of RAM. 

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
4. Mount the disk that will be used for the cache to /stash and set owner of the directory to xrootd user.
