# Part of purchase_product_configurator. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductAttributeCustomValue(models.Model):
    _inherit = 'product.attribute.custom.value'

    purchase_order_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        string="Purchase Order Line",
        index='btree_not_null',
        ondelete='cascade',
    )

    _pol_custom_value_unique = models.Constraint(
        'unique(custom_product_template_attribute_value_id, purchase_order_line_id)',
        'Only one Custom Value is allowed per Attribute Value per Purchase Order Line.',
    )
