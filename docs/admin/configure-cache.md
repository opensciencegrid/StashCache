# Configuring Cache Server

The following section describes required configuration to have a functional StashCache Cache (not origin server!). StashCache Cache package `stashcache-cache-server` needs to be manually configured from pre-existing xrootd configuration.

## Cache server
!!! Note: 
:bangbang: While example of the configuration file below provides combination of _authenticated_ and _non-authenticated_ _Cache_, the non-authenticated cache config is considered to be default option. If you're about to configure in addition _authenticated cache_ read to the end of this document.

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

# Config for v1 (everything <=v4.5.0 of xrootd)
#pfc.nramprefetch 4
#pfc.nramread 4
#pfc.diskusage 0.98 0.99

# Config for v2 (everything >v4.5.0 of xrootd)
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

### Add AuthFile for non-authenticated cache
```
   [root@client ~]$ cat /etc/xrootd/Authfile-noauth 
   u * /user/ligo -rl / rl
```

## Authenticated Cache server

:heavy_exclamation_mark: Make sure you've installed `xrootd-lcmaps` and `globus-proxy-utils` packages during [install step here](install.md) included following pre-steps:
* __Service certificate:__ create copy of the certificate to `/etc/grid-security/xrd/xrd{cert,key}.pem`
   * set owner of the directory `/etc/grid-security/xrd/` to `xrootd:xrootd` user:
      ```
      $ chown -R xrootd:xrootd /etc/grid-security/xrd/
      ```
* __Network ports__: allow connections on port `8443 (TCP)` 

Now, create symbolic link to existing configuration file with `-auth` postfix:
```
   [root@client ~]$ cd /etc/xrootd/
   [root@client ~]$ ln -s xrootd-stashcache-cache-server.cfg xrootd-stashcache-cache-server-auth.cfg
```

### RHEL7

On RHEL7 system, you need to configure in addition following systemd units:
* `xrootd@stashcache-cache-server-auth.service`
* `xrootd-renew-proxy.service`
* `xrootd-renew-proxy.timer`

#### Auth.service
Create the file with following content:
```
   [root@client ~]$ service xrootd@stashcache-cache-server-auth status
```

Reload deamons:
```
   [root@client ~]$ systemctl daemon-reload
```

#### Proxy.service
Create the file with following content:
```
   [root@client ~]$ cat /usr/lib/systemd/system/xrootd-renew-proxy.service
   [Unit]
   Description=Renew xrootd proxy

   [Service]
   User=xrootd
   Group=xrootd
   Type = oneshot
   ExecStart = /bin/grid-proxy-init -cert /etc/grid-security/xrd/xrdcert.pem -key /etc/grid-security/xrd/xrdkey.pem -out /tmp/x509up_xrootd -valid 48:00

   [Install]
   WantedBy=multi-user.target
```
Reload deamons:
```
   [root@client ~]$ systemctl daemon-reload
```
Start proxy daemon:
```
   
```

#### Timer configuration
Create the file with following content:
```
   [root@client ~]$ cat /usr/lib/systemd/system/xrootd-renew-proxy.timer
   [Unit]
   Description=Renew proxy every day at midnight
   
   [Timer]
   OnCalendar=*-*-* 00:00:00
   Unit=xrootd-renew-proxy.service
   
   [Install]
   WantedBy=multi-user.target
```

Enable timer:
```
   [root@client ~]$ systemctl enable xrootd-renew-proxy.timer
```

Start and check if timer is active and working:
```
   [root@client ~]$ systemctl start xrootd-renew-proxy.timer
   [root@client ~]$ systemctl is-active xrootd-renew-proxy.timer
   [root@client ~]$ systemctl list-timers xrootd-renew-proxy*
```

#### Add Authfile for authenticated cache
```
   [root@client ~]$ cat /etc/xrootd/Authfile-auth 
   g /osg/ligo /user/ligo r
   u ligo /user/ligo lr / rl
```

### RHEL6
...to be added

## Optional configuration

### Adjust disk utilization

To adjust the disk utilization of your StashCache cache, modify the values of `pfc.diskusage` in `/etc/xrootd/xrootd-stashcache-cache-server.cfg`:

```
pfc.diskusage 0.98 .99
```

The first value and second values correspond to the low and high usage watermarks, respectively, in percentages. When the high watermark is reached, the XRootD service will automatically purge cache objects down to the low watermark.

### Enable remote debugging
This feature enables remote debugging via the `digFS` read-only file system
```
xrootd.diglib * /etc/xrootd/digauth.cf
```
where `/etc/xrootd/digauth.cf` may have following content:
```
all allow host h=abc.org
all allow host h=*.xyz.edu
```

When ready with configuration, please [register](../ops/register.md) and [start](../ops/start.md) your StashCache Cache server.
