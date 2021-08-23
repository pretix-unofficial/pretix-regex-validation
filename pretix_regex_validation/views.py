import json
import logging
import re
from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _, gettext_noop
from django.views.generic import FormView
from i18nfield.forms import I18nFormField, I18nTextInput
from i18nfield.strings import LazyI18nString
from i18nfield.utils import I18nJSONEncoder
from pretix.base.models import Event, Question
from pretix.control.views.event import EventSettingsViewMixin

logger = logging.getLogger(__name__)


def valid_regex(val):
    try:
        re.compile(val)
    except re.error:
        raise ValidationError(_("Not a valid Python regular expression."))


class RegexValidationSettingsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.obj = kwargs.pop("obj")
        super().__init__(*args, **kwargs)

        fields = []
        fields.append(("email", _("E-mail")))
        if self.obj.settings.attendee_emails_asked:
            fields.append(("attendee_email", _("Attendee email")))
        if self.obj.settings.attendee_company_asked:
            fields.append(("company", _("Company")))

        if self.obj.settings.attendee_addresses_asked:
            fields.append(("street", _("Address")))
            fields.append(("zipcode", _("ZIP code")))
            fields.append(("city", _("City")))

        for q in self.obj.questions.filter(
            type__in=[Question.TYPE_TEXT, Question.TYPE_STRING, Question.TYPE_NUMBER]
        ):
            fields.append((q.identifier, q))

        for identifier, label in fields:
            self.fields[identifier] = forms.CharField(
                label=escape(_('Regular expression for "{field}"').format(field=label)),
                required=False,
                validators=[valid_regex],
            )
            self.fields[f"{identifier}:message"] = I18nFormField(
                label=escape(_('Error message for "{field}"').format(field=label)),
                required=False,
                locales=self.obj.settings.locales,
                initial=LazyI18nString.from_gettext(
                    gettext_noop("Please enter a valid value.")
                ),
                widget=I18nTextInput,
            )


class SettingsView(EventSettingsViewMixin, FormView):
    model = Event
    form_class = RegexValidationSettingsForm
    template_name = "pretix_regex_validation/settings.html"
    permission = "can_change_event_settings"

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretix_regex_validation:settings",
            kwargs={
                "organizer": self.request.event.organizer.slug,
                "event": self.request.event.slug,
            },
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["obj"] = self.request.event
        kwargs["initial"] = self.request.event.settings.regex_validation_config
        return kwargs

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            if form.has_changed():
                self.request.event.settings.regex_validation_config = json.dumps(
                    form.cleaned_data, cls=I18nJSONEncoder
                )
                self.request.event.log_action(
                    "pretix.event.settings",
                    user=self.request.user,
                    data={"regex_validation_config": form.cleaned_data},
                )
            messages.success(self.request, _("Your changes have been saved."))
            return redirect(self.get_success_url())
        else:
            messages.error(
                self.request,
                _("We could not save your changes. See below for details."),
            )
            return self.render_to_response(self.get_context_data(form=form))
