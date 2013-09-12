
from django.template.response import TemplateResponse

# Api specific
from API.v3.resources.model_resources import *
from API.v3.resources.activity_view_resources import *

import json
from django.db import connection
from django.http import HttpResponse
from geodata.data_backup.country_data import countryData

def docs_index(request):
    context = dict()
    context['title'] = 'Documentation'
    t = TemplateResponse(request, 'base.html', context)
    return t.render()

def docs_start(request):
    context = dict()
    context['title'] = 'Getting started'
    t = TemplateResponse(request, 'documentation/start.html', context)
    return t.render()

def docs_resources(request):
    context = dict()
    context['title'] = 'Resources'
    context['resources'] = dict(
        organisation = OrganisationResource.__name__,
        organisation_doc = OrganisationResource.__doc__,
        activity = ActivityResource.__name__,
        activity_doc = ActivityResource.__doc__,
        country = CountryResource.__name__,
        country_doc = CountryResource.__doc__,
        region = RegionResource.__name__,
        region_doc = RegionResource.__doc__,
        sector = SectorResource.__name__,
        sector_doc = SectorResource.__doc__,
    )
    t = TemplateResponse(request, 'documentation/resources.html', context)
    return t.render()

def docs_filtering(request):
    context = dict()
    context['title'] = 'Filtering'
    t = TemplateResponse(request, 'documentation/filtering.html', context)
    return t.render()

def docs_ordering(request):
    context = dict()
    context['title'] = 'Ordering'
    t = TemplateResponse(request, 'documentation/ordering.html', context)
    return t.render()

def docs_about(request):
    context = dict()
    context['title'] = 'About'
    t = TemplateResponse(request, 'documentation/about.html', context)
    return t.render()




def make_where_query(values, name):
    query = ''
    if values:
        if not values[0]:
            return None

        for v in values:
            query += '  ' + name + ' = "' + v +'" OR'
        query = query[:-2]
    return query

def get_and_query(request, parameter, queryparameter):

    filters = request.GET.get(parameter, None)
    if filters:
        query = make_where_query(values=filters.split(','), name=queryparameter)
        query += ') AND ('
    else:
        query = ''
    return query

def get_fields(cursor):
    desc = cursor.description
    results = [
    dict(zip([col[0] for col in desc], row))
    for row in cursor.fetchall()
    ]
    return results

def get_filter_query(filters):
    q= ''

    for f in filters:
        if f[f.keys()[0]]:
            values = f[f.keys()[0]].split(',')
        else:
            values = None
        q += make_where_query(values=values, name=f.keys()[0]) + ') and ('

    q = q.replace(' and ()', '')
    q = q[:-5]
    q = " AND (" + q
    try:
        q[8]
        return q
    except IndexError:
        return ''

def find_polygon(iso2):
    polygon = None
    for k in countryData['features']:
        try:
            if k['properties']['iso2'] == iso2:
                polygon = k['geometry']
        except KeyError:
            pass
    if polygon:
        return polygon
    else:
        return 'Polygon'



