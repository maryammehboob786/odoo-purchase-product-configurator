"""Seed a neutral office-furniture example into a local Odoo 19 database.

Creates (idempotently, matched by name), reusing images of the standard Odoo demo products:
  * a vendor "Nordic Office Supply Co.",
  * a configurable "Executive Standing Desk" with
      - variant attributes "Desk Width" (140/160/180 cm) and "Finish" (Oak/Walnut/White + custom text),
      - a no-variant attribute "Cable Management" (None/Grommets/Full Cable Tray),
      - optional products: Ergonomic Office Chair (with a Chair Colour attribute), Dual Monitor Arm,
        Under-Desk Cable Tray, LED Desk Lamp, Chair Floor Mat, and a non-purchasable "On-site Assembly"
        service (must NOT be proposed on purchase orders),
  * vendor prices for everything (per width for the desk).

Usage:  python scripts/setup_demo_data.py [--url http://localhost:8069] [--db ohs_test]
Requires a database created with demo data (--with-demo) for the product images.
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

    def image_of(demo_product_name):
        rec = call('product.template', 'search_read', [('name', '=', demo_product_name)],
                   fields=['image_1920'], limit=1)
        return rec[0]['image_1920'] if rec else False

    vendor_id = get_or_create('res.partner', [('name', '=', "Nordic Office Supply Co.")], {
        'name': "Nordic Office Supply Co.",
        'is_company': True,
        'supplier_rank': 1,
    })

    # ---- attributes ---------------------------------------------------------
    def attribute(name, create_variant, display_type, values):
        attr_id = get_or_create('product.attribute', [('name', '=', name)], {
            'name': name, 'create_variant': create_variant, 'display_type': display_type,
        })
        value_ids = []
        for value_name, is_custom in values:
            value_ids.append(get_or_create(
                'product.attribute.value',
                [('attribute_id', '=', attr_id), ('name', '=', value_name)],
                {'attribute_id': attr_id, 'name': value_name, 'is_custom': is_custom},
            ))
        return attr_id, value_ids

    width_attr, width_values = attribute("Desk Width", 'always', 'pills',
                                         [("140 cm", False), ("160 cm", False), ("180 cm", False)])
    finish_attr, finish_values = attribute("Finish", 'always', 'radio',
                                           [("Natural Oak", False), ("Walnut", False), ("White", False),
                                            ("Custom Finish", True)])
    cable_attr, cable_values = attribute("Cable Management", 'no_variant', 'radio',
                                         [("None", False), ("Grommets", False), ("Full Cable Tray", False)])
    colour_attr, colour_values = attribute("Chair Colour", 'always', 'radio',
                                           [("Black", False), ("Grey", False)])

    # ---- products -----------------------------------------------------------
    def product(name, cost, price, image=False, extra=None):
        values = {
            'name': name, 'type': 'consu', 'purchase_ok': True, 'sale_ok': True,
            'standard_price': cost, 'list_price': price,
        }
        if image:
            values['image_1920'] = image
        values.update(extra or {})
        return get_or_create('product.template', [('name', '=', name)], values)

    def ensure_attribute_lines(tmpl_id, lines):
        existing = call('product.template.attribute.line', 'search', [('product_tmpl_id', '=', tmpl_id)])
        if not existing:
            call('product.template', 'write', [tmpl_id], {
                'attribute_line_ids': [(0, 0, {'attribute_id': a, 'value_ids': [(6, 0, v)]}) for a, v in lines],
            })

    chair = product("Ergonomic Office Chair", 150, 349, image_of("Office Chair Black"),
                    {'description_purchase': "Mesh back, adjustable lumbar support"})
    ensure_attribute_lines(chair, [(colour_attr, colour_values)])
    arm = product("Dual Monitor Arm", 45, 119, image_of("Monitor Stand"))
    tray = product("Under-Desk Cable Tray", 20, 59, image_of("Cable Management Box"))
    lamp = product("LED Desk Lamp", 26, 69, image_of("Office Lamp"))
    mat = product("Chair Floor Mat", 8, 24, image_of("Chair floor protection"))
    assembly = product("On-site Assembly", 0, 90, extra={'type': 'service', 'purchase_ok': False})

    desk = product("Executive Standing Desk", 420, 899, image_of("Customizable Desk"), {
        'description_purchase': "Electric height-adjustable frame, 120 kg load, EU plug",
        'optional_product_ids': [(6, 0, [chair, arm, tray, lamp, mat, assembly])],
    })
    ensure_attribute_lines(desk, [(width_attr, width_values), (finish_attr, finish_values),
                                  (cable_attr, cable_values)])

    # ---- vendor prices ------------------------------------------------------
    def supplierinfo(tmpl_id, price, product_id=False):
        domain = [('partner_id', '=', vendor_id), ('product_tmpl_id', '=', tmpl_id),
                  ('product_id', '=', product_id)]
        get_or_create('product.supplierinfo', domain, {
            'partner_id': vendor_id, 'product_tmpl_id': tmpl_id, 'product_id': product_id,
            'price': price, 'min_qty': 1,
        })

    width_prices = {"140 cm": 480.0, "160 cm": 520.0, "180 cm": 560.0}
    variants = call('product.product', 'search_read', [('product_tmpl_id', '=', desk)],
                    fields=['id', 'display_name'])
    call('product.product', 'write', [v['id'] for v in variants], {'standard_price': 420.0})
    for variant in variants:
        for width, price in width_prices.items():
            if width in variant['display_name']:
                supplierinfo(desk, price, variant['id'])
    for tmpl_id, price in ((chair, 180.0), (arm, 52.0), (tray, 24.0), (lamp, 30.0), (mat, 9.0)):
        supplierinfo(tmpl_id, price)

    print("Vendor id:", vendor_id)
    print("Executive Standing Desk template id:", desk, "with", len(variants), "variants")
    print("Done.")


if __name__ == '__main__':
    main()
