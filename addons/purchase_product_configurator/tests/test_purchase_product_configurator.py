# Part of the Oxygen Health Systems Odoo customizations.

from odoo import Command, fields
from odoo.tests import tagged

from .common import TestPurchaseProductConfiguratorCommon


@tagged('post_install', '-at_install')
class TestPurchaseProductConfigurator(TestPurchaseProductConfiguratorCommon):

    def _rpc(self, route, **params):
        params.setdefault('so_date', fields.Datetime.to_string(fields.Datetime.now()))
        params.setdefault('currency_id', self.currency.id)
        params.setdefault('company_id', self.company.id)
        return self.make_jsonrpc_request(route, params)

    # -------------------------------------------------------------------------
    # Model helpers
    # -------------------------------------------------------------------------

    def test_single_variant_info_for_purchase(self):
        """The configurator must open for configurable products and for products
        with purchasable optional products only."""
        # Configurable product: no single variant -> configurator opens.
        self.assertEqual(self.chamber.get_single_product_variant_for_purchase(), {})

        # Simple product without optional products: no popup.
        res = self.concentrator.get_single_product_variant_for_purchase()
        self.assertEqual(res['product_id'], self.concentrator.product_variant_id.id)
        self.assertFalse(res['has_optional_products'])

        # Simple product whose optional products cannot be purchased: no popup.
        kit = self.env['product.template'].create({
            'name': "Chamber Kit",
            'purchase_ok': True,
            'optional_product_ids': [Command.set([self.installation.id])],
        })
        self.assertFalse(kit.get_single_product_variant_for_purchase()['has_optional_products'])

        # Simple product with a purchasable optional product: popup.
        kit.optional_product_ids = [Command.link(self.concentrator.id)]
        self.assertTrue(kit.get_single_product_variant_for_purchase()['has_optional_products'])

    def test_description_with_custom_values(self):
        """The line description lists the chosen no-variant values and the custom text."""
        order = self.env['purchase.order'].create({'partner_id': self.vendor.id})
        line = self.env['purchase.order.line'].create({
            'order_id': order.id,
            'product_id': self.chamber_32.id,
            'product_qty': 1,
            'product_no_variant_attribute_value_ids': [Command.set(self.ptav_custom.ids)],
            'product_custom_attribute_value_ids': [Command.create({
                'custom_product_template_attribute_value_id': self.ptav_custom.id,
                'custom_value': "Blue paint",
            })],
        })
        self.assertIn("Chamber Customization: Custom: Blue paint", line.name)
        # The bare "Attribute: Value" line is replaced, not duplicated.
        self.assertEqual(line.name.count("Chamber Customization: Custom"), 1)
        self.assertEqual(line.price_unit, 4000.0, "Vendor price must be used on the line")

        # Copying the order keeps the custom values.
        copy = order.copy()
        self.assertEqual(
            copy.order_line.product_custom_attribute_value_ids.custom_value, "Blue paint"
        )

    def test_onchange_refreshes_description(self):
        """Changing the configuration on an existing line refreshes its description."""
        order = self.env['purchase.order'].create({'partner_id': self.vendor.id})
        line = self.env['purchase.order.line'].create({
            'order_id': order.id,
            'product_id': self.chamber_32.id,
            'product_qty': 1,
        })
        self.assertNotIn("Extra Window", line.name)
        line.product_no_variant_attribute_value_ids = [Command.set(self.ptav_extra_window.ids)]
        line._onchange_configurator_values()
        self.assertIn("Chamber Customization: Extra Window", line.name)

    def test_no_variant_values_cleaned_on_product_change(self):
        """No-variant values of another template are dropped when the product changes."""
        order = self.env['purchase.order'].create({'partner_id': self.vendor.id})
        line = self.env['purchase.order.line'].create({
            'order_id': order.id,
            'product_id': self.chamber_32.id,
            'product_qty': 1,
            'product_no_variant_attribute_value_ids': [Command.set(self.ptav_extra_window.ids)],
        })
        self.assertEqual(line.product_no_variant_attribute_value_ids, self.ptav_extra_window)
        line.product_id = self.concentrator.product_variant_id
        self.assertFalse(line.product_no_variant_attribute_value_ids)

    # -------------------------------------------------------------------------
    # Controller
    # -------------------------------------------------------------------------

    def test_get_values_uses_vendor_prices(self):
        self.authenticate('admin', 'admin')
        values = self._rpc(
            '/purchase/product_configurator/get_values',
            product_template_id=self.chamber.id,
            quantity=1,
            partner_id=self.vendor.id,
            ptav_ids=[],
            only_main_product=False,
        )
        main = values['products'][0]
        self.assertEqual(main['product_tmpl_id'], self.chamber.id)
        self.assertEqual(main['id'], self.chamber_32.id, "First combination is the 32 inch variant")
        self.assertEqual(main['price'], 4000.0, "Vendor price of the vendor must be shown")
        self.assertFalse(main['show_extra_price'])
        self.assertEqual(
            [ptal['attribute']['name'] for ptal in main['attribute_lines']],
            ["Chamber Size", "Chamber Customization"],
        )
        self.assertTrue(all(
            ptav['price_extra'] == 0.0
            for ptal in main['attribute_lines'] for ptav in ptal['attribute_values']
        ))
        self.assertEqual(values['currency_id'], self.currency.id)

        # Only the purchasable optional product is proposed, at its vendor price.
        self.assertEqual(
            [p['display_name'] for p in values['optional_products']],
            ["Oxygen Concentrator (TEST)"],
        )
        self.assertEqual(values['optional_products'][0]['price'], 1000.0)
        self.assertEqual(values['optional_products'][0]['parent_product_tmpl_id'], self.chamber.id)

    def test_update_combination_and_fallback_to_cost(self):
        self.authenticate('admin', 'admin')
        ptav_40 = self.chamber_40.product_template_attribute_value_ids
        values = self._rpc(
            '/purchase/product_configurator/update_combination',
            product_template_id=self.chamber.id,
            ptav_ids=(ptav_40 + self.ptav_standard).ids,
            quantity=1,
            partner_id=self.vendor.id,
        )
        self.assertEqual(values['id'], self.chamber_40.id)
        self.assertEqual(values['price'], 5500.0)

        # A vendor without pricelist for the product: fall back to the product cost.
        values = self._rpc(
            '/purchase/product_configurator/update_combination',
            product_template_id=self.chamber.id,
            ptav_ids=(ptav_40 + self.ptav_standard).ids,
            quantity=1,
            partner_id=self.other_vendor.id,
        )
        self.assertEqual(values['price'], 3000.0)

    def test_get_optional_products(self):
        self.authenticate('admin', 'admin')
        values = self._rpc(
            '/purchase/product_configurator/get_optional_products',
            product_template_id=self.chamber.id,
            ptav_ids=[],
            parent_ptav_ids=[],
            partner_id=self.vendor.id,
        )
        self.assertEqual([p['display_name'] for p in values], ["Oxygen Concentrator (TEST)"])
        self.assertEqual(values[0]['price'], 1000.0)
