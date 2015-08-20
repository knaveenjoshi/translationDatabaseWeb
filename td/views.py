import operator

from account.decorators import login_required
from account.mixins import LoginRequiredMixin
from pinax.eventlog.mixins import EventLogMixin
from django.contrib import messages
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView, UpdateView, CreateView
from django.views.decorators.csrf import csrf_exempt

from td.imports.models import (
    EthnologueCountryCode,
    EthnologueLanguageCode,
    EthnologueLanguageIndex,
    SIL_ISO_639_3,
    WikipediaISOLanguage,
    IMBPeopleGroup
)
from td.models import Language, Country, Region, Network
from .models import AdditionalLanguage
from td.forms import NetworkForm, CountryForm, LanguageForm, UploadGatewayForm
from td.resources.models import transform_country_data
from td.resources.tasks import get_map_gateways
from td.resources.views import EntityTrackingMixin
from .utils import DataTableSourceView, svg_to_pdf


def codes_text_export(request):
    return HttpResponse(Language.codes_text(), content_type="text/plain")


def names_text_export(request):
    return HttpResponse(Language.names_text(), content_type="text/plain")


def names_json_export(request):
    data = cache_get_or_set("langnames", Language.names_data)
    return JsonResponse(data, safe=False)  # Set safe to False to allow list instead of dict to be returned


def cache_get_or_set(key, acallable):
    data = cache.get(key)
    if data is None:
        data = acallable()
        cache.set(key, data, None)
    return data


@csrf_exempt
def export_svg(request):
    svg = request.POST.get("data")
    response = HttpResponse(content_type="application/pdf")
    response.write(svg_to_pdf(svg))
    response["Content-Disposition"] = "attachment; filename=gateway_languages_map.pdf"
    return response


def languages_autocomplete(request):
    term = request.GET.get("q").lower()
    data = cache_get_or_set("langnames", Language.names_data)
    d = []
    if len(term) <= 3:
        term = term.encode("utf-8")
        # search: cc, lc
        # first do a *starts with* style search of language code (lc)
        d.extend([
            x
            for x in data
            if term == x["lc"].lower()[:len(term)]
        ])
        d.extend([
            x
            for x in data
            if term in [y.lower() for y in x["cc"]]
        ])
    if len(term) >= 3:
        # search: lc, ln, lr
        term = term.encode("utf-8")
        d.extend([
            x
            for x in data
            if term in x["lc"] or term in x["ln"].lower() or term in x["lr"].lower()
        ])
    return JsonResponse({"results": d, "count": len(d), "term": term})


class AdditionalLanguageListView(TemplateView):
    template_name = "td/additionallanguage_list.html"


class EthnologueCountryCodeListView(TemplateView):
    template_name = "td/ethnologuecountrycode_list.html"


class EthnologueLanguageCodeListView(TemplateView):
    template_name = "td/ethnologuelanguagecode_list.html"


class EthnologueLanguageIndexListView(TemplateView):
    template_name = "td/ethnologuelanguageindex_list.html"


class SIL_ISO_639_3ListView(TemplateView):
    template_name = "td/sil_list.html"


class WikipediaISOLanguageListView(TemplateView):
    template_name = "td/wikipedia_list.html"


class IMBPeopleGroupListView(TemplateView):
    template_name = "td/imbpeoplegroup_list.html"


class AjaxAdditionalLanguageListView(DataTableSourceView):
    model = AdditionalLanguage
    fields = [
        "ietf_tag",
        "two_letter",
        "three_letter",
        "common_name",
        "native_name",
        "direction",
        "comment"
    ]


class AjaxEthnologueCountryCodeListView(DataTableSourceView):
    model = EthnologueCountryCode
    fields = [
        "code",
        "name",
        "area"
    ]


class AjaxEthnologueLanguageCodeListView(DataTableSourceView):
    model = EthnologueLanguageCode
    fields = [
        "code",
        "country_code",
        "status",
        "name"
    ]


class AjaxEthnologueLanguageIndexListView(DataTableSourceView):
    model = EthnologueLanguageIndex
    fields = [
        "language_code",
        "country_code",
        "name_type",
        "name"
    ]


class AjaxSIL_ISO_639_3ListView(DataTableSourceView):
    model = SIL_ISO_639_3
    fields = [
        "code",
        "part_2b",
        "part_2t",
        "part_1",
        "scope",
        "language_type",
        "ref_name",
        "comment"
    ]


class AjaxWikipediaISOLanguageListView(DataTableSourceView):
    model = WikipediaISOLanguage
    fields = [
        "language_family",
        "language_name",
        "native_name",
        "iso_639_1",
        "iso_639_2t",
        "iso_639_2b",
        "iso_639_3",
        "iso_639_9",
        "notes"
    ]


