"""Customer accounts.

``Customer`` is the identity record for shoppers. It is deliberately *not* the
``AUTH_USER_MODEL``: merchants and staff keep using ``django.contrib.auth.User``,
so the two populations stay separated and a customer can never hold admin
permissions by accident.

Consequences of that separation, worth knowing before building on this model:

* Customers are passwordless. There is no password column, and no credential of
  any kind lives here. Phone verification and OTP issuance belong in their own
  models.
* ``request.user`` is never a ``Customer``. Customer authentication needs its own
  mechanism, and ``last_login`` has to be written by that mechanism rather than
  by ``django.contrib.auth``'s signal.

Customers are global to the platform, not scoped per merchant: one phone number
means one account, shared across every merchant the person buys from.
"""

import uuid

from django.db import models
from django.utils import timezone

from .managers import CustomerManager
from .validators import normalize_iranian_mobile, validate_iranian_mobile


class Customer(models.Model):
    """A shopper identified solely by a verified Iranian mobile number."""

    # UUIDv7 is time-ordered, so it indexes like a sequential key while still
    # being safe to expose in URLs and API payloads.
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid7,
        editable=False,
        verbose_name="ID",
    )
    phone_number = models.CharField(
        max_length=13,
        unique=True,
        validators=[validate_iranian_mobile],
        help_text="Stored in E.164 form, e.g. +989121234567.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text=(
            "Authentication gate. Clear this to block a customer without "
            "removing their history."
        ),
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Written when a customer completes a login; never set on signup.",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "Soft-delete marker. Orders reference customers, so records are "
            "retired rather than deleted."
        ),
    )

    objects = CustomerManager()

    class Meta:
        verbose_name = "customer"
        verbose_name_plural = "customers"
        ordering = ("-joined_at",)

    def __str__(self):
        return self.phone_number

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def clean_fields(self, exclude=None):
        # Normalization has to happen before the field validators run, otherwise
        # valid user input like "09121234567" fails the E.164 check.
        exclude = exclude or []
        if "phone_number" not in exclude and self.phone_number:
            self.phone_number = normalize_iranian_mobile(self.phone_number)
        super().clean_fields(exclude=exclude)

    def save(self, *args, **kwargs):
        # Also normalized here so code paths that skip full_clean() (bulk
        # imports, shell work, future API handlers) cannot write a non-canonical
        # number and silently create a duplicate account.
        if self.phone_number:
            self.phone_number = normalize_iranian_mobile(self.phone_number)
        return super().save(*args, **kwargs)

    def block(self):
        """Deny authentication while keeping the account intact."""
        self.is_active = False
        self.save(update_fields=["is_active"])

    def unblock(self):
        """Re-allow authentication."""
        self.is_active = True
        self.save(update_fields=["is_active"])

    def soft_delete(self):
        """Retire the account. Implies blocking."""
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save(update_fields=["deleted_at", "is_active"])

    def restore(self):
        """Bring a retired account back, unblocked.

        Re-registration with the same phone number should restore the existing
        record rather than insert a new one, since ``phone_number`` stays unique
        across soft-deleted rows.
        """
        self.deleted_at = None
        self.is_active = True
        self.save(update_fields=["deleted_at", "is_active"])
