# Part of purchase_product_configurator. See LICENSE file for full copyright and licensing details.
{
    'name': "Purchase Product Configurator",
    'summary': "Configure products and add optional products on purchase orders, "
               "exactly like on sales orders.",
    'description': """
Purchase Product Configurator
=============================

Brings the sales *product configurator* popup to purchase orders.

When a product is added to a purchase order line, the same popup that Sales
shows is opened so the buyer can:

* pick the product attributes (variants, "no variant" options and custom
  text values, e.g. a custom finish),
* tick the *optional products* linked to the main product (e.g. the add-ons
  of a configurable desk), which are added as extra purchase order lines.

Prices shown in the popup are the vendor prices (vendor pricelists), falling
back to the product cost.  Only products that can be purchased are proposed
as optional products.
    """,
    'category': 'Supply Chain/Purchase',
    'version': '19.0.1.0.0',
    'author': 'Maryam Mehboob',
    'license': 'LGPL-3',
    'depends': ['purchase', 'sale'],
    'data': [
        'views/purchase_order_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'purchase_product_configurator/static/src/js/**/*',
        ],
        'web.assets_tests': [
            'purchase_product_configurator/static/tests/tours/**/*',
        ],
    },
    'installable': True,
    'application': False,
}
