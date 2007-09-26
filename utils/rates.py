class RateLookup:
    """
    Handles lookups of rates applicable for given dates.
    """
    def __init__(self, model, related_object_attr):
        """
        model
            A model defining rates, which must have an effective_from
            field - one of ``UserRate`` or ``TaskTypeRate``.

        related_object_attr
            The name of the field in the given model which holds the
            relationship to the object the rates are for.
        """
        self.model = model
        self.related_object_attr = related_object_attr
        self.reset(rebuild_lookup=True)

    def get_applicable_rate(self, rated_instance, date):
        """
        Gets the Rate object defining rates applicable for the given
        instance of a rated item on the given date, or ``None`` if no
        rate applies.

        If an applicable rate is editable, it will be added to this
        object's ``editable_applicable_rates_used`` list.
        """
        applicable_rate = None
        rates = self.lookup[rated_instance.id]
        for rate in rates:
            if applicable_rate is None or \
               (rate.effective_from > applicable_rate.effective_from and
                rate.effective_from <= date):
                applicable_rate = rate
        if (applicable_rate is not None and
            not applicable_rate.editable and
            applicable_rate not in self.editable_rates_used):
            self.editable_rates_used.append(applicable_rate)
        return applicable_rate

    def reset(self, rebuild_lookup=False):
        """
        Clears the list of editable rates used and, optionally, rebuilds
        the rate lookup.
        """
        self.editable_rates_used = []
        if rebuild_lookup:
            self._lookup = {} # Maps rated object ids to lists of rates
            related_object_id_attr = '%_id' % self.related_object_attr
            for rate in self.model._default_manager.order_by('effective_from'):
                object_id = getattr(rate, related_object_id_attr)
                if not self._lookup.has_key(object_id):
                    self._lookup[object_id] = []
                self._lookup[object_id].append(rate)
