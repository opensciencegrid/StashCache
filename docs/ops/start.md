# Managing StashCache and associated services

Ensure that your `/stash` disk is mounted, and then start `xrootd` and `condor` service.

## Non-authenticated Cache server services
| **Software** | **Service name** | **Notes** |
|--------------|------------------|-----------|
| XRootD | `xrootd@stashcache-cache-server.service` | RHEL7 |
| HTCondor | `condor.service` | RHEL7  |
| Fetch CRL | `fetch-crl-cron` | RHEL7 |

## Authenticated Cache server services
| **Software** | **Service name** | **Notes** |
|--------------|------------------|-----------|
| XRootD | `xrootd@stashcache-cache-server-auth.service` | RHEL7 |
|  | `xrootd-renew-proxy.service` | RHEL7 |
|  | `xrootd-renew-proxy.timer` | RHEL7  |
| HTCondor | `condor.service` | RHEL7  |
| Fetch CRL | `fetch-crl-cron` | RHEL7 |

### Test Cache server reports to HTCondor collector
To verify that your cache is being monitored properly, run the following command:
```
[user@client ~]$ condor_status -any -l -const "Name==\"xrootd@`hostname`\""
```
Where `hostname` is the string returned by the hostname command. The output of the above command should provide an HTCondor ClassAd that details the status of your cache.

### Test CVMFS accessibility via Cache server
```
[user@client ~]$ curl -O http://cache_host:8000/user/dweitzel/public/blast/queries/query1
```

## Origin server services
| **Software** | **Service name** | **Notes** |
|--------------|------------------|-----------|
| XRootD | `xrootd@stashcache-origin-server.service` | RHEL7 |
| XRootD | `cmsd@stashcache-origin-server.service` | RHEL7  |

### Test Origin server availability in Stash Federation
To verify that your origin is being subscribed to the redirector, run the following command:
```
[user@client ~]$ xrdmapc --list s redirector.opensciencegrid.org:1094 
0**** redirector.grid.iu.edu:1094
      Srv redirector1.grid.iu.edu:2094
      Srv csiu.grid.iu.edu:1094
      Srv stash.osgconnect.net:1094
      Srv stashcache.fnal.gov:1094
      Srv redirector2.grid.iu.edu:2094
      Srv ceph-gridftp1.grid.uchicago.edu:1094
```
The output should list hostname of your service. If not, look for any sings of trouble in the log files or contact us at `stashcache@opensciencegrid.org`.

## Start/stop services
| **To...** | **Run the command...** | **Notes** |
|-----------|------------------------|-----------|
| Start a service | systemctl start SERVICE-NAME | RHEL7 |
| Stop a service | systemctl stop SERVICE-NAME | RHEL7 |
| Status | systemctl status SERVICE-NAME | RHEL7 | 
| Enable | systemctl enable SERVICE-NAME | RHEL7 |
