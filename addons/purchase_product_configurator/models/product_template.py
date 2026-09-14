# Part of the Oxygen Health Systems Odoo customizations.

from odoo import models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def get_single_product_variant_for_purchase(self):
        """Purchase counterpart of `get_single_product_variant`.

        Used by the purchase product configurator widget to decide whether the
        configurator popup must be opened.  Same result as the sale version,
        except that only *purchasable* optional products are taken into
        account.
        """
        self.ensure_one()
        res = self.get_single_product_variant()
        if res.get('product_id'):
            res['has_optional_products'] = any(
                optional_product.has_dynamic_attributes()
                or optional_product._get_possible_variants(
                    self.product_variant_id.product_template_attribute_value_ids
                )
                for optional_product in self._get_purchase_optional_products()
            )
            res.pop('is_combo', None)
        return res

    def _get_purchase_optional_products(self):
        """Optional products that may be proposed on a purchase order."""
        self.ensure_one()
        return self.optional_product_ids.filtered(
            lambda product: product.purchase_ok and product.active
        )
