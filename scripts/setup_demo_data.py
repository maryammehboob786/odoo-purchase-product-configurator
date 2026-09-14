"""Seed the local Odoo 19 test database with a hyperbaric-chamber setup.

Creates (idempotently, matched by name):
  * a vendor "Chamber Manufacturer Co.",
  * a "Hyperbaric Chamber" product with
      - a variant attribute  "Chamber Size"           (32 inch / 40 inch),
      - a no-variant attribute "Chamber Customization" (Standard / Extra Viewing
        Window / Wheelchair Door / Custom Color with free text),
      - optional products: "20 Lpm Oxygen Concentrator", "3D Contour Memory Foam
        Mattress", "Chamber Frame Upgrade" and a non-purchasable "Installation
        Service" (must NOT be proposed on purchase orders),
  * vendor prices for the vendor.

Usage:  python scripts/setup_demo_data.py [--url http://localhost:8069] [--db ohs_test]
"""

import argparse
import xmlrpc.client


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://localhost:8069')
    parser.add_argument('--db', default='ohs_test')
    parser.add_argument('--user', default='admin')
    parser.add_argument('--password', default='admin')
    args = parser.parse_args()

    common = xmlrpc.client.ServerProxy(f'{args.url}/xmlrpc/2/common')
    uid = common.authenticate(args.db, args.user, args.password, {})
    if not uid:
        raise SystemExit("Authentication failed")
    models = xmlrpc.client.ServerProxy(f'{args.url}/xmlrpc/2/object')

    def call(model, method, *a, **kw):
        return models.execute_kw(args.db, uid, args.password, model, method, list(a), kw)

    def get_or_create(model, domain, values):
        ids = call(model, 'search', domain, limit=1)
        if ids:
            call(model, 'write', ids, values)
            return ids[0]
        return call(model, 'create', [values])[0]

    vendor_id = get_or_create('res.partner', [('name', '=', "Chamber Manufacturer Co.")], {
        'name': "Chamber Manufacturer Co.",
        'is_company': True,
    })

    # ---- attributes ---------------------------------------------------------
    def attribute(name, create_variant, display_type, values):
        attr_id = get_or_create('product.attribute', [('name', '=', name)], {
            'name': name,
            'create_variant': create_variant,
            'display_type': display_type,
        })
        value_ids = []
        for value_name, is_custom in values:
            value_ids.append(get_or_create(
                'product.attribute.value',
                [('attribute_id', '=', attr_id), ('name', '=', value_name)],
                {'attribute_id': attr_id, 'name': value_name, 'is_custom': is_custom},
            ))
        return attr_id, value_ids

    size_attr, size_values = attribute(
        "Chamber Size", 'always', 'radio', [("32 inch", False), ("40 inch", False)]
    )
    custom_attr, custom_values = attribute(
        "Chamber Customization", 'no_variant', 'radio', [
            ("Standard", False),
            ("Extra Viewing Window", False),
            ("Wheelchair Door", False),
            ("Custom Color", True),
        ],
    )

    # ---- optional products --------------------------------------------------
    def product(name, purchase_ok=True, sale_ok=True, cost=0.0, price=0.0, extra=None):
        values = {
            'name': name,
            'purchase_ok': purchase_ok,
            'sale_ok': sale_ok,
            'standard_price': cost,
            'list_price': price,
            'type': 'consu',
        }
        values.update(extra or {})
        return get_or_create('product.template', [('name', '=', name)], values)

    concentrator = product("20 Lpm Oxygen Concentrator", cost=1500, price=5000,
                           extra={'description_purchase': "110-120 V, 1920 W"})
    mattress = product("3D Contour Memory Foam Mattress", cost=120, price=300)
    frame = product("Chamber Frame Upgrade", cost=400, price=900)
    installation = product("Installation Service", purchase_ok=False, price=500,
                           extra={'type': 'service'})

    # ---- main product -------------------------------------------------------
    chamber = get_or_create('product.template', [('name', '=', "Hyperbaric Chamber")], {
        'name': "Hyperbaric Chamber",
        'purchase_ok': True,
        'sale_ok': True,
        'type': 'consu',
        'standard_price': 3000,
        'list_price': 6000,
        'description_purchase': "Soft-shell hyperbaric chamber, 1.3 ATA",
        'optional_product_ids': [(6, 0, [concentrator, mattress, frame, installation])],
    })
    existing_lines = call('product.template.attribute.line', 'search',
                          [('product_tmpl_id', '=', chamber)])
    if not existing_lines:
        call('product.template', 'write', [chamber], {
            'attribute_line_ids': [
                (0, 0, {'attribute_id': size_attr, 'value_ids': [(6, 0, size_values)]}),
                (0, 0, {'attribute_id': custom_attr, 'value_ids': [(6, 0, custom_values)]}),
            ],
        })

    variants = call('product.product', 'search_read', [('product_tmpl_id', '=', chamber)],
                    fields=['id', 'display_name'])
    # The cost is stored per variant for multi-variant products.
    call('product.product', 'write', [v['id'] for v in variants], {'standard_price': 3000.0})
    prices = {"32 inch": 4000.0, "40 inch": 5500.0}

    # ---- vendor prices ------------------------------------------------------
    def supplierinfo(tmpl_id, price, product_id=False):
        domain = [('partner_id', '=', vendor_id), ('product_tmpl_id', '=', tmpl_id),
                  ('product_id', '=', product_id)]
        get_or_create('product.supplierinfo', domain, {
            'partner_id': vendor_id,
            'product_tmpl_id': tmpl_id,
            'product_id': product_id,
            'price': price,
            'min_qty': 1,
        })

    for variant in variants:
        for size, price in prices.items():
            if size in variant['display_name']:
                supplierinfo(chamber, price, variant['id'])
    supplierinfo(concentrator, 1800.0)
    supplierinfo(mattress, 150.0)
    supplierinfo(frame, 450.0)

    print("Vendor id:", vendor_id)
    print("Hyperbaric Chamber template id:", chamber)
    print("Variants:", [v['display_name'] for v in variants])
    print("Done.")


if __name__ == '__main__':
    main()
