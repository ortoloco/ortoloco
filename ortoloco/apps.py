from django.apps import AppConfig


class OrtolocoConfig(AppConfig):
    name = 'ortoloco'

    def ready(self):
        # Quick fix until juntagrico handles it: the admin builds change messages with deactivated
        # translations, then Config.vocabulary crashes on get_language() being None
        # (e.g. when deleting an assignment in the job form).
        from django.conf import settings
        from django.utils import translation
        from juntagrico.config import Config

        vocabulary = Config.vocabulary

        def vocabulary_with_language(key, fallback=None):
            if translation.get_language() is None:
                with translation.override(settings.LANGUAGE_CODE):
                    return vocabulary(key, fallback)
            return vocabulary(key, fallback)

        Config.vocabulary = vocabulary_with_language
