/*
Copyright (c) 2006 Dan Webb

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial
portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
*/

/*
Modified by Jonathan Buchanan.
*/

DomBuilder =
{
    /**
     * IE is broken in numerous ways which, unfortunately, require browser
     * detection to fix.
     */
    isIE: false,

    /** Translations for attribute names which IE would otherwise choke on. */
    IE_TRANSLATIONS: {
        "class": "className",
        "for": "htmlFor"
    },

    /**
     * Deals with special cases related to setting attribute values in IE.
     */
    ieSetAttribute:function(el, name, value)
    {
        if (typeof(this.IE_TRANSLATIONS[name]) == "string")
        {
            el[this.IE_TRANSLATIONS[name]] = value;
        }
        else if (name == "style")
        {
            el.style.cssText = value;
        }
        else
        {
            el.setAttribute(name, value);
        }
    },

    /**
     * Sets up element creation functions in the given context object.
     */
    apply : function(context)
    {
        context = context || {};
        var tagNames =
           ("p div span strong em img table tr td th thead tbody tfoot " +
            "pre code h1 h2 h3 h4 h5 h6 ul ol li form input textarea legend " +
            "fieldset select option blockquote cite br hr dd dl dt address a " +
            "button abbr acronym script link style bdo ins del object param " +
            "col colgroup optgroup caption label dfn kbd samp var").split(" ");
        for (var i = 0, tagName; tagName = tagNames[i]; i++)
        {
            context[tagName.toUpperCase()] =
                DomBuilder.createElementFunction(tagName);
        }
        return context;
    },

    parseCreateElementArgs: function(args)
    {
        var attributes = {};
        var children = [];

        // List of children
        if (args.length == 1 &&
            args[0] && args[0].constructor == Array)
        {
            children = args[0];
        }
        // Properties and list of children
        else if (args.length == 2 &&
                 args[0] && args[0].constructor == Object &&
                 args[1] && args[1].constructor == Array)
        {
            attributes = args[0];
            children = args[1];
        }
        // If the first argument is not a property object, assume all
        // arguments are children.
        else if (args[0] && (args[0].nodeName ||
                             typeof(args[0]) == "string" ||
                             typeof(args[0]) == "number"))
        {
            children = args;
        }
        // Default - assume the first argument is a property object
        // and all remaining arguments are children.
        else
        {
            attributes = args[0];
            // The arguments object is not an Array - it doesn't have the
            // slice method.
            children = [].slice.call(args, 1);
        }

        return [attributes, children];
    },

    /**
     * Creates an element creation function for the given tagName.
     */
    createElementFunction: function(tagName)
    {
        return function()
        {
            if (arguments.length == 0)
            {
                return DomBuilder.createElement(tagName);
            }
            else
            {
                var args = DomBuilder.parseCreateElementArgs(arguments);
                return DomBuilder.createElement(tagName, args[0], args[1]);
            }
        };
    },

    /**
     * Creates an element with the given attributes and children.
     */
    createElement: function(tagName, attributes, children)
    {
        attributes = attributes || {};
        children = children || [];

        // Create the element itself
        if (this.isIE && typeof(attributes.name) == "string")
        {
            // Name is not updateable in IE
            var el = document.createElement("<" + tagName +
                                            " name=" + attributes.name + ">");
        }
        else
        {
            var el = document.createElement(tagName);
        }

        // Add attributes
        for (var attr in attributes)
        {
            // Guard against additions to Object.prototype
            if (attributes.hasOwnProperty(attr) &&
                attributes[attr] != undefined &&
                attributes[attr] != null)
            {
                if (attr.match(/^on/i) && typeof(attributes[attr]) == "function")
                {
                    // Trust the user with the event name
                    Event.observe(el,
                                  attr.replace(/^on/i, ""),
                                  attributes[attr]);
                }
                else if (this.isIE)
                {
                    this.ieSetAttribute(el, attr, attributes[attr]);
                }
                else
                {
                    el.setAttribute(attr, attributes[attr]);
                }
            }
        }

        // Append children
        for (var i = 0, l = children.length; i < l; i++)
        {
            var child = children[i];

            // Ignore any null or undefined children
            if (child === undefined || child === null)
            {
                continue;
            }

            if (typeof(child) == "string" || typeof(child) == "number")
            {
                el.appendChild(document.createTextNode(child));
            }
            else
            {
                el.appendChild(child);
            }
        }

        return el;
    }
};

// Detect Internet Explorer using conditional comments
/*@cc_on @*/
/*@if (@_win32)
DomBuilder.isIE = true;
/*@end @*/