def indicator_data_response(request):

    country_q = get_and_query(request, 'countries', 'c.code')
    region_q = get_and_query(request, 'regions', 'dac_region_code')
    year_q = get_and_query(request, 'years', 'id.year')
    indicator_q = get_and_query(request, 'indicators', 'indicator_id')

    if not indicator_q:
        indicator_q = ' indicator_id = "population"'

    filter_string = '  (' + country_q + region_q + year_q + indicator_q + ')'

    if 'AND ()' in filter_string:
        filter_string = filter_string[:-6]

    cursor = connection.cursor()

    cursor.execute('SELECT da.name as indicator_id, da.friendly_label, da.type_data, c.name as country_name, c.dac_region_code, '
                   'c.dac_region_name, id.value, id.year, AsText(c.center_longlat) as loc, c.code as country_id '
                   'FROM indicators_indicator_data id '
                   'LEFT OUTER JOIN geodata_country c ON id.country_id = c.code '
                   'JOIN indicators_indicator da ON da.name = id.indicator_id WHERE %s' % (filter_string))
    cursor_max = connection.cursor()

    cursor_max.execute('SELECT max(value) as max_value FROM indicators_indicator_data WHERE %s' % indicator_q)
    result_max = cursor_max.fetchone()
    desc = cursor.description
    results = [
    dict(zip([col[0] for col in desc], row))
    for row in cursor.fetchall()
    ]
    country = {}
    for r in results:

        try:
            country[r['country_id']]['years']
        except:
            loc = r['loc']
            if loc:

                loc = loc.replace("POINT(", "")
                loc = loc.replace(")", "")
                loc_array = loc.split(" ")
                longitude = loc_array[0]
                latitude = loc_array[1]
            else:
                longitude = None
                latitude = None

            country[r['country_id']] = {'name' : r['country_name'], 'country_id' : r['country_id'], 'longitude' : longitude, 'latitude' : latitude, 'indicator_friendly' : r['friendly_label'], 'type_data' : r['type_data'] , 'indicator' : r['indicator_id'],  'years' : {}}

        year = {}
        year['y' + str(r['year'])] = r['value']
        country[r['country_id']]['years'].update(year)

    country['max_value'] = result_max[0]

    return HttpResponse(json.dumps(country), mimetype='application/json')


def activity_filter_options(request):
    cursor = connection.cursor()
    q_organisations = request.GET.get('organisation', None);
    q_organisations_and = ""
    if q_organisations:
        q_organisations_and = 'AND a.reporting_organisation_id = "' + q_organisations + '"'

    query = 'SELECT DISTINCT s.code as sector_id, s.name as sector_name, c.code as country_id, c.name as country_name, r.code as region_id, r.name as region_name  '\
                   'FROM iati_activity a '\
                   'LEFT JOIN iati_activity_recipient_region ir ON a.id = ir.activity_id '\
                   'LEFT JOIN geodata_region r ON r.code = ir.region_id '\
                   'LEFT JOIN iati_activity_recipient_country ic ON a.id = ic.activity_id '\
                   'LEFT JOIN geodata_country c ON ic.country_id = c.code '\
                   'LEFT JOIN iati_activity_sector ias ON a.id = ias.activity_id '\
                   'LEFT JOIN iati_sector s ON ias.sector_id = s.code '\
                   'WHERE 1 %s' % q_organisations_and
    cursor.execute(query)
    results = get_fields(cursor=cursor)
    countries = {}
    countries['countries'] = {}
    countries['regions'] = {}
    countries['sectors'] = {}

    for r in results:

        if r['country_name']:
            countries['countries'][r['country_id']] = r['country_name']
        if r['sector_name']:
            countries['sectors'][r['sector_id']] = r['sector_name']
        if r['region_name']:
            countries['regions'][r['region_id']] = r['region_name']

    return HttpResponse(json.dumps(countries), mimetype='application/json')



