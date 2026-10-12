# Kodessy App

Custom ERPNext App for Kodessy Business Implementation.

### Modules Covered:
- **Sales**: Quotation custom validations, approval workflows, custom print formats.
- **Fulfilment**: Warehouse management, delivery automation.
- **Procurement**: Purchase order approvals and supplier workflows.
- **Finance**: Custom ledgers, invoice validation, regional tax configurations.

### Installation

```bash
bench get-app https://github.com/Luffy11323/John-s-ERP
bench --site [your-site] install-app kodessy_app
bench --site [your-site] migrate
```
