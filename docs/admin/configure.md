# Configuring StashCache

The following section describes required configuration to have a functional StashCache cache. StashCache packages need to be manually configured from pre-existing xrootd configuration.

## Origin server
The origin server connects only to a redirector (not directly to cache server), thus minimal xrootd configuration is required. The configuration file, `/etc/xrootd/xrootd-stashcache-origin-server.cfg`:
```
all.export /
set localroot = /stash
xrd.port 1094

all.role server
all.manager redirector.osgstorage.org+ 1213

oss.localroot $(localroot)
xrootd.trace emsg login stall redirect
ofs.trace none
xrd.trace conn
cms.trace all
sec.protocol  host
sec.protbind  * none
all.adminpath /var/spool/xrootd
all.pidpath /var/run/xrootd

# Sending monitoring information
xrd.report uct2-collectd.mwt2.org:9931
xrootd.monitor all auth flush 30s window 5s fstat 60 lfn ops xfr 5 dest redir fstat info user uct2-collectd.mwt2.org:9930
```

[P](../configs/xrootd-stashcache-origin-server.cfg)

## Cache server
!!! Note: 
:bangbang: While example of the configuration file below provides combination of _authenticated_ and _non-authenticated_ _Cache_, the non-authenticated cache config is considered to load by system as default.

For configuring **cache** one needs to define directive `pss.origin redirector.osgstorage.org:1024` (not `all.manager redirector.osgstorage.org+ 1213` directive as it is in case of configuring **origin**). 
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

# Config for v1 (everything <=v4.5.0)
#pfc.nramprefetch 4
#pfc.nramread 4
#pfc.diskusage 0.98 0.99

# Config for v2 (4.4.0 pre-release)
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

# Remote debugging
xrootd.diglib * /etc/xrootd/digauth.cf
```

### Authenticated Cache server

:heavy_exclamation_mark: Make sure you've installed `xrootd-lcmaps` package during install [step](install.md##Installing the StashCache metapackage)

#### RHEL7

#### RHEL6

### Optional configuration
#### Adjust disk utilization
To adjust the disk utilization of your StashCache cache, modify the values of pfc.diskusage in /etc/xrootd/xrootd-stashcache-cache-server.cfg:
```
pfc.diskusage 0.98 .99
```
The first value and second values correspond to the low and high usage watermarks, respectively, in percentages. When the high watermark is reached, the XRootD service will automatically purge cache objects down to the low watermark.

#### Enable remote debugging
This feature enables remote debugging via the digFS read-only file system
```
xrootd.diglib * /etc/xrootd/digauth.cf
```
where `/etc/xrootd/digauth.cf` may have following content:
```
all allow host h=abc.org
all allow host h=*.xyz.edu
```
