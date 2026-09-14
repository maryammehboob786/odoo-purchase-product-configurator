# Oxygen Health Systems – Odoo 19 customizations

Local Docker stack (Odoo 19 Community + PostgreSQL 16) used to develop and test
custom modules before deploying them to the production server on Hostinger.

## Modules

| Module | Purpose |
| --- | --- |
| `addons/purchase_product_configurator` | Shows the Sales *product configurator* popup (chamber customization + optional products) on purchase order lines. |

## Local stack

```bash
# start database + Odoo (http://localhost:8069, master password "admin")
docker compose up -d

# first time only: create the test database with demo data and the module
docker compose run --rm odoo odoo -d ohs_test -i base,purchase,sale_management,stock,purchase_product_configurator --with-demo --stop-after-init

# seed a realistic hyperbaric chamber setup (vendor, attributes, optional products, vendor prices)
python scripts/setup_demo_data.py --db ohs_test

# after changing Python/XML in the module
docker compose run --rm odoo odoo -d ohs_test -u purchase_product_configurator --stop-after-init
docker compose restart odoo

# run the module's automated tests (Python + browser tour; the odoo_test image bundles Google Chrome)
# In Git Bash, prefix with MSYS_NO_PATHCONV=1 so "/purchase_product_configurator" is not rewritten as a Windows path.
docker compose run --rm odoo_test odoo -d ohs_test -u purchase_product_configurator --test-enable --test-tags /purchase_product_configurator --stop-after-init
```

Login: `admin` / `admin`.

## Deploying `purchase_product_configurator` to production

The module depends on the standard `purchase` and `sale` apps only (Community
and Enterprise are both fine).

1. Copy the folder `addons/purchase_product_configurator` to a directory that is
   in the server's `addons_path` (check `/etc/odoo/odoo.conf`, key `addons_path`;
   a dedicated folder such as `/opt/odoo/custom-addons` is recommended).
2. Restart the Odoo service (`sudo systemctl restart odoo`).
3. In Odoo, enable developer mode, go to *Apps → Update Apps List*, then search
   for **Purchase Product Configurator** and click *Install*.
4. Make sure the optional products (the chamber upgrades) have *Can be
   Purchased* ticked on their product form, otherwise the popup does not propose
   them on purchase orders.

Always take a database backup before installing on production.
