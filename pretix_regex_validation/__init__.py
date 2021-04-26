from django.utils.translation import gettext_lazy

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")

__version__ = "1.0.0"


class PluginApp(PluginConfig):
    name = "pretix_regex_validation"
    verbose_name = "Regex Validation"

    class PretixPluginMeta:
        name = gettext_lazy("Regex Validation")
        author = "pretix team"
        description = gettext_lazy("Allows to add arbitrary regex validation to fields")
        visible = True
        version = __version__
        category = "CUSTOMIZATION"
        compatibility = "pretix>=3.18.0.dev0"

    def ready(self):
        from . import signals  # NOQA


default_app_config = "pretix_regex_validation.PluginApp"
