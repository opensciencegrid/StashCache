# StashCache

This documenation serve for Operations team and Site Admins who manage StashCache nodes (origin or cache server; or redirectors). All individual components of StashCache are based on [XRootD](xrootd.org) technology.
If you are a user of "stashcp" you want to follow [this](https://support.opensciencegrid.org/support/solutions/articles/12000002775-transferring-data-with-stashcache) document instead.

---

StashCache operations consist of the following documents:

* [StashCache redirectors](https://confluence.grid.iu.edu/display/STAS/Installing+an+XRootD+StashCache+Federation+Redirector): Redirectors are managed by GOC Operations team at Indiana University, redirectors provides federated access to the data across origins.
* [StashCache origins](https://github.com/opensciencegrid/StashCache/docs/admin): Managed by an organization, "origin" is storage element to host data locally and serve to users upon transfer request unless already cached.
* [StashCache caches](https://github.com/opensciencegrid/StashCache/docs/admin): Managed by an organization, "cache" server to keep data cached and immediately available within Stash federation.
* [StashCache upgrades](https://twiki.grid.iu.edu/bin/view/Documentation/Release3/StashCacheUpgrades): Keeps track of versions deployed at sites as well as other information about OS, system resources, connectivity.
