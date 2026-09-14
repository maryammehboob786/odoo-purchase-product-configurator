import {
    ProductLabelSectionAndNoteField,
    productLabelSectionAndNoteField,
} from "@account/components/product_label_section_and_note_field/product_label_section_and_note_field";
import { useEffect } from "@odoo/owl";
import { serializeDateTime } from "@web/core/l10n/dates";
import { _t } from "@web/core/l10n/translation";
import { x2ManyCommands } from "@web/core/orm_service";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { getSelectedCustomPtav } from "@sale/js/sale_utils";
import { PurchaseProductConfiguratorDialog } from "./purchase_product_configurator_dialog";

const { DateTime } = luxon;

/**
 * Apply a product configured in the popup on a purchase order line.
 *
 * The product is set first and the configuration second, in two separate
 * updates: the purchase `onchange_product_id` resets the quantity, the unit
 * price and the description, so it must run before the values chosen in the
 * popup are written.
 *
 * @param {Record} record The purchase order line record.
 * @param {Object} product The configured product returned by the popup.
 */
async function applyProduct(record, product) {
    // handle custom values & no variants
    const customAttributesCommands = [
        x2ManyCommands.set([]), // Command.clear isn't supported in static_list/_applyCommands
    ];
    for (const ptal of product.attribute_lines) {
        const selectedCustomPTAV = getSelectedCustomPtav(ptal);
        if (selectedCustomPTAV) {
            customAttributesCommands.push(
                x2ManyCommands.create(undefined, {
                    custom_product_template_attribute_value_id: [
                        selectedCustomPTAV.id,
                        "we don't care",
                    ],
                    custom_value: ptal.customValue,
                })
            );
        }
    }

    const noVariantPTAVIds = product.attribute_lines
        .filter((ptal) => ptal.create_variant === "no_variant")
        .flatMap((ptal) => ptal.selected_attribute_value_ids);

    // We use `_update` (not locked) instead of `update` (locked) so that multiple records can be
    // updated in parallel (for performance).
    const currentProduct = record.data.product_id;
    if (!currentProduct || currentProduct.id !== product.id) {
        await record._update({
            product_id: { id: product.id, display_name: product.display_name },
        });
    }
    const values = {
        product_qty: product.quantity,
        product_no_variant_attribute_value_ids: [x2ManyCommands.set(noVariantPTAVIds)],
        product_custom_attribute_value_ids: customAttributesCommands,
    };
    if (product.uom) {
        // only update uom field if uom are enabled (uom_data provided), otherwise we don't have the
        // display_name and the value isn't expected to change anyway.
        values.product_uom_id = product.uom;
    }
    await record._update(values);
}

export class PurchaseOrderLineProductField extends ProductLabelSectionAndNoteField {
    static template = "purchase_product_configurator.PurchaseProductField";
    static props = {
        ...super.props,
        readonlyField: { type: Boolean, optional: true },
    };

    setup() {
        super.setup();
        this.dialog = useService("dialog");
        this.orm = useService("orm");
        this.isInternalUpdate = false;
        let isMounted = false;
        useEffect(
            (value) => {
                if (!isMounted) {
                    isMounted = true;
                } else if (value && this.isInternalUpdate && this.relation === "product.template") {
                    // we don't want to trigger product update when update comes from an external
                    // source, such as an onchange, or the product configuration dialog itself
                    this._onProductTemplateUpdate();
                }
                this.isInternalUpdate = false;
            },
            () => [this.value && this.value.id]
        );
    }

    get productName() {
        if (this.props.name == "product_template_id") {
            const product_id_data = this.props.record.data.product_id;
            if (product_id_data && product_id_data.display_name) {
                return product_id_data.display_name.split("\n")[0];
            }
        }
        return super.productName;
    }

    get isProductClickable() {
        // product form should be accessible if the widget field is readonly
        // or if the line cannot be edited (e.g. confirmed/locked PO)
        return (
            this.props.readonlyField ||
            (this.props.record.model.root.activeFields.order_line &&
                this.props.record.model.root._isReadonly("order_line"))
        );
    }

    get hasConfigurationButton() {
        return this.isConfigurableTemplate;
    }

    get isConfigurableTemplate() {
        return this.props.record.data.is_configurable_product;
    }

    get isDownpayment() {
        return this.props.record.data.is_downpayment;
    }

    get configurationButtonHelp() {
        return _t("Edit Configuration");
    }

    /**
     * @override
     */
    get sectionAndNoteClasses() {
        return {
            ...super.sectionAndNoteClasses,
            "text-warning":
                !this.isSectionOrSubSection &&
                !this.isNote() &&
                !this.productName &&
                !this.isDownpayment,
        };
    }

    get label() {
        let label = this.props.record.data.name;
        if (this.translatedProductName && label.startsWith(this.translatedProductName)) {
            // Remove the translated name as it is already shown to the buyer on the line.
            label = label.slice(this.translatedProductName.length + 1); // + "\n"
        } else {
            label = super.label;
        }
        return label;
    }

    get translatedProductName() {
        return this.props.record.data.translated_product_name;
    }

    parseLabel(value) {
        if (!this.translatedProductName) {
            return super.parseLabel(value);
        }
        return (value && this.translatedProductName.concat("\n", value)) || this.translatedProductName;
    }

    get m2oProps() {
        const p = super.m2oProps;
        return {
            ...p,
            canOpen: this.props.canOpen && (!this.props.readonly || this.isProductClickable),
            update: (value) => {
                this.isInternalUpdate = true;
                return p.update(value);
            },
        };
    }

    get relation() {
        return this.props.record.fields[this.props.name].relation;
    }

    get value() {
        return this.props.record.data[this.props.name];
    }

