from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist

from account.signals import password_changed
from account.signals import user_sign_up_attempt, user_signed_up
from account.signals import user_login_attempt, user_logged_in

from pinax.eventlog.models import log

from .models import AdditionalLanguage
from td.models import Country, Language
from .signals import languages_integrated


@receiver(post_save, sender=AdditionalLanguage)
def handle_additionallanguage_save(sender, instance, **kwargs):
    a_code = instance.merge_code()
    lang, created = Language.objects.get_or_create(code=a_code)
    lang.name = instance.merge_name()
    lang.direction = instance.direction
    lang.iso_639_3 = instance.three_letter
    lang.save()


@receiver(post_delete, sender=AdditionalLanguage)
def handle_additionallanguage_delete(sender, instance, **kwargs):
    d_code = instance.merge_code()
    try:
        lang = Language.objects.get(code=d_code)
        lang.delete()
    except ObjectDoesNotExist:
        pass


@receiver(post_save, sender=Language)
def handle_language_save(sender, **kwargs):
    cache.delete("langnames")
    cache.set("map_gateway_refresh", True)


@receiver(post_delete, sender=Language)
def handle_language_delete(sender, **kwargs):
    cache.delete("langnames")
    cache.set("map_gateway_refresh", True)


@receiver(post_save, sender=Country)
def handle_country_save(sender, **kwargs):
    cache.set("map_gateway_refresh", True)


@receiver(post_delete, sender=Country)
def handle_country_delete(sender, **kwargs):
    cache.set("map_gateway_refresh", True)


@receiver(languages_integrated)
def handle_languages_integrated(sender, **kwargs):
    cache.delete("langnames")
    cache.set("langnames", Language.names_data(), None)


@receiver(user_logged_in)
def handle_user_logged_in(sender, **kwargs):
    log(
        user=kwargs.get("user"),
        action="USER_LOGGED_IN",
        extra={}
    )


@receiver(password_changed)
def handle_password_changed(sender, **kwargs):
    log(
        user=kwargs.get("user"),
        action="PASSWORD_CHANGED",
        extra={}
    )


@receiver(user_login_attempt)
def handle_user_login_attempt(sender, **kwargs):
    log(
        user=None,
        action="LOGIN_ATTEMPTED",
        extra={
            "username": kwargs.get("username"),
            "result": kwargs.get("result")
        }
    )


@receiver(user_sign_up_attempt)
def handle_user_sign_up_attempt(sender, **kwargs):
    log(
        user=None,
        action="SIGNUP_ATTEMPTED",
        extra={
            "username": kwargs.get("username"),
            "email": kwargs.get("email"),
            "result": kwargs.get("result")
        }
    )


@receiver(user_signed_up)
def handle_user_signed_up(sender, **kwargs):
    log(
        user=kwargs.get("user"),
        action="USER_SIGNED_UP",
        extra={}
    )
