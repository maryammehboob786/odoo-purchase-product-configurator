# Part of the Oxygen Health Systems Odoo customizations.

from odoo import api, fields, models
from odoo.tools import get_lang


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_template_id = fields.Many2one(
        comodel_name='product.template',
        string="Product Template",
        compute='_compute_product_template_id',
        readonly=False,
        search='_search_product_template_id',
        # Same "editable but not stored" setup as sale.order.line: the widget
        # sets `product_id` itself once the configurator popup is confirmed.
        domain=[('purchase_ok', '=', True)],
    )
    is_configurable_product = fields.Boolean(
        string="Is the product configurable?",
        related='product_template_id.has_configurable_attributes',
        depends=['product_template_id'],
    )
    product_custom_attribute_value_ids = fields.One2many(
        comodel_name='product.attribute.custom.value',
        inverse_name='purchase_order_line_id',
        string="Custom Values",
        compute='_compute_custom_attribute_values',
        store=True, readonly=False, precompute=True, copy=True,
    )
    # Field defined in `purchase`; make it self-cleaning when the product changes.
    product_no_variant_attribute_value_ids = fields.Many2many(
        compute='_compute_no_variant_attribute_values',
        store=True, readonly=False, precompute=True,
    )

    # -------------------------------------------------------------------------
    # Computes
    # -------------------------------------------------------------------------

    @api.depends('product_id')
    def _compute_product_template_id(self):
        for line in self:
            line.product_template_id = line.product_id.product_tmpl_id

    def _search_product_template_id(self, operator, value):
        return [('product_id.product_tmpl_id', operator, value)]

    @api.depends('product_id')
    def _compute_custom_attribute_values(self):
        for line in self:
            if not line.product_id:
                line.product_custom_attribute_value_ids = False
                continue
            if not line.product_custom_attribute_value_ids:
                continue
            valid_values = line.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
            # remove the custom values that do not belong to this template
            for pacv in line.product_custom_attribute_value_ids:
                if pacv.custom_product_template_attribute_value_id not in valid_values:
                    line.product_custom_attribute_value_ids -= pacv

    @api.depends('product_id')
    def _compute_no_variant_attribute_values(self):
        for line in self:
            if not line.product_id:
                line.product_no_variant_attribute_value_ids = False
                continue
            if not line.product_no_variant_attribute_value_ids:
                continue
            valid_values = line.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
            # remove the no_variant attribute values that do not belong to this template
            for ptav in line.product_no_variant_attribute_value_ids:
                if ptav._origin not in valid_values:
                    line.product_no_variant_attribute_value_ids -= ptav

    # -------------------------------------------------------------------------
    # Onchange
    # -------------------------------------------------------------------------

    @api.onchange('product_no_variant_attribute_value_ids', 'product_custom_attribute_value_ids')
    def _onchange_configurator_values(self):
        """Refresh the description when the configuration chosen in the
        configurator popup changes (the standard purchase description is only
        generated when the product itself changes)."""
        for line in self:
            if not line.product_id or line.display_type:
                continue
            product_lang = line.product_id.with_context(
                lang=get_lang(self.env, line.partner_id.lang).code,
                partner_id=None,
                company_id=line.company_id.id,
            )
            line.name = line._get_product_purchase_description(product_lang)

    # -------------------------------------------------------------------------
    # Business methods
    # -------------------------------------------------------------------------

    def _get_product_purchase_description(self, product_lang):
        """Append the custom attribute values (e.g. a free-text customization)
        to the standard purchase description.

        The standard description already lists the "no variant" attribute
        values as ``Attribute: Value``; for a value that carries a custom text
        that line is replaced by ``Attribute: Value: custom text``.
        """
        name = super()._get_product_purchase_description(product_lang)
        custom_values = self.product_custom_attribute_value_ids
        if not custom_values:
            return name
        lines = name.split('\n')
        sorted_custom_ptavs = custom_values.custom_product_template_attribute_value_id.sorted()
        for ptav in sorted_custom_ptavs:
            pacv = custom_values.filtered(
                lambda pcav: pcav.custom_product_template_attribute_value_id == ptav
            )[:1]
            ptav_lang = ptav.with_context(product_lang.env.context)
            duplicate = f"{ptav_lang.attribute_id.name}: {ptav_lang.name}"
            if duplicate in lines:
                lines.remove(duplicate)
            lines.append(pacv.display_name)
        return '\n'.join(lines)