    async _onProductTemplateUpdate() {
        const result = await this.orm.call(
            "product.template",
            "get_single_product_variant_for_purchase",
            [this.props.record.data.product_template_id.id]
        );
        if (result && result.product_id) {
            const currentProduct = this.props.record.data.product_id;
            if (!currentProduct || currentProduct.id !== result.product_id) {
                if (result.has_optional_products) {
                    this._openProductConfigurator();
                } else {
                    await this.props.record.update({
                        product_id: { id: result.product_id, display_name: result.product_name },
                    });
                }
            }
        } else {
            this._openProductConfigurator();
        }
    }

    onEditConfiguration() {
        if (this.isConfigurableTemplate) {
            this._openProductConfigurator(true);
        }
    }

    async _openProductConfigurator(edit = false) {
        const purchaseOrderRecord = this.props.record.model.root;
        const purchaseOrder = purchaseOrderRecord.data;
        const purchaseOrderLine = this.props.record.data;
        const ptavIds = [...this._getVariantPtavIds(purchaseOrderLine)];
        let customPtavs = [];

        if (edit) {
            /**
             * no_variant and custom attribute don't need to be given to the configurator for new
             * products.
             */
            ptavIds.push(...this._getNoVariantPtavIds(purchaseOrderLine));
            customPtavs = await this._getCustomPtavs(purchaseOrderLine);
        }

        const orderDate = purchaseOrder.date_order || DateTime.now();

        this.dialog.add(PurchaseProductConfiguratorDialog, {
            productTemplateId: purchaseOrderLine.product_template_id.id,
            ptavIds: ptavIds,
            customPtavs: customPtavs,
            quantity: purchaseOrderLine.product_qty || 1,
            productUOMId: purchaseOrderLine.product_uom_id
                ? purchaseOrderLine.product_uom_id.id
                : undefined,
            companyId: purchaseOrder.company_id ? purchaseOrder.company_id.id : undefined,
            partnerId: purchaseOrder.partner_id ? purchaseOrder.partner_id.id : undefined,
            currencyId: purchaseOrderLine.currency_id ? purchaseOrderLine.currency_id.id : undefined,
            soDate: serializeDateTime(orderDate),
            edit: edit,
            save: async (mainProduct, optionalProducts) => {
                const proms = [applyProduct(this.props.record, mainProduct)];

                for (const [i, product] of optionalProducts.entries()) {
                    // New lines are inserted right after the main product line, in order.
                    const index =
                        purchaseOrder.order_line.records.indexOf(this.props.record) + i;
                    const line = await purchaseOrder.order_line.addNewRecordAtIndex(index, {
                        mode: "readonly",
                    });
                    proms.push(applyProduct(line, product));
                }

                await Promise.all(proms);
                purchaseOrder.order_line.leaveEditMode();
            },
            discard: () => {
                purchaseOrder.order_line.delete(this.props.record);
            },
        });
    }

    /**
     * Return the PTAV ids of the provided purchase order line.
     *
     * @param purchaseOrderLine The purchase order line
     * @return {Number[]} The purchase order line's PTAV ids.
     */
    _getVariantPtavIds(purchaseOrderLine) {
        return purchaseOrderLine.product_template_attribute_value_ids.currentIds;
    }

    /**
     * Return the `no_variant` PTAV ids of the provided purchase order line.
     *
     * @param purchaseOrderLine The purchase order line
     * @return {Number[]} The purchase order line's `no_variant` PTAV ids.
     */
    _getNoVariantPtavIds(purchaseOrderLine) {
        return purchaseOrderLine.product_no_variant_attribute_value_ids.currentIds;
    }

    /**
     * Return the custom PTAVs of the provided purchase order line.
     *
     * @param purchaseOrderLine The purchase order line
     * @return {Promise<CustomPtav[]>} The purchase order line's custom PTAVs.
     */
    async _getCustomPtavs(purchaseOrderLine) {
        // `product.attribute.custom.value` records are not loaded in the view because sub templates
        // are not loaded in list views. Therefore, we fetch them from the server if the record was
        // saved. Otherwise, we use the value stored on the line.
        const customPtavIds = purchaseOrderLine.product_custom_attribute_value_ids;
        let customPtavs = [];
        if (customPtavIds.records[0]?.isNew) {
            customPtavs = customPtavIds.records.map((record) => record.data);
        } else if (customPtavIds.currentIds.length) {
            const specification = {
                custom_product_template_attribute_value_id: {
                    fields: { id: {} },
                },
                custom_value: {},
            };
            customPtavs = await this.orm.webRead(
                "product.attribute.custom.value",
                customPtavIds.currentIds,
                { specification }
            );
        }
        return customPtavs.map((customPtav) => ({
            id:
                customPtav.custom_product_template_attribute_value_id &&
                customPtav.custom_product_template_attribute_value_id.id,
            value: customPtav.custom_value,
        }));
    }
}

export const purchaseOrderLineProductField = {
    ...productLabelSectionAndNoteField,
    component: PurchaseOrderLineProductField,
    extractProps(fieldInfo, dynamicInfo) {
        return {
            ...productLabelSectionAndNoteField.extractProps(fieldInfo, dynamicInfo),
            readonlyField: dynamicInfo.readonly,
        };
    },
    // `translated_product_name` is deliberately not declared as a dependency: it does not exist on
    // purchase order lines in every Odoo 19 build (e.g. Enterprise 19.0-20260105), and the label
    // getters above fall back to the standard behaviour when it is absent from the record.
    fieldDependencies: [
        { name: "is_configurable_product", type: "boolean" },
        { name: "product_template_attribute_value_ids", type: "many2many" },
    ],
};

registry
    .category("fields")
    .add("purchase_configurator_product_many2one", purchaseOrderLineProductField);
