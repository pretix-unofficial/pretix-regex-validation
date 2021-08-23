from django.core.validators import RegexValidator
from django.dispatch import receiver
from django.urls import resolve, reverse
from django.utils.translation import gettext_lazy as _
from i18nfield.strings import LazyI18nString
from pretix.base.settings import settings_hierarkey
from pretix.control.signals import nav_event_settings
from pretix.presale.signals import (
    contact_form_fields_overrides,
    question_form_fields_overrides,
)


@receiver(nav_event_settings, dispatch_uid="regex_validation_nav")
def navbar_info(sender, request, **kwargs):
    url = resolve(request.path_info)
    if not request.user.has_event_permission(
        request.organizer, request.event, "can_change_event_settings", request=request
    ):
        return []
    return [
        {
            "label": _("Regex validation"),
            "url": reverse(
                "plugins:pretix_regex_validation:settings",
                kwargs={
                    "event": request.event.slug,
                    "organizer": request.organizer.slug,
                },
            ),
            "active": url.namespace == "plugins:pretix_regex_validation",
        }
    ]


@receiver(
    contact_form_fields_overrides, dispatch_uid="regex_validation_fields_overrides"
)
@receiver(
    question_form_fields_overrides, dispatch_uid="regex_validations_fields_overrides"
)
def form_fields_overrides(sender, request, **kwargs):
    o = {}
    for k, v in sender.settings.regex_validation_config.items():
        if k.endswith(":message") or not v:
            continue
        o[k] = {
            "validators": [
                RegexValidator(
                    regex=v,
                    message=str(
                        LazyI18nString(
                            sender.settings.regex_validation_config.get(
                                f"{k}:message",
                                _("Please enter a valid value."),
                            )
                        )
                    ),
                )
            ]
        }
    return o


settings_hierarkey.add_default("regex_validation_config", "{}", dict)
