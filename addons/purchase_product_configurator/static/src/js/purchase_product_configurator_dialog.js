import { ProductConfiguratorDialog } from "@sale/js/product_configurator_dialog/product_configurator_dialog";

/**
 * Product configurator popup for purchase orders.
 *
 * Reuses the whole sale configurator UI (attribute lines, custom values,
 * optional products, quantities, packaging) but fetches its data from the
 * purchase controller, which returns vendor prices instead of pricelist prices
 * and only proposes purchasable optional products.
 */
export class PurchaseProductConfiguratorDialog extends ProductConfiguratorDialog {
    static props = {
        ...ProductConfiguratorDialog.props,
        partnerId: { type: Number, optional: true },
    };

    setup() {
        super.setup();
        this.getValuesUrl = "/purchase/product_configurator/get_values";
        this.createProductUrl = "/purchase/product_configurator/create_product";
        this.updateCombinationUrl = "/purchase/product_configurator/update_combination";
        this.getOptionalProductsUrl = "/purchase/product_configurator/get_optional_products";
    }

    /**
     * Send the vendor along with every RPC so that vendor prices can be computed.
     *
     * @override
     */
    _getAdditionalRpcParams() {
        return {
            ...super._getAdditionalRpcParams(),
            partner_id: this.props.partnerId,
        };
    }
}
