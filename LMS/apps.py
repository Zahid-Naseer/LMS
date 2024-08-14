from django.apps import AppConfig


class LmsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'LMS'
    
    def ready(self):
        import LMS.templatetags.custom_filters