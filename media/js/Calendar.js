/**
 * Provides a means of displaying a dynamic calendar when a control is clicked
 * and populating a field with the selected date.
 * <p>
 * Usage: <code>Calendar.bindEventListener("fieldId", "controlId");</code>
 */
var Calendar =
{
    DAYS_IN_MONTH: [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
    DAYS: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    MONTHS: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    UK_DATE_REGEX: /^(0?[1-9]|[1-2][0-9]|3[0-1])\/(0?[1-9]|1[0-2])\/(\d\d\d\d)$/,

    /**
     * Id of the element which should be used or created to display the
     * calendar.
     */
    calendarOutput: "cal",
    /**
     * Id of the element which should be used or created to display the month
     * select.
     */
    monthOutput: "month",
    /** Year to be displayed. */
    year: -1,
    /** Month to be displayed. */
    month: -1,
    /** Day to be displayed. */
    day: -1,
    /** Function which should be executed with the selected date when selected. */
    callback: null,
    /** Currently selected day. */
    selectedDay: -1,
    /** <code>true</code> if the calendar is visible. */
    visible: false,
    /** <code>true</code> if the calendar controls are active. */
    active: true,
    /** Position of the calendar - [x, y]. */
    pos: [-1, -1],
    /** <code>true</code> if the month select is visible. */
    monthSelectVisible: false,

    /**
     * Shows the calendar.
     *
     * @param {String} fieldId the field which should be populated with the
     *                         selected date, and from which the starting date
     *                         should be taken, if valid in dd/mm/yyyy format.
     * @param {String} controlId the control which was click to display the
     *                           calendar, and whose position should be used to
     *                           display the calendar.
     */
    show: function(fieldId, controlId)
    {
        // Configure calendar
        this.pos = Position.cumulativeOffset($(controlId));
        this.callback = this.updateField(fieldId);
        if (!this.active)
        {
            this.hideMonthSelect();
            this.active = true;
        }
        this.visible = false;
        var currentDate = $(fieldId).value;
        if (currentDate != "" && this.isValidUKDate(currentDate) == true)
        {
            this.setDate(currentDate);
        }
        else
        {
            this.setDate(new Date());
        }

        // Create and show calendar
        this.createCalendar();
    },

    /**
     * Binds a function to show the calendar when the control with the given id
     * is clicked.
     *
     * @param {String} fieldId
     * @param {String} controlId
     */
    bindEventListener: function(fieldId, controlId)
    {
        var calendar = this;
        Event.observe(controlId,
                      "click",
                      function() { calendar.show(fieldId, controlId); },
                      false);
    },

    /**
     * Creates a function which when executed will populate the given field with
     * a supplied value.
     *
     * @param {String} fieldId id of the field whose value should be updated.
     */
    updateField: function(fieldId)
    {
        return function(date)
        {
            $(fieldId).value = date;
        }
    },

    /**
     * Sets the date to be displayed on the calendar and shows it.
     * <p>
     * This function may accept the following input:
     * <ul>
     *   <li>a Date object</li>
     *   <li>a String representing a valid date in dd/mm/yyyy format</li>
     *   <li>a year and a month</li>
     *   <li>a year, a month and a day</li>
     * </ul>
     */
    setDate: function()
    {
        if (arguments.length == 1)
        {
            if (typeof arguments[0] == "object")
            {
                var date = arguments[0];
                this.year = date.getFullYear();
                this.month = date.getMonth() + 1;
                this.day = date.getDate();
                this.createCalendar();
            }
            else if (typeof arguments[0] == "string")
            {
                if (this.isValidUKDate(arguments[0]))
                {
                    var parts = this.UK_DATE_REGEX.exec(arguments[0]);
                    this.setDate(parts[3], parts[2], parts[1]);
                    this.createCalendar();
                }
                else
                {
                    throw new Error("Invalid date format");
                }
            }
        }
        else if (arguments.length == 2)
        {
            this.year = 1 * arguments[0];
            this.month = 1 * arguments[1];
            this.createCalendar();
        }
        else if (arguments.length == 3)
        {
            this.year = 1 * arguments[0];
            this.month = 1 * arguments[1];
            this.day = 1 *arguments[2];
            this.createCalendar();
        }
        else
        {
            throw new Error("Invalid date input");
        }
    },

    /* Calendar Controls
    ------------------------------------------------------------------------- */
    /**
     * Selects the day represented by the given table cell.
     *
     * @param {Element} cell a table cell representing the selected day.
     */
    selectDay: function(cell)
    {
        if (!this.active)
        {
            return;
        }

        // Determine the selected day from the cell's contents
        this.day = 1 * cell.firstChild.data;

        // Call the callback function, passing in the selected date
        (this.callback)((this.day < 10 ? "0" + this.day : this.day) + "/" +
                        (this.month < 10 ? "0" + this.month : this.month) + "/" +
                        this.year);

        // Hide the calendar
        Element.hide(this.calendarOutput);
        this.visible = false;
    },

    /**
     * Decrements the month to be displayed on the calendar and redraws it.
     */
    previousMonth: function()
    {
        if (!this.active)
        {
            return;
        }
        this.month--;
        if (this.month == 0)
        {
            this.month = 12;
            this.year--;
        }
        this.createCalendar();
    },

    /**
     * Increments the month to be displayed on the calendar and redraws it.
     */
    nextMonth: function()
    {
        if (!this.active)
        {
            return;
        }
        this.month++;
        if (this.month == 13)
        {
            this.month = 1;
            this.year++;
        }
        this.createCalendar();
    },

    /**
     * Decrements the year to be displayed on the calendar and redraws it.
     */
    previousYear: function()
    {
        if (!this.active)
        {
            return;
        }
        this.year--;
        this.createCalendar();
    },

    /**
     * Increments the year to be displayed on the calendar and redraws it.
     */
    nextYear: function()
    {
        if (!this.active)
        {
            return;
        }
        this.year++;
        this.createCalendar();
    },

    /**
     * Creates the calendar using the currently configured date and shows it, if
     * not already being shown.
     */
    createCalendar: function()
    {
        this.generateCalendar();
        if (!this.active)
        {
            this.hideMonthSelect();
        }
        if (!this.visible)
        {
            var output = $(this.calendarOutput);
            output.style.display = "block";
            output.style.position = "absolute";
            output.style.left = this.pos[0] + "px";
            output.style.top = this.pos[1] + "px";
            this.visible = true;
        }
    },

    /**
     * Creates and shows a month select dialogue according to the currently
     * configured date.
     */
    showMonthSelect: function()
    {
        this.generateMonthSelect();

        var output = $(this.monthOutput);
        output.style.display = "block";
        output.style.position = "absolute";
        var pos = Position.cumulativeOffset($(this.calendarOutput));
        output.style.left = (pos[0] + Math.round(($(this.calendarOutput).offsetWidth - output.offsetWidth) / 2)) + "px";

        var items = output.getElementsByTagName("li");
        var pos1 = Position.cumulativeOffset(items[0]);
        var pos2 = Position.cumulativeOffset(items[3]);
        var diff = pos2[1] - pos1[1];
        if (pos[1] - diff > 0)
        {
            output.style.top = (pos[1] - diff) + "px";
        }
        else
        {
            output.style.top = pos[1] + "px";
        }

        output.style.zIndex = 99;
        Element.show(output);
        // Disable other calendar controls
        this.active = false;
    },

    /**
     * Hides the month select dialogue.
     */
    hideMonthSelect: function()
    {
        Element.hide(this.monthOutput);
        // Re-enable other calendar controls
        this.active = true;
    },

    /* Calendar
    ------------------------------------------------------------------------- */
    /**
     * Uses the DOM to generate a calendar.
     */
    generateCalendar: function()
    {
        var container = $(this.calendarOutput);

        // Create or empty the container, as necessary
        if (container == null)
        {
            container = document.createElement("div");
            container.id = this.calendarOutput;
            document.body.appendChild(container);
        }
        else
        {
            Element.update(container);
        }

        /* Month Controls
        ----------------------------------------------------- */
        var monthControl = document.createElement("div");
        monthControl.className = "month";
        var prev = document.createElement("span");
        prev.className = "previous";
        prev.onclick = this.previousMonth.bind(this);

        var img = document.createElement("img");
        img.src = mediaURL + "img/prev.gif";
        prev.appendChild(img);
        monthControl.appendChild(prev);
        monthControl.appendChild(document.createTextNode(" "));

        var month = document.createElement("span");
        month.className = "current";
        Element.update(month, this.MONTHS[this.month - 1]);
        monthControl.appendChild(month);
        monthControl.appendChild(document.createTextNode(" "));
        month.onclick = this.showMonthSelect.bind(this);

        var next = document.createElement("span");
        next.className = "next";
        next.onclick = this.nextMonth.bind(this);

        var img = document.createElement("img");
        img.src = mediaURL + "img/next.gif";
        next.appendChild(img);
        monthControl.appendChild(next);

        container.appendChild(monthControl);

        /* Calendar
        --------------------------------------------------------- */
        var cal = document.createElement("table");
        Element.update(cal);
        cal.cellSpacing = 0;

        // Day header
        var dayHeader = document.createElement("thead");
        var row = document.createElement("tr");
        for (var i = 0, dayName; dayName = Calendar.DAYS[i]; i++)
        {
            var day = document.createElement("th");
            Element.update(day, dayName.substring(0, 2));
            row.appendChild(day);
        }
        dayHeader.appendChild(row);
        cal.appendChild(dayHeader);

        var days = document.createElement("tbody");

        // Calendar variables
        var blanksBefore = this.blankRowsBefore();
        var daysInMonth = this.daysInMonth() + blanksBefore;
        var totalCells = 42;

        // Day rows
        var row = document.createElement("tr");
        for (var i = 1; i <= blanksBefore; i++)
        {
            var day = document.createElement("td");
            Element.update(day, "-");
            day.className = "blank";
            row.appendChild(day);
        }
        for (var i = blanksBefore, j = 1; i < daysInMonth; i++, j++)
        {
            if (i % 7 == 0)
            {
                days.appendChild(row);
                row = document.createElement("tr");
            }
            var day = document.createElement("td");
            Element.update(day, j);
            day.className = "day";
            if (j == this.day)
            {
                Element.addClassName(day, "selected");
                this.selectedDay = day;
            }
            day.onclick = function()
            {
                Calendar.selectDay(this);
            };
            row.appendChild(day);
        }
        for (var i = daysInMonth; i <= totalCells; i++)
        {
            if (i % 7 == 0)
            {
                days.appendChild(row);
                row = document.createElement("tr");
            }
            var day = document.createElement("td");
            Element.update(day, "-");
            day.className = "blank";
            row.appendChild(day);
        }
        cal.appendChild(days);

        container.appendChild(cal);

        /* Year Controls
        ---------------------------------------------- */
        var yearControl = document.createElement("div");
        yearControl.className = "year";

        var prev = document.createElement("span");
        prev.className = "previous";
        prev.onclick = this.previousYear.bind(this);
        Element.update(prev, this.year - 1);
        yearControl.appendChild(prev);

        var year = document.createElement("span");
        year.className = "current";
        Element.update(year, " " + this.year + " ");
        yearControl.appendChild(year);

        var next = document.createElement("span");
        next.className = "next";
        next.onclick = this.nextYear.bind(this);
        Element.update(next, this.year + 1);
        yearControl.appendChild(next);

        container.appendChild(yearControl);

        return container;
    },

    /**
     * Determines the number of cells which should be left blank before the
     * cells for days in the current month should be created.
     */
    blankRowsBefore: function()
    {
        var date = new Date(this.year, this.month - 1, 1);
        return (date.getDay() - 1 >= 0 ? date.getDay() - 1 : 6);
    },

    /**
     * Determines the number of days in the current month.
     */
    daysInMonth: function()
    {
        if (this.isLeapYear(this.year))
        {
            this.DAYS_IN_MONTH[1] = 29;
        }
        else
        {
            this.DAYS_IN_MONTH[1] = 28;
        }
        return this.DAYS_IN_MONTH[this.month - 1];
    },

    /* Month Select
    ------------------------------------------------------------------------- */
    /**
     * Uses the DOM to generate a month select control.
     */
    generateMonthSelect: function()
    {
        var container = $(this.monthOutput);

        // Create or empty the month select control
        if (container == null)
        {
            container = document.createElement("div");
            container.id = this.monthOutput;
            document.body.appendChild(container);
        }
        else
        {
            Element.update(container);
        }

        var list = document.createElement("ul");

        var monthIndex = this.month - 5;
        var year = (monthIndex < 0 ? this.year - 1 : this.year);
        if (monthIndex < 0)
        {
            monthIndex = monthIndex + this.MONTHS.length;
        }

        for (var i = 0; i < 7; i++)
        {
            if (monthIndex > 10)
            {
                year++;
            }

            monthIndex = (monthIndex + 1) % this.MONTHS.length;

            var li = document.createElement("li");
            if (monthIndex == this.month - 1)
            {
                li.className = "current";
            }
            Element.update(li, this.MONTHS[monthIndex] + " " + year);
            li.onmouseover = function()
            {
                Element.addClassName(this, "hover");
            };
            li.onmouseout = function()
            {
                Element.removeClassName(this, "hover");
            };
            Event.observe(li, "click", this.setMonthClosure(year, monthIndex + 1), false);
            list.appendChild(li);
        }
        container.appendChild(list);
    },

    /**
     * Creates a function which when executed will select the given year and
     * month in the calendar.
     *
     * @param {Number} year the year to be selected.
     * @param {Number} month the month to be selected.
     */
    setMonthClosure: function(year, month)
    {
        return function()
        {
            Calendar.hideMonthSelect();
            Calendar.setDate(year, month);
            Calendar.createCalendar();
        }
    },

    /* Date Validation
    ------------------------------------------------------------------------- */
    /**
     * @return <code>true</code> if the given date string is a valid date in
     *         dd/mm/yyyy format, <code>false</code> otherwise.
     */
    isValidUKDate: function(aDate)
    {
        var parts = this.UK_DATE_REGEX.exec(aDate);
        return (parts != null
                && this.isValidDate(parts[3], parts[2], parts[1]));
    },

    /**
     * @return <code>true</code> if the given date is valid, <code>false</code>
     *         otherwise.
     */
    isValidDate: function(aYear, aMonth, aDay)
    {
        // Adjust days per month for February according to the selected year.
        if (this.isLeapYear(aYear))
        {
            this.DAYS_IN_MONTH[1] = 29;
        }
        else
        {
            this.DAYS_IN_MONTH[1] = 28;
        }

        var monthIndex = parseInt(aMonth, 10) - 1;
        var day = parseInt(aDay, 10);

        return day <= this.DAYS_IN_MONTH[monthIndex];
    },

    /**
     * @return <code>true</code> if the given year is a leap year,
     *         <code>false</code> otherwise.
     */
    isLeapYear: function(aYear)
    {
        var year = parseInt(aYear, 10);
        return ((year % 4 == 0) && (year % 100 != 0)) || (year % 400 == 0);
    }
}