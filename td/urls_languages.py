from django.conf.urls import patterns, url

from td.resources.views import ResourceEditView, ResourceCreateView, HomeView
from .views import (
    country_tree_data,
    country_map_data,
    upload_gateway_flag_file,
    upload_rtl_list,
    RegionListView,
    RegionDetailView,
    CountryListView,
    CountryDetailView,
    CountryEditView,
    LanguageListView,
    AjaxLanguageListView,
    AjaxLanguageGatewayListView,
    LanguageCreateView,
    LanguageDetailView,
    LanguageEditView,
    NetworkCreateView,
    NetworkDetailView,
    NetworkEditView,
    NetworkListView
)

urlpatterns = patterns(
    "",
    url(r"^$", HomeView.as_view(), name="uw_home"),
    url(r"networks/$", NetworkListView.as_view(), name="network_list"),
    url(r"networks/create/$", NetworkCreateView.as_view(), name="network_create"),
    url(r"networks/(?P<pk>\d+)/$", NetworkDetailView.as_view(), name="network_detail"),
    url(r"networks/(?P<pk>\d+)/edit/$", NetworkEditView.as_view(), name="network_edit"),

    url(r"regions/$", RegionListView.as_view(), name="region_list"),
    url(r"regions/(?P<slug>\w+)/$", RegionDetailView.as_view(), name="region_detail"),
    url(r"countries/$", CountryListView.as_view(), name="country_list"),
    url(r"countries/(?P<pk>\d+)/$", CountryDetailView.as_view(), name="country_detail"),
    url(r"countries/(?P<pk>\d+)/edit/$", CountryEditView.as_view(), name="country_edit"),
    url(r"countries/(?P<pk>\d+)/languages/create/$", LanguageCreateView.as_view(), name="language_create"),
    url(r"ajax/languages/$", AjaxLanguageListView.as_view(), name="ajax_ds_uw_languages"),
    url(r"ajax/languages_gateway/(?P<pk>\d+)/$", AjaxLanguageGatewayListView.as_view(), name="ajax_ds_uw_languages_gateway"),
    url(r"languages/$", LanguageListView.as_view(), name="language_list"),
    url(r"languages/(?P<pk>\d+)/$", LanguageDetailView.as_view(), name="language_detail"),
    url(r"languages/(?P<pk>\d+)/edit/$", LanguageEditView.as_view(), name="language_edit"),
    url(r"languages/(?P<pk>\d+)/resources/create/$", ResourceCreateView.as_view(), name="resource_create"),
    url(r"languages/(?P<pk>\d+)/resources/edit/$", ResourceEditView.as_view(), name="resource_edit"),

    url(r"gateway_language_flag/update/$", upload_gateway_flag_file, name="gateway_flag_update"),
    url(r"rtl_languages/update/$", upload_rtl_list, name="rtl_languages_update"),

    url(r"country_gateways.json$", country_tree_data, name="country_tree_data"),
    url(r"country_map_data.json$", country_map_data, name="country_map_data"),
)
