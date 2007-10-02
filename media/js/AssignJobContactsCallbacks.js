/**
 * Callback functions for use when dynamically assigning contacts while
 * editing a Job's details.
 */
var AssignJobContactsCallbacks =
{
    jobContactsCallback: function(win, contacts)
    {
        var select = $("id_job_contacts");
        for (var i = 0, l = contacts.length; i < l; i++)
        {
            var option = document.createElement("option");
            option.value = contacts[i].id;
            // Workaround for IE
            option.appendChild(document.createTextNode(contacts[i].first_name + " " + contacts[i].last_name));
            option.selected = true;
            select.appendChild(option);
        }
        win.close();
    },

    primaryContactCallback: function(win, contact)
    {
        $("primary_contact_display").update(contact.first_name + " " + contact.last_name);
        $("id_primary_contact").value = contact.id;
        win.close();
    },

    billingContactCallback: function(win, contact)
    {
        $("billing_contact_display").update(contact.first_name + " " + contact.last_name);
        $("id_billing_contact").value = contact.id;
        win.close();
    }
};