class AjaxIMBPeopleGroupListView(DataTableSourceView):
    model = IMBPeopleGroup
    fields = [
        "peid",
        "affinity_bloc",
        "people_cluster",
        "sub_continent",
        "country",
        "country_of_origin",
        "people_group",
        "population",
        "dispersed",
        "rol",
        "language",
        "religion",
        "written_scripture",
        "jesus_film",
        "radio_broadcast",
        "gospel_recording",
        "audio_scripture",
        "bible_stories"
    ]


@login_required
def country_tree_data(request):
    return JsonResponse(transform_country_data(Country.gateway_data()))


def country_map_data(request):
    language_to_color = {
        "defaultFill": "#CCCCCC",
        "en": "#ACEA73",
        "fr": "#CCAAEA",
        "es": "#E9E36F",
        "es-419": "#E9E36F",
        "pt": "#E1AB5B",
        "nl": "#BA4759",
        "hi": "#868686",
        "ru": "#794C53",
        "ar": "#84E9CF",
        "sw": "#F54982",
        "am": "#F7E718",
        "tr": "#3A39DD",
        "ps": "#6FCF1A",
        "ja": "#216A8B",
        "id": "#591468",
        "zh": "#6B9BE0",
        "km": "#39FF06",
        "tl": "#DEE874",
        "bn": "#346507",
        "my": "#F1FF31",
        "lo": "#CE0008",
        "th": "#B7FFF8",
        "mn": "#DE7E6A",
        "fa": "#5F441A",
        "ur": "#BEB41F",
        "vi": "#E8AB50",
        "ne": "#741633",
        "dz": "#F2951C",
        "ms": "#A7DA3D",
        "pis": "#8A8A8A",
        "tpi": "#E966C7",
        "ta": "#8A8A8A"
    }
    map_gateways = get_map_gateways()
    return JsonResponse({"fills": language_to_color, "country_data": map_gateways})


@login_required
def upload_gateway_flag_file(request):
    if request.method == "POST":
        form = UploadGatewayForm(request.POST, request.FILES)
        if form.is_valid():
            for lang in Language.objects.filter(code__in=form.cleaned_data["languages"]):
                lang.gateway_flag = True
                lang.source = request.user
                lang.save()
            messages.add_message(request, messages.SUCCESS, "Gateway languages updated")
            return redirect("gateway_flag_update")
    else:
        form = UploadGatewayForm(
            initial={
                "languages": "\n".join([
                    l.code.lower()
                    for l in Language.objects.filter(gateway_flag=True).order_by("code")
                ])
            }
        )
    return render(request, "resources/gateway_languages_update.html", {"form": form})


@login_required
def upload_rtl_list(request):
    if request.method == "POST":
        form = UploadGatewayForm(request.POST)
        if form.is_valid():
            for lang in Language.objects.filter(code__in=form.cleaned_data["languages"]):
                lang.direction = "r"
                lang.source = request.user
                lang.save()
            messages.add_message(request, messages.SUCCESS, "RTL languages updated")
            return redirect("rtl_languages_update")
    else:
        form = UploadGatewayForm(
            initial={
                "languages": "\n".join([
                    l.code.lower()
                    for l in Language.objects.filter(direction="r").order_by("code")
                ])
            }
        )
    return render(request, "resources/rtl_languages_update.html", {"form": form})


class RegionListView(ListView):
    model = Region
    template_name = "resources/region_list.html"

    def get_queryset(self):
        return Region.objects.all()


class RegionDetailView(ListView):
    model = Region
    template_name = "resources/region_detail.html"

    def get_context_data(self, **kwargs):
        region = Region.objects.get(slug=self.kwargs.get("slug"))
        context = super(RegionDetailView, self).get_context_data(**kwargs)
        context.update({
            "region": region,
            "country_list": region.countries.all(),
            "languages": Language.objects.filter(country__region=region).order_by("name")
        })
        return context

    def get_queryset(self):
        qs = super(RegionDetailView, self).get_queryset()
        qs = qs.filter(slug__iexact=self.kwargs.get("slug"))
        qs = qs.order_by("name")
        return qs


class CountryListView(ListView):
    model = Country
    template_name = "resources/country_list.html"

    def get_queryset(self):
        qs = super(CountryListView, self).get_queryset()
        qs = qs.order_by("name")
        return qs


class CountryDetailView(DetailView):
    model = Country
    template_name = "resources/country_detail.html"


