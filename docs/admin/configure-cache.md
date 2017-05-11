# Configuring Cache Server

Packages installed: `stashcache-daemon fetch-crl stashcache-cache-server`

The following section describes required configuration to have a functional non-authenticated StashCache Cache (not origin server!). StashCache Cache package `stashcache-cache-server` needs to be manually configured from pre-existing XRootD configuration.

## Cache server
!!! Note: 
:bangbang: While example of the configuration file below provides combination of _authenticated_ and _non-authenticated_ _Cache_, the non-authenticated cache is considered to be default and authenticated cache just optional (additional) service. If you're about to configure in addition _authenticated cache_ read to the end of this document and then follow post-installation of [authenticated part here](configure-cache-auth.md).

For configuring **cache** one needs to define directive `pss.origin redirector.osgstorage.org:1024` (not `all.manager redirector.osgstorage.org+ 1213` directive as it is in case of [configuring origin](configure-origin.md)). 
`StashCache-daemon` package provides default configuration file `/etc/xrootd/xrootd-stashcache-cache-server.cfg`. Example of the configuration of cache server is as follows:
```
all.export  /
set cachedir = /stash
xrd.allow host *
sec.protocol  host
all.adminpath /var/spool/xrootd

xrootd.trace emsg login stall redirect
ofs.trace all
xrd.trace all
cms.trace all

ofs.osslib  libXrdPss.so
pss.origin redirector.osgstorage.org:1094
pss.cachelib libXrdFileCache.so
pss.setopt DebugLevel 1

oss.localroot $(cachedir)

# Config for v1 (xrootd <=v4.5.0)
#pfc.nramprefetch 4
#pfc.nramread 4
#pfc.diskusage 0.98 0.99

# Config for v2 (xrootd >v4.5.0)
pfc.blocksize 512k
pfc.ram       32g
pfc.prefetch  10
pfc.diskusage 0.98 0.99

xrootd.seclib /usr/lib64/libXrdSec.so
sec.protocol /usr/lib64 gsi \
  -certdir:/etc/grid-security/certificates \
  -cert:/etc/grid-security/xrd/xrdcert.pem \
  -key:/etc/grid-security/xrd/xrdkey.pem \
  -crl:1 \
  -authzfun:libXrdLcmaps.so \
  -authzfunparms:--lcmapscfg,/etc/xrootd/lcmaps.cfg,--loglevel,4|useglobals \
  -gmapopt:10 \
  -authzto:3600

# Enable the authorization module, even if we have an unauthenticated instance.
ofs.authorize 1
acc.audit deny grant

# Run the authenticated instance on port 8443 (Xrootd and HTTPS)
# Notice authenticated and unauthenticated instances use separate auth
# files.
if named stashcache-cache-server-auth
   #pss.origin  red-gridftp4.unl.edu:1094
   xrd.port 8443
   acc.authdb /etc/xrootd/Authfile-auth
   sec.protbind * gsi
   xrd.protocol http:8443 libXrdHttp.so
   pss.origin xrootd-local.unl.edu:1094
else
# Unauthenticated instance runs on port 1094 (Xrootd) and 8000 (HTTP/HTTPS)
   acc.authdb /etc/xrootd/Authfile-noauth
   #sec.protbind * none
   sec.protbind  * none
   xrd.protocol http:8000 libXrdHttp.so
fi

http.cadir /etc/grid-security/certificates
http.cert /etc/grid-security/xrd/xrdcert.pem
http.key /etc/grid-security/xrd/xrdkey.pem
http.secxtractor /usr/lib64/libXrdLcmaps.so
http.listingdeny yes
http.staticpreload http://static/robots.txt /etc/xrootd/stashcache-robots.txt

# Tune the client timeouts to more aggressively timeout.
pss.setopt ParallelEvtLoop 10
pss.setopt RequestTimeout 25
pss.setopt ConnectTimeout 25
pss.setopt ConnectionRetry 2

#Sending monitoring information
xrd.report uct2-collectd.mwt2.org:9931
xrootd.monitor all auth flush 30s window 5s fstat 60 lfn ops xfr 5 dest redir fstat info user uct2-collectd.mwt2.org:9930

all.sitename Nebraska

# Optional configuration
# Remote debugging
xrootd.diglib * /etc/xrootd/digauth.cf
```

### Add Authfile for non-authenticated cache
In Authfile you want to allow local reads below `$(cachedir)` defined in the main config. Example of Authfile:
```
   [root@client ~]$ cat /etc/xrootd/Authfile-noauth 
   u * /user/ligo -rl / rl
```

### Add Robots file
```
   [root@client ~]$ cat /etc/xrootd/stashcache-robots.txt 
   User-agent: *
   Disallow: /
```

### RHEL7
On RHEL7 system, you need to run following systemd unit:
* `systemctl start xrootd@stashcache-cache-server.service`
* `systemctl start condor.service`

Please, refer to [start services document](../ops/start.md) for more information.

### RHEL6
...to be added, old doc for RHEL6 configuration resides temporarily [here](https://twiki.grid.iu.edu/bin/view/Documentation/Release3/InstallStashCache).

When ready with configuration, please [register](../ops/register.md) and [start](../ops/start.md) your StashCache Cache server.
If you'd like to configure in addition authenticated cache instance, please follow [this](configure-cache-auth.md) document.
