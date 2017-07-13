# Installing XRootD StashCache Federation Redirector

Use these instructions to install an XRootD StashCache Federation Redirector. These instructions assume that you have SL, CentOS, or RHEL 6.

## Redirector server recommendations
The service is very lightweight depending on number of subscribers (caching proxies), though. Recommended would be use machine with 4GB of RAM and 2 cores. Load avg is practically close to zero, therefore 2 cores is sufficient with as much RAM as you can reasonably ask for.  As far as disk goes, something reasonable like 500GB of local storage is good enough, and best if the server has a 10 Gbps NIC at least.

You must have ==port== `1094` and `1213` open to all traffic; otherwise the redirector will not work.
In addition (this is optional), we run separate xrootd server instance on redirector host for RSV tests which needs open port `2094`.

## Installation using yum
If you don't want to use yum, refer to http://xrootd.org/dload.html for other methods.

Use predefined OSG repo or copy `http://xrootd.org/binaries/xrootd-stable-slc6.repo` to `/etc/yum.repos.d`
Do: `yum install xrootd` and answer every question with y


## Configure the (local) server for RSV tests (optional)
Edit the configuration file `/etc/xrootd/xrootd-clustered-server.cfg` to look like this:

```
xrd.port 2094 if exec xrootd
all.adminpath /var/spool/xrootd

all.role server

all.export /stash/
#Production Redirector DNS alias
all.manager redirector.osgstorage.org+ 1213
#ITB Redirector DNS alias
#all.manager stash-itb.grid.iu.edu+ 1213

For the RSV test purpose make sure the testing file is present on the file system:
/stash/user/test.1M
```

## Configure the redirector for caches and origins

1. Edit the configuration file (`/etc/xrootd/xrootd-clustered.cfg`) to look as follows:
```
     all.export   / 
     xrd.allow host * 
     cms.allow host * 
     sec.protocol  host 
     sec.protbind  * none 
     all.adminpath /var/spool/xrootd 
     all.pidpath /var/run/xrootd 
 
     xrootd.trace emsg login stall redirect 
     ofs.trace all 
     xrd.trace all debug 
     cms.trace all debug 
 
     xrd.port 1094 
     all.role meta manager 

     #Production Redirector DNS alias
     all.manager meta all redirector.osgstorage.org+ 1213
     all.sitename GOC-StashCache-Redirector 

     #ITB Redirector DNS alias
     #all.manager meta all stash-itb.grid.iu.edu+ 1213
     #all.sitename GOC-StashCache-ITB-Redirector
     # XRootD Stats - sends UDP packets
     xrd.report uct2-collectd.mwt2.org:9931
     xrootd.monitor all auth flush 30s window 5s fstat 60 lfn ops xfr 5 dest redir fstat info user uct2-collectd.mwt2.org:9930
```

2. Change ownership of these directories:
```
     chown -R xrootd: /var/spool/xrootd
     chown -R xrootd: /var/log/xrootd
     chown -R xrootd: /stash
```

3. Start the service: `/etc/init.d/{xrootd,cmsd} start`

4. Set the service start when machine is rebooted: `chkconfig --level 2345 {xrootd,cmsd} on`

5. Test that your instance works as expected, ideally would be setup origin server and subscribe into this redirector. Then, see the log files if origin server joined the Federation. Now, configure `/etc/sysconfig/xrootd`.
Assuming host runs both ==server and redirector== and the two configurations above are applied, make sure properly edit /etc/sysconfig/xrootd and add/edit these lines:
```
       XROOTD_DEFAULT_OPTIONS="-l /var/log/xrootd/xrootd.log -c /etc/xrootd/xrootd-clustered.cfg -k fifo"
       CMSD_DEFAULT_OPTIONS="-l /var/log/xrootd/cmsd.log -c /etc/xrootd/xrootd-clustered.cfg -k fifo”
       XROOTD_SERVER_OPTIONS="-l /var/log/xrootd/xrootd.log -c /etc/xrootd/xrootd-clustered-server.cfg -k fifo"
       CMSD_SERVER_OPTIONS="-l /var/log/xrootd/cmsd.log -c /etc/xrootd/xrootd-clustered-server.cfg -k fifo”
...
...
       XROOTD_INSTANCES="default server"
       CMSD_INSTANCES="default server”
```
If you don't choose server instance setup for RSV tests you can skip lines XROOTD_SERVER_OPTIONS and CMSD_SERVER_OPTIONS as well as ==server== in the _INSTANCES lines.

## Test if Origins subscribe to redirector
There is command `xrdmapc` in the xrootd-server packages that you can use to check what Origins subscribe to your redirector:
```
$ xrdmapc --list all redirector.osgstorage.org:1094 
0**** redirector.grid.iu.edu:1094
      Srv redirector1.grid.iu.edu:2094
      Srv csiu.grid.iu.edu:1094
      Srv redirector2.grid.iu.edu:2094
      Srv stashcache.fnal.gov:1094
      Srv ceph-gridftp1.grid.uchicago.edu:1094
      Srv stash.osgconnect.net:1094
```

## Useful Project Links
https://twiki.opensciencegrid.org/bin/view/SoftwareTeam/SW023_StashCacheDetails
https://twiki.opensciencegrid.org/bin/view/SoftwareTeam/SW023_XrootdAcrossOsg
