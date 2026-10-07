# John's ERP Demo Backup

This repository contains the database backup and uploaded files for the ERP Demo. 

Because ERPNext and Frappe are massive open-source frameworks, you do **not** need to push the core framework files here. To run this ERP remotely (on a VPS, a new laptop, etc.), you simply install a fresh instance of ERPNext and then restore this exact database backup into it.

## How to restore this ERP remotely:

1. **Install Frappe & ERPNext version 15** on your new server/machine:
   ```bash
   bench init --frappe-branch version-15 frappe-bench
   cd frappe-bench
   bench get-app erpnext --branch version-15
   bench new-site client.local
   bench --site client.local install-app erpnext
   ```

2. **Clone this backup repository** into your server.

3. **Restore the database and files**:
   Run this command from inside your `frappe-bench` directory, pointing it to the SQL and TAR files in this repository:
   ```bash
   bench --site client.local restore /path/to/cloned/repo/20261007_180518-client_local-database.sql.gz \
   --with-public-files /path/to/cloned/repo/20261007_180518-client_local-files.tar \
   --with-private-files /path/to/cloned/repo/20261007_180518-client_local-private-files.tar
   ```

4. **Migrate the database** to rebuild custom fields and caches:
   ```bash
   bench --site client.local migrate
   ```

That's it! Your entire ERP (with all workflows, print formats, demo items, and data) will be instantly restored and ready to use.
