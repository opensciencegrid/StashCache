# Optional configuration

## Adjust disk utilization
To adjust the disk utilization of your StashCache cache, modify the values of `pfc.diskusage` in `/etc/xrootd/xrootd-stashcache-cache-server.cfg`:
```
pfc.diskusage 0.98 .99
```
The first value and second values correspond to the low and high usage watermarks, respectively, in percentages. When the high watermark is reached, the XRootD service will automatically purge cache objects down to the low watermark.

## Enable remote debugging
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
