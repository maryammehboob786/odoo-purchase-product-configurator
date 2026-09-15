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
            run: "edit Desk Manufacturer (TEST)",
        },
        {
            trigger: 'ul.ui-autocomplete > li > a:contains("Desk Manufacturer (TEST)")',
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
            run: "edit Standing Desk (TEST)",
        },
        {
            trigger: 'ul.ui-autocomplete a:contains("Standing Desk (TEST)")',
            run: "click",
        },
        // The configurator popup opens: the 140 cm variant is preselected at its vendor price.
        configuratorTourUtils.assertProductPrice("Standing Desk (TEST)", "4,000.00"),
        configuratorTourUtils.selectAttribute("Standing Desk (TEST)", "Desk Width", "160 cm"),
        configuratorTourUtils.assertProductPrice("Standing Desk (TEST)", "5,500.00"),
        ...configuratorTourUtils.selectAndSetCustomAttribute(
            "Standing Desk (TEST)", "Finish", "Custom", "Pastel blue"
        ),
        configuratorTourUtils.setProductQuantity("Standing Desk (TEST)", 2),
        configuratorTourUtils.assertProductQuantity("Standing Desk (TEST)", 2),
        // Optional products: only the purchasable one is proposed, at its vendor price.
        configuratorTourUtils.assertOptionalProductPrice("Monitor Arm (TEST)", "1,000.00"),
        {
            content: "A non-purchasable optional product is not proposed",
            trigger: '.o_sale_product_configurator_dialog:not(:has(span:contains("Assembly Service (TEST)")))',
        },
        configuratorTourUtils.addOptionalProduct("Monitor Arm (TEST)"),
        ...configuratorTourUtils.saveConfigurator(),
        // Both lines are on the purchase order with the configured values.
        {
            trigger: 'tr:has(td.o_data_cell:contains("Standing Desk (TEST) (160 cm)")) td.o_data_cell:contains("2.0")',
        },
        {
            trigger: 'tr:has(td.o_data_cell:contains("Standing Desk (TEST) (160 cm)")) td.o_data_cell:contains("5,500.00")',
        },
        {
            trigger: 'tr:has(td.o_data_cell:contains("Monitor Arm (TEST)")) td.o_data_cell:contains("1,000.00")',
        },
        ...stepUtils.saveForm(),
    ],
});
