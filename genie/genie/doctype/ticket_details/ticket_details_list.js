frappe.listview_settings['Ticket Details'] = {
    onload: function(listview) {
        listview.page.add_inner_button('Raise Ticket', () => {
            new genie.SupportTicket();  // or your desired Doctype
        });

        $('[data-label="Add Ticket Details"]').hide();
    }
};
