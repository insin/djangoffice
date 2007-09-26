Event.onDOMReady(function()
{
    var suffix = "over";

    var mouseOverHandler = function(e)
    {
        var el = Event.element(e);
        el.className += suffix;
    };

    var mouseOutHandler = function(e)
    {
        var el = Event.element(e);
        if (el.className.lastIndexOf(suffix) == el.className.length - suffix.length)
        {
            el.className = el.className.substring(0, el.className.length - suffix.length);
        }
    };

    $$("button").each(function(el)
    {
        Event.observe(el, "mouseover", mouseOverHandler);
        Event.observe(el, "mouseout", mouseOutHandler);
    });
});