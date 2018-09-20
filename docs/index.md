# StashCache

## **This documentation is legacy.  Please view the current documentation on the [OSG Documentation](https://opensciencegrid.org/docs/data/stashcache/overview/) website.**


This documentation is for Site Admins and OSG Operations team who manage StashCache nodes (origin or cache server; or redirectors). Main functionality of StashCache is based on [XRootD](http://xrootd.org) technology, there are other components involved to function StashCache properly, though. E.g. if you are a user of **"stashcp"** you want to follow [this](https://support.opensciencegrid.org/support/solutions/articles/12000002775-transferring-data-with-stashcache) document instead.

---

StashCache operations consist of the following documents:

* [StashCache caches](admin/install.md): Managed by an organization, **"cache"** server to keep data cached and immediately available (via [stashcp](https://support.opensciencegrid.org/support/solutions/articles/12000002775-transferring-data-with-stashcach))within Stash federation (without re-transfering from "origin").
* [StashCache origins](admin/install.md): Managed by an organization, **"origin"** is data server to host files locally and serve them to users upon transfer request (via [stashcp](https://support.opensciencegrid.org/support/solutions/articles/12000002775-transferring-data-with-stashcach)) unless data are already cached.
* [StashCache redirectors](ops/redirector.md): Redirectors are managed by OSG Operations, redirectors provides federated access to the data across origins.
* [StashCache upgrades](ops/upgrades.md): Keeps track of versions deployed at sites as well as other information about OS, system resources, connectivity, etc.
