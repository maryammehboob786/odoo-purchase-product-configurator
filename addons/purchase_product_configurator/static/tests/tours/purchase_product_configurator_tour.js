import { registry } from "@web/core/registry";
import { stepUtils } from "@web_tour/tour_utils";
import configuratorTourUtils from "@sale/js/tours/product_configurator_tour_utils";

registry.category("web_tour.tours").add("purchase_product_configurator_tour", {
    url: "/odoo",
    steps: () => [
        ...stepUtils.goToAppSteps("purchase.menu_purchase_root", "Go to the Purchase App"),
        {
            content: "Create a new request for quotation",
            trigger: ".o_list_button_add",
            run: "click",
        },
        {
            content: "Select the vendor",
            trigger: ".o_field_widget[name=partner_id] input",
            run: "edit Chamber Manufacturer (TEST)",
        },
        {
            trigger: 'ul.ui-autocomplete > li > a:contains("Chamber Manufacturer (TEST)")',
            run: "click",
        },
        {
            content: "Add a product line",
            trigger: 'a:contains("Add a product")',
            run: "click",
        },
        {
            content: "Type the product in the Product column",
            trigger: 'div[name="product_template_id"] input',
            run: "edit Hyperbaric Chamber (TEST)",
        },
        {
            trigger: 'ul.ui-autocomplete a:contains("Hyperbaric Chamber (TEST)")',
            run: "click",
        },
        // The configurator popup opens: the 32 inch variant is preselected at its vendor price.
        configuratorTourUtils.assertProductPrice("Hyperbaric Chamber (TEST)", "4,000.00"),
        configuratorTourUtils.selectAttribute("Hyperbaric Chamber (TEST)", "Chamber Size", "40 inch"),
        configuratorTourUtils.assertProductPrice("Hyperbaric Chamber (TEST)", "5,500.00"),
        ...configuratorTourUtils.selectAndSetCustomAttribute(
            "Hyperbaric Chamber (TEST)", "Chamber Customization", "Custom", "Blue paint"
        ),
        configuratorTourUtils.setProductQuantity("Hyperbaric Chamber (TEST)", 2),
        configuratorTourUtils.assertProductQuantity("Hyperbaric Chamber (TEST)", 2),
        // Optional products: only the purchasable one is proposed, at its vendor price.
        configuratorTourUtils.assertOptionalProductPrice("Oxygen Concentrator (TEST)", "1,000.00"),
        {
            content: "A non-purchasable optional product is not proposed",
            trigger: '.o_sale_product_configurator_dialog:not(:has(span:contains("Installation Service (TEST)")))',
        },
        configuratorTourUtils.addOptionalProduct("Oxygen Concentrator (TEST)"),
        ...configuratorTourUtils.saveConfigurator(),
        // Both lines are on the purchase order with the configured values.
        {
            trigger: 'tr:has(td.o_data_cell:contains("Hyperbaric Chamber (TEST) (40 inch)")) td.o_data_cell:contains("2.0")',
        },
        {
            trigger: 'tr:has(td.o_data_cell:contains("Hyperbaric Chamber (TEST) (40 inch)")) td.o_data_cell:contains("5,500.00")',
        },
        {
            trigger: 'tr:has(td.o_data_cell:contains("Oxygen Concentrator (TEST)")) td.o_data_cell:contains("1,000.00")',
        },
        ...stepUtils.saveForm(),
    ],
});