class CountryEditView(LoginRequiredMixin, EventLogMixin, EntityTrackingMixin, UpdateView):
    model = Country
    form_class = CountryForm
    action_kind = "EDIT"
    template_name = "resources/country_form.html"

    def get_success_url(self):
        return reverse("country_detail", args=[self.object.pk])


class LanguageTableSourceView(DataTableSourceView):

    def __init__(self, **kwargs):
        super(LanguageTableSourceView, self).__init__(**kwargs)

    @property
    def queryset(self):
        if "pk" in self.kwargs:
            return Language.objects.filter(gateway_language=self.kwargs["pk"])
        else:
            return self.model._default_manager.all()

    @property
    def filtered_data(self):
        if len(self.search_term) and len(self.search_term) <= 3:
            qs = self.queryset.filter(
                reduce(
                    operator.or_,
                    [Q(code__istartswith=self.search_term)]
                )
            ).order_by("code")
            if qs.count():
                return qs
        return self.queryset.filter(
            reduce(
                operator.or_,
                [Q(x) for x in self.filter_predicates]
            )
        ).order_by(
            self.order_by
        )


class LanguageListView(TemplateView):
    template_name = "resources/language_list.html"


class AjaxLanguageListView(LanguageTableSourceView):
    model = Language
    fields = [
        "code",
        "iso_639_3",
        "name",
        "direction",
        "country__name",
        "native_speakers",
        "gateway_language__name",
        "gateway_flag"
    ]
    link_column = "code"
    link_url_name = "language_detail"
    link_url_field = "pk"


class AjaxLanguageGatewayListView(LanguageTableSourceView):
    model = Language
    fields = [
        "code",
        "iso_639_3",
        "name",
        "direction",
        "country__name",
        "native_speakers",
        "gateway_flag"
    ]
    link_column = "code"
    link_url_name = "language_detail"
    link_url_field = "pk"


class LanguageCreateView(LoginRequiredMixin, EventLogMixin, EntityTrackingMixin, CreateView):
    model = Language
    form_class = LanguageForm
    action_kind = "CREATE"

    def dispatch(self, request, *args, **kwargs):
        self.country = get_object_or_404(Country, pk=self.kwargs.get("pk"))
        return super(LanguageCreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.country = self.country
        self.object.save()
        form.save_m2m()
        self.log_action()
        return redirect("language_detail", self.object.pk)

    def get_context_data(self, **kwargs):
        context = super(LanguageCreateView, self).get_context_data(**kwargs)
        context.update({
            "country": self.country
        })
        return context


class LanguageDetailView(DetailView):
    model = Language
    template_name = "resources/language_detail.html"

    def get_context_data(self, **kwargs):
        context = super(LanguageDetailView, self).get_context_data(**kwargs)
        context.update({
            "country": self.object.country
        })
        return context


class LanguageEditView(LoginRequiredMixin, EventLogMixin, EntityTrackingMixin, UpdateView):
    model = Language
    form_class = LanguageForm
    template_name = "resources/language_form.html"
    action_kind = "EDIT"

    def get_success_url(self):
        return reverse("language_detail", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super(LanguageEditView, self).get_context_data(**kwargs)
        context.update({
            "country": self.object.country
        })
        return context


class NetworkCreateView(LoginRequiredMixin, EventLogMixin, EntityTrackingMixin, CreateView):
    model = Network
    form_class = NetworkForm
    action_kind = "CREATE"

    def get_success_url(self):
        return reverse("network_detail", args=[self.object.pk])


class NetworkDetailView(DetailView):
    model = Network
    template_name = "resources/network_detail.html"


class NetworkEditView(LoginRequiredMixin, EventLogMixin, EntityTrackingMixin, UpdateView):
    model = Network
    form_class = NetworkForm
    action_kind = "EDIT"
    template_name = "resources/network_form.html"

    def get_success_url(self):
        return reverse("network_detail", args=[self.object.pk])


class NetworkListView(ListView):
    model = Network
    template_name = "resources/network_list.html"

    def get_queryset(self):
        qs = super(NetworkListView, self).get_queryset()
        qs = qs.order_by("name")
        return qs


class BaseLanguageView(LoginRequiredMixin, EventLogMixin, EntityTrackingMixin):

    def dispatch(self, request, *args, **kwargs):
        self.language = get_object_or_404(Language, pk=self.kwargs.get("pk"))
        return super(BaseLanguageView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.language = self.language
        self.object.save()
        form.save_m2m()
        self.log_action()
        return redirect("language_detail", self.language.pk)

    def get_context_data(self, **kwargs):
        context = super(BaseLanguageView, self).get_context_data(**kwargs)
        context.update({
            "language": self.language
        })
        return context


