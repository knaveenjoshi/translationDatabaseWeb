import json
import os

from django.core import management
from django.test import TestCase

from mock import patch

from td.imports.models import WikipediaISOLanguage, EthnologueCountryCode, EthnologueLanguageCode, SIL_ISO_639_3, WikipediaISOCountry

from ..models import AdditionalLanguage
from td.models import Language
from ..tasks import integrate_imports, update_countries_from_imports


class AdditionalLanguageTestCase(TestCase):

    def test_updated_at_set_on_save(self):
        additional = AdditionalLanguage.objects.create(
            ietf_tag="ttt-x-ismai",
            common_name="Ismaili"
        )
        first_updated_at = additional.updated_at
        additional.save()
        self.assertTrue(additional.updated_at > first_updated_at)

    def test_string_representation(self):
        additional = AdditionalLanguage(
            ietf_tag="ttt-x-ismai",
            common_name="Ismaili"
        )
        self.assertEquals(str(additional), "ttt-x-ismai")


class LanguageIntegrationTests(TestCase):

    @classmethod
    def setUpClass(cls):
        wikipedia = open(os.path.join(os.path.dirname(__file__), "../imports/tests/data/wikipedia.html")).read()  # noqa
        ethno = open(os.path.join(os.path.dirname(__file__), "../imports/tests/data/LanguageCodes.tab")).read()  # noqa
        country = open(os.path.join(os.path.dirname(__file__), "../imports/tests/data/CountryCodes.tab")).read()  # noqa
        sil = open(os.path.join(os.path.dirname(__file__), "../imports/tests/data/iso_639_3.tab")).read()  # noqa
        w_country = open(os.path.join(os.path.dirname(__file__), "../imports/tests/data/wikipedia_country.html")).read()
        with patch("requests.Session") as mock_requests:
            mock_requests.get().status_code = 200
            mock_requests.get().content = wikipedia
            WikipediaISOLanguage.reload(mock_requests)
            mock_requests.get().content = ethno
            EthnologueLanguageCode.reload(mock_requests)
            mock_requests.get().content = country
            EthnologueCountryCode.reload(mock_requests)
            mock_requests.get().content = sil
            SIL_ISO_639_3.reload(mock_requests)
            mock_requests.get().content = w_country
            WikipediaISOCountry.reload(mock_requests)

        management.call_command("loaddata", "additional-languages.json", verbosity=1, noinput=True)
        management.call_command("loaddata", "uw_region_seed.json", verbosity=1, noinput=True)
        update_countries_from_imports()  # run task synchronously here
        integrate_imports()  # run task synchronously here

    def test_codes_export(self):
        data = Language.codes_text().split(" ")
        # self.assertFalse("bmy" in data)
        self.assertTrue("aa" in data)
        self.assertTrue("kmg" in data)
        self.assertTrue("es-419" in data)

    def test_names_export(self):
        data = Language.names_text().split("\n")
        data = [x.split("\t")[0] for x in data]
        # self.assertFalse("bmy" in data)
        self.assertTrue("aa" in data)
        self.assertTrue("kmg" in data)
        self.assertTrue("es-419" in data)

    def test_names_json_export(self):
        data = json.loads(json.dumps(Language.names_data()))
        langs = {x["lc"]: x for x in data}
        # self.assertFalse("bmy" in langs)
        self.assertTrue("aa" in langs)
        self.assertEquals(langs["aa"]["cc"], ["ET"])
        self.assertEquals(langs["aa"]["ln"], "Afaraf")
        self.assertEquals(langs["aa"]["lr"], "Africa")
        self.assertEquals(langs["aa"]["ld"], "ltr")
        self.assertTrue("kmg" in langs)
        self.assertEquals(langs["kmg"]["cc"], ["PG"])
        self.assertEquals(langs["kmg"]["ln"], u"K\xe2te")
        self.assertEquals(langs["kmg"]["lr"], "Pacific")
        self.assertEquals(langs["kmg"]["ld"], "ltr")
        self.assertTrue("es-419" in langs)
        self.assertEquals(langs["es-419"]["cc"], [""])
        self.assertEquals(langs["es-419"]["ln"], u"Espa\xf1ol Latin America")
        self.assertEquals(langs["es-419"]["lr"], "")
        self.assertEquals(langs["es-419"]["ld"], "ltr")

    def test_three_letter_field(self):
        additional = AdditionalLanguage(
            two_letter="z3",
            common_name="ZTest of 3 Letters",
            three_letter="z3z",
            ietf_tag="z3-test"
        )
        additional.save()
        lang = Language.objects.get(code="z3")
        self.assertEquals(lang.iso_639_3, additional.three_letter)

    def test_add_and_delete_from_additionallanguage(self):
        additional = AdditionalLanguage.objects.create(
            ietf_tag="zzz-z-test",
            common_name="ZTest"
        )
        additional.save()
        integrate_imports()   # run task synchronously
        data = Language.names_text().split("\n")
        self.assertTrue("zzz-z-test\tZTest" in data)
        additional.delete()
        data = Language.names_text().split("\n")
        self.assertTrue("zzz-z-test\tZTest" not in data)

    def test_additionallanguage_direction(self):
        additional = AdditionalLanguage.objects.create(
            ietf_tag="zzz-r-test",
            common_name="ZRTest",
            direction="r"
        )
        additional.save()
        langnames = Language.names_text().split("\n")
        self.assertTrue("zzz-r-test\tZRTest" in langnames)
        data = json.loads(json.dumps(Language.names_data()))
        langs = {x["lc"]: x for x in data}
        self.assertTrue("zzz-r-test" in langs)
        self.assertEquals(langs["zzz-r-test"]["ld"], "rtl")
