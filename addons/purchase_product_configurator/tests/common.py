# Part of the Oxygen Health Systems Odoo customizations.

from odoo import Command
from odoo.tests import HttpCase


class TestPurchaseProductConfiguratorCommon(HttpCase):
    """Hyperbaric chamber test data shared by the unit, controller and tour tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.currency = cls.company.currency_id
        cls.vendor = cls.env['res.partner'].create({'name': "Chamber Manufacturer (TEST)"})
        cls.other_vendor = cls.env['res.partner'].create({'name': "Other Vendor"})

        cls.size_attribute = cls.env['product.attribute'].create({
            'name': "Chamber Size",
            'create_variant': 'always',
            'display_type': 'radio',
            'value_ids': [
                Command.create({'name': "32 inch"}),
                Command.create({'name': "40 inch"}),
            ],
        })
        cls.customization_attribute = cls.env['product.attribute'].create({
            'name': "Chamber Customization",
            'create_variant': 'no_variant',
            'display_type': 'radio',
            'value_ids': [
                Command.create({'name': "Standard"}),
                Command.create({'name': "Extra Window"}),
                Command.create({'name': "Custom", 'is_custom': True}),
            ],
        })

        cls.concentrator = cls.env['product.template'].create({
            'name': "Oxygen Concentrator (TEST)",
            'purchase_ok': True,
            'sale_ok': True,
            'standard_price': 900.0,
            'list_price': 1500.0,
        })
        cls.installation = cls.env['product.template'].create({
            'name': "Installation Service (TEST)",
            'type': 'service',
            'purchase_ok': False,
            'sale_ok': True,
            'list_price': 300.0,
        })
        cls.chamber = cls.env['product.template'].create({
            'name': "Hyperbaric Chamber (TEST)",
            'purchase_ok': True,
            'sale_ok': True,
            'standard_price': 3000.0,
            'list_price': 6000.0,
            'attribute_line_ids': [
                Command.create({
                    'attribute_id': cls.size_attribute.id,
                    'value_ids': [Command.set(cls.size_attribute.value_ids.ids)],
                }),
                Command.create({
                    'attribute_id': cls.customization_attribute.id,
                    'value_ids': [Command.set(cls.customization_attribute.value_ids.ids)],
                }),
            ],
            'optional_product_ids': [Command.set([cls.concentrator.id, cls.installation.id])],
        })
        cls.chamber_32 = cls.chamber.product_variant_ids.filtered(
            lambda variant: variant.product_template_attribute_value_ids.name == "32 inch"
        )
        cls.chamber_40 = cls.chamber.product_variant_ids.filtered(
            lambda variant: variant.product_template_attribute_value_ids.name == "40 inch"
        )
        assert cls.chamber_32 and cls.chamber_40, "Both chamber variants must exist"
        # The cost is stored per variant for multi-variant products.
        cls.chamber.product_variant_ids.write({'standard_price': 3000.0})
        cls.env['product.supplierinfo'].create([
            {
                'partner_id': cls.vendor.id,
                'product_tmpl_id': cls.chamber.id,
                'product_id': cls.chamber_32.id,
                'price': 4000.0,
                'min_qty': 1,
            }, {
                'partner_id': cls.vendor.id,
                'product_tmpl_id': cls.chamber.id,
                'product_id': cls.chamber_40.id,
                'price': 5500.0,
                'min_qty': 1,
            }, {
                'partner_id': cls.vendor.id,
                'product_tmpl_id': cls.concentrator.id,
                'price': 1000.0,
                'min_qty': 1,
            },
        ])
        cls.customization_ptals = cls.chamber.attribute_line_ids.filtered(
            lambda ptal: ptal.attribute_id == cls.customization_attribute
        )
        cls.ptav_standard = cls.customization_ptals.product_template_value_ids.filtered(
            lambda ptav: ptav.name == "Standard"
        )
        cls.ptav_extra_window = cls.customization_ptals.product_template_value_ids.filtered(
            lambda ptav: ptav.name == "Extra Window"
        )
        cls.ptav_custom = cls.customization_ptals.product_template_value_ids.filtered(
            lambda ptav: ptav.name == "Custom"
        )
