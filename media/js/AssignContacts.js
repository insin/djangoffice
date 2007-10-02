String.prototype.startsWithIgnoreCase = function(str)
{
    return this.toLowerCase().indexOf(str.toLowerCase()) == 0;
};

var AssignContacts =
{
    init: function(contacts, options)
    {
        this.contacts = contacts;
        this.options = Object.extend(
        {
            filterForm: "filterForm",
            contactTableBodyId: "contacts",
            selectedContactTableBodyId: "selectedContactTableBody",
            contactForm: "contactForm",
            mode: "multiple"
        }, options || {});

        // Register event handlers
        Event.observe(this.options.filterForm, "submit", this.filterFormHandler.bindAsEventListener(this));
        Event.observe("filterButton", "click", this.filterFormHandler.bindAsEventListener(this));
        Event.observe("selectContacts", "click", this.selectContactsHandler.bindAsEventListener(this));
        Event.observe("cancelButton", "click", this.cancelHandler.bindAsEventListener(this));

        if (this.options.mode == "multiple")
        {
            Event.observe("assignSelectedContacts", "click", this.assignSelectedContactsHandler.bindAsEventListener(this));
        }

        var letters = "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z".split(" ");
        for (var i = 0, l = letters.length; i < l; i++)
        {
            Event.observe("letter" + letters[i],
                          "click",
                          this.filterContactsByLetter(letters[i]).bind(this));
        }
    },

    cancelHandler: function(e)
    {
        window.close();
    },

    filterFormHandler: function(e)
    {
        Event.stop(e);
        var form = document.forms[this.options.filterForm];
        var property = form.elements["property"].value;
        var criteria = form.elements["criteria"].value;
        var contactsToShow = this.filterContactsByField(property, criteria);
        this.displayContacts(contactsToShow);
    },

    /**
     * If in multiple mode, adds the selected contacts to the list of selected
     * contacts, otherwise replaces the selected contact.
     */
    selectContactsHandler: function(e)
    {
        Event.stop(e);

        var form = document.forms[this.options.contactForm];
        var boxes = form.elements["contacts"];

        if (typeof(boxes) == "undefined")
        {
            alert("There are no Contacts to select.");
            return;
        }

        var boxLookup = {};
        var contactSelected = false;
        if (typeof(boxes.length) == "number")
        {
            for (var i = 0, l = boxes.length; i < l; i++)
            {
                if (boxes[i].checked == true)
                {
                    boxLookup[boxes[i].value] = true;
                    contactSelected = true;
                }
            }
        }
        else
        {
            if (boxes.checked == true)
            {
                boxLookup[boxes.value] = true;
                contactSelected = true;
            }
        }

        if (!contactSelected)
        {
            alert("You have not selected any Contacts.");
            return;
        }

        for (var i = 0, l = this.contacts.length; i < l; i++)
        {
            if (boxLookup[this.contacts[i].id] == true)
            {
                this.contacts[i].selected = true;
            }
        }

        if (this.options.mode == "multiple")
        {
            this.displaySelectedContacts();
        }
        else
        {
            this.assignSelectedContactsHandler(e);
        }
    },

    assignSelectedContactsHandler: function(e)
    {
        if (!confirm("Are you sure you want to assign " +
                     (this.options.mode == "single" ? "this Contact?" : "these Contacts?")))
        {
            return;
        }

        var selectedContacts = [];
        for (var i = 0, l = this.contacts.length; i < l; i++)
        {
            if (this.contacts[i].selected == true)
            {
                selectedContacts.push(this.contacts[i]);
            }
        }

        if (mode == "single")
        {
            opener.assignContactsCallback(window, selectedContacts[0]);
        }
        else
        {
            opener.assignContactsCallback(window, selectedContacts);
        }
    },

    filterContactsByLetter: function(letter)
    {
        return function()
        {
            var contactsToShow = [];
            for (var i = 0, l = this.contacts.length; i < l; i++)
            {
                if (this.contacts[i].last_name.startsWithIgnoreCase(letter))
                {
                    contactsToShow.push(this.contacts[i]);
                }
            }
            this.displayContacts(contactsToShow);
        };
    },

    /**
     * Retrieves contacts for which a given property matches a given value in a
     * case-insensitive manner.
     */
    filterContactsByField: function(property, value)
    {
        var contactsToShow = [];
        var searchValue = value.toLowerCase();
        for (var i = 0, l = this.contacts.length; i < l; i++)
        {
            var p = this.contacts[i][property];
            if (p != undefined && p != null && p.toLowerCase().indexOf(searchValue) != -1)
            {
                contactsToShow.push(this.contacts[i]);
            }
        }
        return contactsToShow;
    },

    /**
     * Displays the given contacts.
     */
    displayContacts: function(contacts)
    {
        var contactTable = $(this.options.contactTableBodyId);
        Element.removeChildNodes(contactTable);
        for (var i = 0, l = contacts.length; i < l; i++)
        {
            if (!contacts[i].selected)
            {
                var row = this.contactToRow(contacts[i]);
                row.className = i % 2 == 0 ? "odd" : "even";
                contactTable.appendChild(row);
            }
        }
    },

    /**
     * Creates a table row representing the given contact.
     */
    contactToRow: function(contact)
    {
        var inputType = this.options.mode == "multiple" ? "checkbox" : "radio";
        return TR(
            TD(INPUT({"type": inputType, "name": "contacts", "value": contact.id})),
            TD((contact.last_name || "") + (contact.first_name != "" ? ", " + (contact.first_name || "") : "")),
            TD(contact.company_name || ""),
            TD(contact.position || "")
        );
    },

    displaySelectedContacts: function()
    {
        Element.removeChildNodes(this.options.selectedContactTableBodyId);
        var selectedTable = $(this.options.selectedContactTableBodyId);
        var selectedContactCount = 0;
        for (var i = 0, l = this.contacts.length; i < l; i++)
        {
            var contact = this.contacts[i];
            if (contact.selected == true)
            {
                var row = TR({"class": (selectedContactCount++ % 2 == 0 ? "odd" : "even")},
                    TD(IMG({"style": "cursor: pointer;", "src": mediaURL + "img/delete.png", "alt": "Deselect", "title": "Deselect Contact", "onclick": this.deselectContactHandler(contact.id).bind(this)})),
                    TD((contact.last_name || "") + (contact.first_name != "" ? ", " + (contact.first_name || "") : "")),
                    TD(contact.company_name || ""),
                    TD(contact.position || "")
                );
                selectedTable.appendChild(row);
            }
        }
    },

    deselectContact: function(id)
    {
        for (var i = 0, l = this.contacts.length; i < l; i++)
        {
            if (this.contacts[i].id == id)
            {
                this.contacts[i].selected = false;
                break;
            }
        }
        this.displaySelectedContacts();
    },

    deselectContactHandler: function(id)
    {
        return function()
        {
            this.deselectContact(id);
        }
    }
};