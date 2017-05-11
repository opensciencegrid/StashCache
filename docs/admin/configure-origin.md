# Configuring Origin Server

Packages installed: `stashcache-daemon fetch-crl stashcache-origin-server`

The following section describes required configuration to have a functional StashCache Origin (not cache server!). StashCache Origin package `stashcache-cache-origin` needs to be manually configured from pre-existing XRootD configuration.

## Origin server
The origin server connects only to a redirector (not directly to cache server), thus minimal xrootd configuration is required. `StashCache-daemon` package provides default configuration file `/etc/xrootd/xrootd-stashcache-origin-server.cfg`. Example of the configuration of origin server is as follows:
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

### RHEL7
On RHEL7 system, you need to run following systemd units:
* `xrootd@stashcache-cache-origin.service`
* `cmsd@stashcache-cache-origin.service`

### RHEL6
...to be added

When ready with configuration, please [register](../ops/register.md) and [start](../ops/start.md) your StashCache Origin server.
