# Part of the Oxygen Health Systems Odoo customizations.

from odoo.tests import tagged

from .common import TestPurchaseProductConfiguratorCommon


@tagged('post_install', '-at_install')
class TestPurchaseProductConfiguratorUi(TestPurchaseProductConfiguratorCommon):

    def test_purchase_product_configurator_tour(self):
        """Create a purchase order through the UI: the configurator popup must
        open, apply the configuration and add the optional product."""
        self.start_tour('/odoo', 'purchase_product_configurator_tour', login='admin')

        order = self.env['purchase.order'].search(
            [('partner_id', '=', self.vendor.id)], order='id desc', limit=1
        )
        self.assertTrue(order, "The tour must have created a purchase order")
        self.assertEqual(len(order.order_line), 2)
        chamber_line, concentrator_line = order.order_line.sorted('sequence')

        self.assertEqual(chamber_line.product_id, self.chamber_40)
        self.assertEqual(chamber_line.product_qty, 2)
        self.assertEqual(chamber_line.price_unit, 5500.0)
        self.assertEqual(chamber_line.product_no_variant_attribute_value_ids, self.ptav_custom)
        self.assertEqual(chamber_line.product_custom_attribute_value_ids.custom_value, "Blue paint")
        self.assertIn("Chamber Customization: Custom: Blue paint", chamber_line.name)

        self.assertEqual(concentrator_line.product_id, self.concentrator.product_variant_id)
        self.assertEqual(concentrator_line.product_qty, 1)
        self.assertEqual(concentrator_line.price_unit, 1000.0)
