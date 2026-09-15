# Part of purchase_product_configurator. See LICENSE file for full copyright and licensing details.

from odoo import Command
from odoo.tests import HttpCase


class TestPurchaseProductConfiguratorCommon(HttpCase):
    """Configurable desk test data shared by the unit, controller and tour tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.currency = cls.company.currency_id
        cls.vendor = cls.env['res.partner'].create({'name': "Desk Manufacturer (TEST)"})
        cls.other_vendor = cls.env['res.partner'].create({'name': "Other Vendor"})

        cls.width_attribute = cls.env['product.attribute'].create({
            'name': "Desk Width",
            'create_variant': 'always',
            'display_type': 'radio',
            'value_ids': [
                Command.create({'name': "140 cm"}),
                Command.create({'name': "160 cm"}),
            ],
        })
        cls.finish_attribute = cls.env['product.attribute'].create({
            'name': "Finish",
            'create_variant': 'no_variant',
            'display_type': 'radio',
            'value_ids': [
                Command.create({'name': "Standard"}),
                Command.create({'name': "Walnut"}),
                Command.create({'name': "Custom", 'is_custom': True}),
            ],
        })

        cls.monitor_arm = cls.env['product.template'].create({
            'name': "Monitor Arm (TEST)",
            'purchase_ok': True,
            'sale_ok': True,
            'standard_price': 900.0,
            'list_price': 1500.0,
        })
        cls.assembly = cls.env['product.template'].create({
            'name': "Assembly Service (TEST)",
            'type': 'service',
            'purchase_ok': False,
            'sale_ok': True,
            'list_price': 300.0,
        })
        cls.desk = cls.env['product.template'].create({
            'name': "Standing Desk (TEST)",
            'purchase_ok': True,
            'sale_ok': True,
            'standard_price': 3000.0,
            'list_price': 6000.0,
            'attribute_line_ids': [
                Command.create({
                    'attribute_id': cls.width_attribute.id,
                    'value_ids': [Command.set(cls.width_attribute.value_ids.ids)],
                }),
                Command.create({
                    'attribute_id': cls.finish_attribute.id,
                    'value_ids': [Command.set(cls.finish_attribute.value_ids.ids)],
                }),
            ],
            'optional_product_ids': [Command.set([cls.monitor_arm.id, cls.assembly.id])],
        })
        cls.desk_140 = cls.desk.product_variant_ids.filtered(
            lambda variant: variant.product_template_attribute_value_ids.name == "140 cm"
        )
        cls.desk_160 = cls.desk.product_variant_ids.filtered(
            lambda variant: variant.product_template_attribute_value_ids.name == "160 cm"
        )
        assert cls.desk_140 and cls.desk_160, "Both desk variants must exist"
        # The cost is stored per variant for multi-variant products.
        cls.desk.product_variant_ids.write({'standard_price': 3000.0})
        cls.env['product.supplierinfo'].create([
            {
                'partner_id': cls.vendor.id,
                'product_tmpl_id': cls.desk.id,
                'product_id': cls.desk_140.id,
                'price': 4000.0,
                'min_qty': 1,
            }, {
                'partner_id': cls.vendor.id,
                'product_tmpl_id': cls.desk.id,
                'product_id': cls.desk_160.id,
                'price': 5500.0,
                'min_qty': 1,
            }, {
                'partner_id': cls.vendor.id,
                'product_tmpl_id': cls.monitor_arm.id,
                'price': 1000.0,
                'min_qty': 1,
            },
        ])
        cls.finish_ptals = cls.desk.attribute_line_ids.filtered(
            lambda ptal: ptal.attribute_id == cls.finish_attribute
        )
        cls.ptav_standard = cls.finish_ptals.product_template_value_ids.filtered(
            lambda ptav: ptav.name == "Standard"
        )
        cls.ptav_walnut = cls.finish_ptals.product_template_value_ids.filtered(
            lambda ptav: ptav.name == "Walnut"
        )
        cls.ptav_custom = cls.finish_ptals.product_template_value_ids.filtered(
            lambda ptav: ptav.name == "Custom"
        )