def indicator_filter_options(request):

    city_q = get_and_query(request, 'cities', 'city.id')
    country_q = get_and_query(request, 'countries', 'country.code')
    region_q = get_and_query(request, 'regions', 'region.code')
    indicator_q = get_and_query(request, 'indicators', 'i.indicator_id')

    # if not indicator_q:
        # indicator_q = ' i.indicator_id = "cpi_5_dimensions"'

    filter_string = ' AND (' + city_q + country_q + region_q + indicator_q + ')'
    if 'AND ()' in filter_string:
        filter_string = filter_string[:-6]
    cursor = connection.cursor()
    cursor.execute('SELECT DISTINCT i.indicator_id ,ind.friendly_label, city.id as city_id, city.name as city_name, country.code as country_id, country.name as country_name, region.code as region_id, region.name as region_name '
                   'FROM indicators_indicator_data i '
                   'JOIN indicators_indicator ind ON i.indicator_id = ind.name '
                   'LEFT OUTER JOIN geodata_city city ON i.city_id=city.id '
                   'LEFT OUTER JOIN geodata_country country on i.country_id = country.code '
                   'LEFT OUTER JOIN geodata_region region on country.region_id = region.code '
                   'WHERE 1 %s' % (filter_string))

    desc = cursor.description
    results = [
    dict(zip([col[0] for col in desc], row))
    for row in cursor.fetchall()
    ]

    regions = {}
    countries = {}
    cities = {}
    indicators = {}
    jsondata = {}

    for r in results:

        region = {}
        if r['region_id']:
            region[r['region_id']] = r['region_name']
            regions.update(region)

        country = {}
        if r['country_id']:
            country[r['country_id']] = r['country_name']
            countries.update(country)

        city = {}
        if r['city_id']:
            city[r['city_id']] = r['city_name']
            cities.update(city)

        indicator = {}
        if r['indicator_id']:
            indicator[r['indicator_id']] = r['friendly_label']
            indicators.update(indicator)

    jsondata['regions'] = regions
    jsondata['countries'] = countries
    jsondata['cities'] = cities
    jsondata['indicators'] = indicators

    return HttpResponse(json.dumps(jsondata), mimetype='application/json')




def json_activities_response(request):

    city_q = get_and_query(request, 'cities', 'city.id')
    country_q = get_and_query(request, 'countries', 'country.code')
    region_q = get_and_query(request, 'regions', 'region.code')
    budget_q = get_and_query(request, 'indicators', 'i.indicator_id')
    organisation_q = get_and_query(request, 'indicators', 'i.indicator_id')

    q_countries = { 'country_id' :request.GET.get('countries', None)}
    q_sectors = {'sector_id' : request.GET.get('sectors', None)}
    q_regions = {'dac_region_code' :request.GET.get('regions', None)}
    q_budget = {'total_budget' : request.GET.get('budget', None)}
    q_organisations = {'reporting_organisation_id' : request.GET.get('organisations', None)}

    filters = []

    filters.append(q_organisations)
    filters.append(q_countries)
    filters.append(q_regions)

    filter_region = []
    filter_region.append(q_regions)
    filter_sector = []
    filter_sector.append(q_sectors)

    if request.GET.get('sectors', None):
        where_sector =  ' Where ' + str(get_filter_query(filters=filter_sector)[4:])
        where_sector = ' and a.id in (select activity_id from iati_activity_sector s %s)  ' % where_sector
    else:
        where_sector = ''

    if q_budget['total_budget']:
        query_having = 'having total_budget ' + q_budget['total_budget'].split(',')[0]
    else:
        query_having = ''

    query_string = get_filter_query(filters=filters)
    query_string = query_string.replace('AND () and' , ' (')

    cursor = connection.cursor()

    query = 'SELECT c.country_id, count(a.id) as total_projects, cd.name as country_name, sum(b.value) as total_budget, cd.region_id '\
            'FROM iati_activity a '\
            'LEFT JOIN iati_budget b ON b.activity_id = a.id '\
            'LEFT JOIN iati_activity_recipient_country c ON c.activity_id = a.id '\
            'LEFT JOIN geodata_country cd ON c.country_id = cd.code '\
            'WHERE 1' \
            ' %s %s '\
            'GROUP BY c.country_id %s' % (query_string, where_sector, query_having)
    cursor.execute(query)

    activity_result = {}
    activity_result = {'type' : 'FeatureCollection', 'features' : []}

    activities = []

    results = get_fields(cursor=cursor)
    for r in results:
        country = {}
        country['type'] = 'Feature'
        country['id'] = r['country_id']
        country['properties'] = {'name' : r['country_name'], 'project_amount' : r['total_projects'], 'total_budget' : str(r['total_budget'])}

        country['geometry'] = find_polygon(r['country_id'])

        activities.append(country)

    result = {}

    activity_result['features'] = activities
    return HttpResponse(json.dumps(activity_result), mimetype='application/json')