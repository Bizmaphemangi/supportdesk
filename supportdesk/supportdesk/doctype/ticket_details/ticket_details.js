frappe.ui.form.on("Ticket Details", {

    refresh: function (frm) {
      
        if(frm.doc.status != 'Closed'){
        frm.add_custom_button(__("Close"), function() {
                frm.set_value("status", "Closed");
            });
        }
        else{
            frm.add_custom_button(__("Re-Open"), function() {
                    
                      frappe.confirm(
                      'Are you sure you want to Re-Opened the ticket?',
                      function() {              /// YES
                           frm.set_value("status", "Re-Opened");
                          ['rating', 'feedback_option', 'feedback_extra'].forEach(field => {
                              frm.set_value(field, null);
                          });
                          frm.save();
                      },
                      function() {              /// NO
                          // If user clicks 'No'
                      })
                   
                });
        }
        if (!frm.doc.ticket_timeline || frm.doc.ticket_timeline.length === 0) return;
        render_timeline_graph(frm);

    },
    validate: function(frm) {
        if (frm.doc.status === "Re-Opened") {
            ['rating', 'feedback_option', 'feedback_extra'].forEach(field => {
                frm.set_value(field, '');
            });
        }


        frappe.call({
        method: 'supportdesk.utils.support.sync_details_to_support',
        args: {
          doc: frm.doc
        },
        callback: function(r) {
          if (r.message) {
            // frappe.msgprint(__('Ticket status updated successfully.'));
            frm.reload_doc();
          } else {
            // frappe.msgprint(__('1Failed to update ticket status.'));
          }
        }
        });
        if (!frm.is_new() && frm.doc.status !== frm._previous_status){
            console.log('diff ststus!!');
            
            frm.add_child("ticket_timeline", {
                    timestamp: frappe.datetime.now_datetime(),
                    date: frappe.datetime.get_today(),
                    status: frm.doc.status,
                    notes: `Status changed from ${frm._previous_status} to ${frm.doc.status}`,
                    added_by: frappe.user_info(frappe.session.user).fullname
                });
          frappe.call({
            method: 'supportdesk.utils.support.sync_timeline_to_support_system',
            args: {
              doc: frm.doc
            },
            callback: function(r) {
              if (r.message) {
                console.log(__('Timeline entry updated successfully in support.'));
                frm.reload_doc();
              } else {
                console.log(__('Failed to update Timeline entry in support.'));
              }
            }
          });
        }
      },
    after_save: function(frm) {
        frm.reload_doc();
    },
    view_recording: function(frm) {
      frappe.db.get_value("File", {
        attached_to_doctype: frm.doctype,
        attached_to_name: frm.doc.name
      }, "file_url").then((r) => {
        if (r && r.message && r.message.file_url) {
          const file_url = r.message.file_url;
    
          let dialog = new frappe.ui.Dialog({
            title: 'View Recording',
            size: 'large', // can also be 'large' or 'extra-large'
            primary_action_label: 'Close',
            primary_action() {
              dialog.hide();
            }
          });
    
          dialog.$body.html(`
            <video width="100%" controls>
              <source src="${file_url}" type="video/mp4">
              Your browser does not support the video tag.
            </video>
          `);
    
          dialog.show();
    
        } else {
          frappe.msgprint("No video file found.");
        }
      });
    },
    
    onload: function(frm){
      frm._previous_status = frm.doc.status;

      frappe.db.get_value("File", {
        attached_to_doctype: frm.doctype,
        attached_to_name: frm.doc.name
      }, "file_url").then((r) => {
        if (r && r.message && r.message.file_url) {
          frm.set_df_property('view_recording', 'hidden', '0');
          console.log('show view button');
          
        }
      });

    //   if (frm.doc.category) {
    //     const category_key = frappe.scrub(frm.doc.category); // Converts "Doubt" -> "doubt"

    //     frm.set_query("status", function () {
    //       console.log("Category Key: ", category_key);
    //         return {
    //             filters: {
    //                 [category_key]: 1
    //             }
    //         };
    //     });
    // }
    },
    feedback_option: function(frm){        
        if(frm.doc.feedback_option){            
            frappe.db.get_value(
                "Ticket Feedback Option",
                { name: frm.doc.feedback_option },
                "rating",
                (r) => {
                    // console.log(r.rating);
                    frm.set_value("rating",r.rating);
                }
            );
        }   
    }
});
function getStatusColor(status) {
  const colors = {
      "Open": "#e74c3c",
      "Replied": "#f1c40f",
      "Resolved": "#2ecc71",
      "Closed": "#2ecc71",
      "Live": "#2ecc71",
      "Re-Opened": "#e74c3c"
  };
  return colors[status] || "#f1c40f"; // default gray
}
function render_timeline_graph(frm) {
  let timeline = frm.doc.ticket_timeline || [];

  // Sort by timestamp
  timeline.sort((a, b) => {
      return new Date(a.timestamp) - new Date(b.timestamp);
  });

  let html = `<div style="display: flex; align-items: center; flex-wrap: wrap;">`;

  timeline.forEach((row, index) => {
      const color = getStatusColor(row.status);

      // Status box
      html += `
          <div style="display: flex; flex-direction: column; align-items: center; margin: 10px;">
              <div style="padding: 6px 12px; border-radius: 20px; background-color: ${color}; color: white;">
                  ${row.status}
              </div>
              <div style="font-size: 12px; margin-top: 4px;">
                  ${frappe.datetime.str_to_user(row.timestamp.split(" ")[0])}
              </div>
              <div style="font-size: 12px; color: #888;">
                  ${row.added_by}
              </div>
          </div>
      `;

      // Arrow (except after the last one)
      if (index < timeline.length - 1) {
          html += `
          <div style="margin: 0 8px; font-size: 22px; display: flex; align-items: center; height: 100%;">➜</div>            `;
      }
  });

  html += `</div>`;
  frm.fields_dict.timeline_graph.$wrapper.html(html);
}