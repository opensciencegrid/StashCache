# Configuring Cache Server with authentication

In addition to default Cache Server instance configured [here](configure-cache.md), you have option to enable authenticated cache. This chapter describes all the steps needed. 

Packages installed: `stashcache-daemon fetch-crl stashcache-cache-server xrootd-lcmaps globus-proxy-utils`

## Authenticated Cache server

:heavy_exclamation_mark: Make sure you've in place following pre-requisities from [install step here](install.md):
* __Service certificate:__ create copy of the certificate to `/etc/grid-security/xrd/xrd{cert,key}.pem`
   * set owner of the directory `/etc/grid-security/xrd/` to `xrootd:xrootd` user:
      ```
      $ chown -R xrootd:xrootd /etc/grid-security/xrd/
      ```
* __Network ports__: allow connections on port `8443 (TCP)` 

:heavy_exclamation_mark: Beware, authenticated cache requires presence of the config file `/etc/xrootd/xrootd-stashcache-cache-server.cfg`. 

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
1. Create the file with following content:
```
   [root@client ~]$ service xrootd@stashcache-cache-server-auth status
```

2. Reload daemons:
```
   [root@client ~]$ systemctl daemon-reload
```

#### Proxy.service
1. Create the file with following content:
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

2. Reload daemons:
```
   [root@client ~]$ systemctl daemon-reload
```

3. Start proxy daemon:
```
   
```

#### Timer configuration
1. Create the file with following content:
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

2. Enable timer:
```
   [root@client ~]$ systemctl enable xrootd-renew-proxy.timer
```

3. Start and check if timer is active and working:
```
   [root@client ~]$ systemctl start xrootd-renew-proxy.timer
   [root@client ~]$ systemctl is-active xrootd-renew-proxy.timer
   [root@client ~]$ systemctl list-timers xrootd-renew-proxy*
```

### RHEL6
...to be added

### Add Authfile for authenticated cache
Authfile for authenticated cache may differ from `/etc/xrootd/Authfile-noauth` defined in [noauth configuration](configure-cache.md). Example:
```
   [root@client ~]$ cat /etc/xrootd/Authfile-auth 
   g /osg/ligo /user/ligo r
   u ligo /user/ligo lr / rl
```

When ready with configuration, please [register](../ops/register.md) and [start](../ops/start.md) your StashCache Cache server.
