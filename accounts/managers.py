"""Query helpers for the customer account model."""

from django.db import models

from .validators import normalize_iranian_mobile


class CustomerQuerySet(models.QuerySet):
    """Filters for the two independent states a customer can be in."""

    def alive(self):
        """Customers that have not been soft deleted."""
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        """Soft-deleted customers only."""
        return self.filter(deleted_at__isnull=False)

    def active(self):
        """Customers allowed to authenticate: present and not blocked."""
        return self.alive().filter(is_active=True)


class CustomerManager(models.Manager.from_queryset(CustomerQuerySet)):
    """Default manager. Returns every row, including soft-deleted ones.

    Soft-deleted customers are deliberately visible by default so the admin and
    any future support tooling can find them. Call ``.alive()`` or ``.active()``
    for the filtered views.
    """

    def create_customer(self, phone_number, **extra_fields):
        """Create a customer from a phone number in any accepted input format."""
        customer = self.model(phone_number=phone_number, **extra_fields)
        customer.full_clean()
        customer.save(using=self._db)
        return customer

    def get_by_phone(self, phone_number):
        """Look a customer up by phone number in any accepted input format."""
        return self.get(phone_number=normalize_iranian_mobile(phone_number))
