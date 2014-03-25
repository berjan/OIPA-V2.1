from django.contrib import admin
from indicator.models import Indicator, IndicatorData, IndicatorSource, IncomeLevel, LendingType, IndicatorTopic
from django.conf.urls import patterns
from indicator.admin_tools import IndicatorAdminTools
from django.http import HttpResponse
from indicator.wbi_parser import WBI_Parser


class IndicatorAdmin(admin.ModelAdmin):

    def get_urls(self):
        urls = super(IndicatorAdmin, self).get_urls()

        my_urls = patterns('',
            (r'^update-indicator/$', self.admin_site.admin_view(self.update_indicators)),
            (r'^update-indicator-data/$', self.admin_site.admin_view(self.update_indicator_data)),
            (r'^update-indicator-city-data/$', self.admin_site.admin_view(self.update_indicator_city_data)),
            (r'^update-wbi-indicator/$', self.admin_site.admin_view(self.update_WBI_indicators))
        )
        return my_urls + urls

    def update_indicator_data(self, request):
        admTools = IndicatorAdminTools()
        admTools.update_indicator_data()
        return HttpResponse('Success')

    def update_indicator_city_data(self, request):
        admTools = IndicatorAdminTools()
        admTools.update_indicator_city_data()
        return HttpResponse('Success')

    def update_indicators(self, request):
        admTools = IndicatorAdminTools()
        admTools.update_indicators()
        return HttpResponse('Success')

    def update_WBI_indicators(self, request):
        wbi_parser = WBI_Parser()
        wbi_parser.import_wbi_indicators()
        return HttpResponse('Success')

class IndicatorDataAdmin(admin.ModelAdmin):
    list_display = ['indicator', 'city','country', 'region', 'year', 'value']
    search_fields = ['year', 'indicator__friendly_label', 'value']
    list_filter = ['indicator', 'city', 'country', 'year']



admin.site.register(Indicator, IndicatorAdmin)
admin.site.register(IndicatorData, IndicatorDataAdmin)
admin.site.register(IndicatorSource)
admin.site.register(IncomeLevel)
admin.site.register(LendingType)
admin.site.register(IndicatorTopic)

