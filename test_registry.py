import json
import os
import pytest
import random
import rawes
import registry
import requests
import shutil
import yaml
from datetime import datetime
from django.test import RequestFactory
from PIL import Image
from pycsw.core import config
from pycsw.core.admin import delete_records
from pycsw.core.etree import etree

catalog_slug = 'test'
catalog_search_api = '/catalog/{0}/api/'.format(catalog_slug)

registry.MAPPROXY_ERROR_IMAGES = True

default_params = {
    "q_time": "[* TO *]",
    "q_geo": "[-90,-180 TO 90,180]",
    "d_docs_limit": 0,
    "d_docs_page": 1,
    "d_docs_sort": "score"
}

layers_list = [
    {
        'identifier': 'f28ad41b-b91f-4d5d-a7c3-4b17dfaa5170',
        'title': 'layer_1 titleterm1',
        'creator': 'user_1',
        'lower_corner_1': -40.0,
        'upper_corner_1': -20.0,
        'lower_corner_2': -40.0,
        'upper_corner_2': -20.0,
        'title_alternate': '0',
        'registry_tag': 'vehicula',
        'i': 0,
        'source': 'None',
        'type': 'ESRI:ArcGIS:ImageServer',
        'references_scheme': 'WWW:LINK',
        'references_url': 'http://some_url.com/rest/services/some_service/some_layer',
        'modified': datetime(2000, 3, 1, 0, 0, 0, tzinfo=registry.TIMEZONE)
    },
    {
        'identifier': '0cbd4894-c9d2-4624-b4fc-ea66d2d1c71c',
        'title': 'Part of Section 2 : New York City.',
        'creator': 'user_1',
        'lower_corner_1': 40.72,
        'upper_corner_1': 40.74,
        'lower_corner_2': -74.0,
        'upper_corner_2': -73.98,
        'title_alternate': '234',
        'registry_tag': 'tag_2',
        'source': 'http://maps.nypl.org/warper/maps/wms/8198?',
        'i': 1,
        'type': 'dataset',
        'references_scheme': 'WWW:LINK',
        'references_url': 'http://some_url2.com/rest/services/some_service/some_layer',
        'modified': datetime(2001, 3, 1, 0, 0, 0, tzinfo=registry.TIMEZONE)
    },
    {
        'identifier': '9eb27aec-15d0-47c5-bfea-5a5279f77394',
        'title': 'layer_3 titleterm3',
        'creator': 'user_2',
        'lower_corner_1': 40.0,
        'upper_corner_1': 20.0,
        'lower_corner_2': 40.0,
        'upper_corner_2': 20.0,
        'title_alternate': '566',
        'registry_tag': 'vehicula',
        'i': 2,
        'type': 'ESRI:ArcGIS:MapServer',
        'source': 'None',
        'references_scheme': 'OGC:WMS',
        'references_url': 'http://some_wms_service/wms/2',
        'modified': datetime(2002, 3, 1, 0, 0, 0, tzinfo=registry.TIMEZONE)
    },
    {
        'identifier': 'baad8665-34fb-4e4a-85a3-158e6f350201',
        'title': 'layer_4 titleterm4',
        'creator': 'user_2',
        'lower_corner_1': 40.0,
        'upper_corner_1': 20.0,
        'lower_corner_2': -40.0,
        'upper_corner_2': -20.0,
        'title_alternate': '4234',
        'registry_tag': 'tag_2',
        'i': 3,
        'type': 'ESRI:ArcGIS:MapServer',
        'source': 'None',        
        'modified': datetime(2003, 3, 1, 0, 0, 0, tzinfo=registry.TIMEZONE)
    },{
        'identifier': 'e1142992-9368-481a-8db0-dcfa5a57a7f3',
        'title': 'layer_5 titleterm4',
        'creator': 'user_2',
        'lower_corner_1': 50.0,
        'upper_corner_1': 20.0,
        'lower_corner_2': -40.0,
        'upper_corner_2': -20.0,
        'title_alternate': '1',
        'registry_tag': 'tag_wms',
        'i': 4,
        'format': 'OGC:WMS',
        'type': 'dataset',
        'source' : 'None',
        'modified': datetime(2004, 3, 1, 0, 0, 0, tzinfo=registry.TIMEZONE)
    },
    {
        'identifier': 'e1142992-9368-481a-8db0-dcfa5a57a7g3',
        'title': 'layer_6 titleterm4',
        'creator': 'user_3',
        'title_alternate': '7',
        'registry_tag': 'not',
        'i': 5,
        'format': 'OGC:WMS',
        'type': 'dataset',
        'source' : 'None',
        'modified': datetime(2004, 3, 1, 0, 0, 0, tzinfo=registry.TIMEZONE)
    }
]

@pytest.mark.skip(reason='')
def get_xml_block(dictionary):
    xml_block = (
        '  <csw:Record xmlns:registry="http://gis.harvard.edu/HHypermap/registry/0.1" >\n'
        '    <dc:identifier>%s</dc:identifier>\n'
        '    <dc:title>%s</dc:title>\n'
        '    <dc:creator>%s</dc:creator>\n'
        '    <dc:type>%s</dc:type>\n'
        '    <dct:alternative>%s</dct:alternative>\n'
        '    <dct:modified>%s</dct:modified>\n'
        '    <dct:abstract>Augue purus abstractterm%d vehicula ridiculus eu donec et eget '
        'sit justo. Fames dolor ipsum dignissim aliquet. Proin massa congue '
        'lorem tortor facilisis feugiat vitae ut. Purus justo cum arcu '
        'nascetur etiam hymenaeos volutpat amet. Lacus curae cras quam eni '
        'mi odio purus venenatis massa a elit parturient. Porta lacus '
        'lacinia lectus ad semper sociosqu. Augue neque vel. Neque fusce a'
        'ante ipsum sem ornare fames nisl fames curabitur auctor. Dolor '
        'class praesent curabitur id venenatis potenti auctor dis nec. '
        'Massa magna semper eu bibendum amet. Velit fusce rhoncus ultrices '
        'commodo cras enim curabitur. Proin vitae mus ante luctus ut orci '
        'sociosqu nonummy integer nisi a proin. Justo augue libero. Felis '
        'massa potenti. Fusce dolor iaculis tempor eu. Massa velit. Risus '
        'metus enim molestie sed pede a amet parturient facilisis '
        'scelerisque dui nibh.</dct:abstract>\n'
        '    <dc:format>%s</dc:format>\n'
        '    <dc:source>%s</dc:source>\n'
        '    <dc:relation>%s</dc:relation>\n'
        '<registry:property name="ContactInformation/Primary/organization" value="%s"/>\n'
        '<registry:property name="category" value="Intelligence"/>\n'
    ) % (dictionary['identifier'],
         dictionary['title'],
         dictionary['creator'],
         dictionary['type'],
         dictionary['title_alternate'],
         dictionary['modified'].isoformat().split('.')[0],
         dictionary['i'],
         dictionary.get('format', 'Hypermap:WARPER'),
         dictionary['source'],
         dictionary['identifier'],
         dictionary['registry_tag'])

    if 'references_scheme' in dictionary.keys():
        references_string = (
            '    <dct:references scheme="%s">%s</dct:references>') % (dictionary['references_scheme'],
                                                                      dictionary['references_url'])
        xml_block += references_string

    if 'lower_corner_1' in dictionary.keys():
        bbox_string = (
            '    <ows:BoundingBox crs="http://www.opengis.net/def/crs/EPSG/0/4326" dimensions="2">\n'
            '        <ows:LowerCorner>%4f %4f</ows:LowerCorner>\n'
            '        <ows:UpperCorner>%4f %4f</ows:UpperCorner>\n'
            '    </ows:BoundingBox>\n'
        ) % (dictionary['lower_corner_1'],
             dictionary['lower_corner_2'],
             dictionary['upper_corner_1'],
             dictionary['upper_corner_2'])
        xml_block += bbox_string

    xml_block += '    </csw:Record>\n'

    return xml_block


@pytest.mark.skip(reason='')
def create_layers_list(records_number):
    layers = [
        {
            'identifier': random.randint(1e6, 1e7),
            'title': 'Random data',
            'creator': 'Random user',
            'type': 'dataset',
            'modified': datetime(random.randint(1950, 2000),
                                 random.randint(1, 12),
                                 random.randint(1, 28),
                                 tzinfo=registry.TIMEZONE),
            'lower_corner_1': random.uniform(-90, 0),
            'lower_corner_2': random.uniform(-180, 0),
            'upper_corner_1': random.uniform(0, 90),
            'title_alternate': 'random_id',
            'i': item,
            'source': 'Random source',
            'registry_tag': 'random_tag',
            'upper_corner_2': random.uniform(0, 180)
        } for item in range(records_number)
    ]

    return layers


@pytest.mark.skip(reason='')
def construct_payload(*args, **kwargs):
    xml_string = (
        '<csw:Transaction xmlns:csw="http://www.opengis.net/cat/csw/2.0.2" '
        'xmlns:ows="http://www.opengis.net/ows" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:schemaLocation="http://www.opengis.net/cat/csw/2.0.2 '
        'http://schemas.opengis.net/csw/2.0.2/CSW-publication.xsd" '
        'service="CSW" version="2.0.2" xmlns:dc="http://purl.org/dc/'
        'elements/1.1/" xmlns:dct="http://purl.org/dc/terms/" '
        'xmlns:registry="http://gis.harvard.edu/HHypermap/registry/0.1" >\n'
        '<csw:Insert>\n'
    )

    end_part = ('  </csw:Insert>\n'
                '</csw:Transaction>')

    try:
        layers_list = kwargs['layers_list']
    except KeyError:
        layers_list = create_layers_list(kwargs['records_number'])

    for item in layers_list:
        xml_block = get_xml_block(item)
        xml_string += xml_block

    xml_string += end_part
    return xml_string


@pytest.mark.skip(reason='')
def get_number_records(request):
    parsed = etree.fromstring(request.content,
                              etree.XMLParser(resolve_entities=False))
    search_param = '{http://www.opengis.net/cat/csw/2.0.2}SearchResults'
    search_results = parsed.findall(search_param)[0]

    return int(search_results.attrib['numberOfRecordsMatched'])


def test_create_catalog(client):
    # Test empty list of catalogs.
    response = client.get('/catalog')
    assert 404 == response.status_code
    assert 'Empty' in response.content.decode('utf-8')

    response = client.put('/catalog/{0}/csw'.format(catalog_slug))
    assert 200 == response.status_code
    assert 'created' in response.content.decode('utf-8')

    # List indices.
    response = client.get('/catalog')
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert 1 == len(results)
    assert response.get('Content-Type') == 'application/json'


def test_single_transaction(client):
    # Create payload and insert data into both pycsw database and elasticsearch.
    payload = construct_payload(layers_list=layers_list[:2])
    response = client.post('/catalog/{0}/csw'.format(catalog_slug), payload, content_type='text/xml')
    assert 200 == response.status_code

    # Provisional hack to refresh documents in elasticsearch.
    es_client = rawes.Elastic(registry.REGISTRY_SEARCH_URL)
    es_client.post('/_refresh')

    # Verify records have been added into both pycsw.
    repository = registry.RegistryRepository()
    records_number = int(repository.query('')[0])
    assert 2 == records_number

    # Verify records added into elasticsearch using the search api.
    response = client.get(catalog_search_api)
    assert 200 == response.status_code
    search_response = json.loads(response.content.decode('utf-8'))
    assert 2 == search_response['a.matchDocs']
    assert response.get('Content-Type') == 'application/json'

    # Remove records using individual requests.
    request_string = (
        '<csw:Transaction xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:ogc="http://www.opengis.net/ogc" '
        'xmlns:csw="http://www.opengis.net/cat/csw/2.0.2" '
        'xmlns:ows="http://www.opengis.net/ows" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:schemaLocation="http://www.opengis.net/cat/csw/2.0.2 '
        'http://schemas.opengis.net/csw/2.0.2/CSW-publication.xsd" service="CSW" version="2.0.2">\n'
        '  <csw:Delete>\n'
        '    <csw:Constraint version="1.1.0">\n'
        '      <ogc:Filter>\n'
        '        <ogc:PropertyIsLike wildCard="%" singleChar="." escapeChar="\">\n'
        '          <ogc:PropertyName>dc:identifier</ogc:PropertyName>\n'
        '          <ogc:Literal>{0}</ogc:Literal>\n'
        '        </ogc:PropertyIsLike>\n'
        '      </ogc:Filter>\n'
        '    </csw:Constraint>\n'
        '  </csw:Delete>\n'
        '</csw:Transaction>\n'
    )
    response = client.post('/catalog/{0}/csw'.format(catalog_slug), request_string.format(layers_list[0]['identifier']), content_type='text/xml')
    assert 200 == response.status_code

    response = client.post('/catalog/{0}/csw'.format(catalog_slug), request_string.format(layers_list[1]['identifier']), content_type='text/xml')
    assert 200 == response.status_code


def test_create_transaction(client):
    # Create payload and insert data into both pycsw database and elasticsearch.
    payload = construct_payload(layers_list=layers_list)
    response = client.post('/catalog/{0}/csw'.format(catalog_slug), payload, content_type='text/xml')
    assert 200 == response.status_code

    # Provisional hack to refresh documents in elasticsearch.
    es_client = rawes.Elastic(registry.REGISTRY_SEARCH_URL)
    es_client.post('/_refresh')

    # Verify records have been added into both pycsw.
    repository = registry.RegistryRepository()
    records_number = int(repository.query('')[0])
    assert len(layers_list) == records_number

    # Verify records added into elasticsearch using the search api.
    response = client.get(catalog_search_api)
    assert 200 == response.status_code
    search_response = json.loads(response.content.decode('utf-8'))
    assert len(layers_list) - 1 == search_response['a.matchDocs']
    assert response.get('Content-Type') == 'application/json'

    layer_uuid = 'f28ad41b-b91f-4d5d-a7c3-4b17dfaa5170'
    layer_dic, layer_id, index_name = registry.get_data_from_es(es_client, layer_uuid)
    assert 'layer_1 titleterm1' == layer_dic['title']
    assert 'test' == index_name


def test_parse_params(client):
    params_test = {
        "q.time": "[* TO *]",
        "q.geo": "[-90,-180 TO 90,180]",
        "d.docs.limit": 0,
        "d.docs.page": 1,
        "d.docs.sort": "score"
    }

    factory = RequestFactory()
    request = factory.get(catalog_search_api, params_test)
    parsed_url_keys = registry.parse_get_params(request).keys()

    assert_dots = ['.' in key for key in parsed_url_keys]
    assert False in assert_dots


def test_search_api(client):
    # Test configuration file for swagger api client.
    response = client.get('/api/config')
    assert 200 == response.status_code
    assert 'text/plain' in response.serialize_headers().decode('utf-8')

    response = client.get(catalog_search_api, default_params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert len(layers_list) - 1 == results['a.matchDocs']

    # Test invalidated d_docs_page.
    params = default_params.copy()
    params['d_docs_page'] = -1
    response = client.get(catalog_search_api, params)
    assert 400 == response.status_code
    params.pop('d_docs_page', None)

    # Test wrong search engine url.
    params['search_engine_endpoint'] = 'http://wrong.url:8000'
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    es_status, data = results
    assert 400 == es_status
    assert 'error' in data

    # Sort time
    params.pop('search_engine_endpoint', None)
    params['d_docs_sort'] = 'time'
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    docs = results['d.docs']
    range_dates = [int(doc['layer_date'].split('-')[0]) for doc in docs]

    for item in zip(range_dates, range_dates[1:]):
        first_year, second_year = item[0], item[1]
        assert first_year >= second_year

    # Test 404 error giving wrong search index.
    params = default_params.copy()
    wrong_search_endpoint = '/catalog/{0}/api/'.format('wrong_index')
    response = client.get(wrong_search_endpoint, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    es_status, data = results
    assert 404 == es_status
    assert 'error' in data

    # Test for original response.
    params['original_response'] = 1
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert 'a.matchDocs' not in results

    # Test search within registry tags.
    params = default_params.copy()
    params["q_text"] = "vehicula"
    params["d_docs_limit"] = 100
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert len(layers_list) - 1 == results['a.matchDocs']

    # Search only in registry subfield.
    params = default_params.copy()
    params['q_registry_text'] = 'vehicula'
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert 2 == results['a.matchDocs']

    # Get documents using an specific reference url.
    params = default_params.copy()
    params['q_references_url'] = 'http://some_url.com/rest/services/some_service/some_layer'
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert 1 == results['a.matchDocs']

    # Get documents using an specific schema url.
    params = default_params.copy()
    params['q_references_scheme'] = 'WWW:LINK'
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert 2 == results['a.matchDocs']

    # Get documents with both scheme and url references.
    params['q_references_url'] = 'http://some_url.com/rest/services/some_service/some_layer'
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert 1 == results['a.matchDocs']

    params = default_params.copy()
    params['a_categories_limit'] = 10
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert 'Intelligence' == results['a.categories'][0]['key']
    assert len(layers_list) - 1 == results['a.categories'][0]['doc_count']


@pytest.mark.skipif(os.getenv('VERSION') != '5.1',
                    reason='Test is performed only for elasticsearch with heatmap plugin')
def test_heatmap(client):
    # Test for heatmap support.
    params = default_params.copy()    
    params['a_hm_limit'] = 1
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert 5 == results['a.matchDocs'] 
    assert results['a.hm']['minY'] == -90
    assert results['a.hm']['maxY'] == 90 

    params['a_hm_filter'] = '[0,0 TO 30, 30]'
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert 5 == results['a.matchDocs']
    assert results['a.hm']['minY'] > -90
    assert results['a.hm']['maxY'] < 90

    params['a_hm_gridlevel'] = 5
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert 5 == results['a.matchDocs']
    assert results['a.hm']['gridLevel'] == 5


def test_q_text_keywords(client):
    params = default_params.copy()
    params["q_text"] = "alltext:(titleterm1+OR+abstractterm3)"
    params["d_docs_limit"] = 100

    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert 2 == results['a.matchDocs']


def test_q_text(client):
    params = default_params.copy()
    params["q_text"] = "title:\"{0}\"".format(layers_list[0]['title'])
    params["d_docs_limit"] = 100

    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert 1 == results['a.matchDocs']

    for doc in results.get("d.docs", []):
        assert layers_list[0]['title'] == doc['title']


def test_q_text_fields(client):
    params = default_params.copy()
    params["q_text"] = "{0}".format("titleterm1")
    params["q_text_fields"] = "{0}".format("title")
    params["d_docs_limit"] = 100

    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert 1 == results['a.matchDocs']

    params["q_text"] = "{0}".format("volutpat")
    params["q_text_fields"] = "{0}".format("abstract")
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert len(layers_list) - 1 == results['a.matchDocs']

    params["q_text"] = "{0} {1}".format("volutpat", "titleterm1")
    params["q_text_fields"] = "{0},{1}".format("title", "creator")
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert 1 == results['a.matchDocs']


def test_q_text_fields_boost(client):
    test_clear_records(client)
    test_create_catalog(client)
    layers = [
        {
            'identifier': 10,
            'title': 'alpha',
            'creator': 'beta',
            'lower_corner_1': -1.0,
            'upper_corner_1': -1.0,
            'lower_corner_2': -1.0,
            'upper_corner_2': -1.0,
            'i': 0,
            'title_alternate': '934',
            'registry_tag': 'notag_1',
            'type': 'ESRI:ArcGIS:ImageServer',
            'source': 'None',
            'modified': datetime(2000, 3, 1, 0, 0, 0, tzinfo=registry.TIMEZONE)
        },
        {
            'identifier': 20,
            'title': 'beta',
            'creator': 'alpha',
            'lower_corner_1': -2.0,
            'upper_corner_1': -2.0,
            'lower_corner_2': -2.0,
            'upper_corner_2': -2.0,
            'i': 1,
            'title_alternate': '935',
            'registry_tag': 'notag_2',
            'source': 'None',
            'type': 'ESRI:ArcGIS:ImageServer',
            'modified': datetime(2001, 3, 1, 0, 0, 0, tzinfo=registry.TIMEZONE)
        }
    ]
    payload = construct_payload(layers_list=layers)
    response = client.post('/catalog/{0}/csw'.format(catalog_slug), payload, content_type='text/xml')
    assert 200 == response.status_code

    # Provisional hack to refresh documents in elasticsearch.
    es_client = rawes.Elastic(registry.REGISTRY_SEARCH_URL)
    es_client.post('/_refresh')
    response = client.post('/', payload, content_type='text/xml')
    assert 200 == response.status_code

    try:
        # Boosting title will make doc 10 score higher
        params = default_params.copy()
        params["q_text"] = "{0}".format("alpha")
        params["q_text_fields"] = "{0},{1}".format("title^999.0", "layer_originator^0.1")
        params["d_docs_limit"] = 100
        response = client.get(catalog_search_api, params)
        assert 200 == response.status_code
        results = json.loads(response.content.decode('utf-8'))
        assert 2 == results['a.matchDocs']
        assert layers[0]['title'] == results.get("d.docs", [])[0]['title']
        assert layers[1]['creator'] == results.get("d.docs", [])[1]['layer_originator']

        # Boosting layer_originator will make doc 20 score higher
        params["q_text_fields"] = "{0},{1}".format("title^0.1", "layer_originator^9.0")
        response = client.get(catalog_search_api, params)
        assert 200 == response.status_code
        results = json.loads(response.content.decode('utf-8'))
        assert 2 == results['a.matchDocs']
        assert layers[0]['title'] == results.get("d.docs", [])[1]['title']
        assert layers[1]['creator'] == results.get("d.docs", [])[0]['layer_originator']

    finally:
        test_clear_records(client)
        test_create_catalog(client)
        test_create_transaction(client)


def test_q_user(client):
    params = default_params.copy()
    query_user = "user_1"
    params["q_user"] = query_user
    params["d_docs_limit"] = 100

    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert 2 == results['a.matchDocs']

    for doc in results.get("d.docs", []):
        assert query_user == doc['layer_originator']


def test_q_uuid(client):
    params = default_params.copy()
    query_uuid = 'f28ad41b-b91f-4d5d-a7c3-4b17dfaa5170'
    params["q_uuid"] = query_uuid
    params["d_docs_limit"] = 100

    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert 1 == results['a.matchDocs']

    for doc in results.get("d.docs", []):
        assert query_uuid == doc['layer_identifier']


def test_q_geo(client):
    params = default_params.copy()
    params["d_docs_limit"] = 100

    # top right square
    params["q_geo"] = "[0,0 TO 30,30]"

    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert 1 == results['a.matchDocs']

    # Bottom left
    params["q_geo"] = "[-30,-30 TO 0,0]"
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert 1 == results['a.matchDocs']

    # big square
    params["q_geo"] = "[-30,-30 TO 30,30]"
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert 4 == results['a.matchDocs']

    # center where no layers
    params["q_geo"] = "[-5,-5 TO 5,5]"
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert 0 == results['a.matchDocs']

    # Wrong format
    params["q_geo"] = "[-5,-5 5,5]"
    response = client.get(catalog_search_api, params)
    assert 400 == response.status_code


def test_q_time(client):
    params = default_params.copy()
    params["d_docs_limit"] = 100

    # test validations
    params["q_time"] = "[2000-01-01 - 2001-01-01T00:00:00]"
    response = client.get(catalog_search_api, params)
    assert 400 == response.status_code

    # Test asterisks.
    params["q_time"] = "[* TO *]"
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert len(layers_list) - 1 == results['a.matchDocs']

    # test range
    # entire year 2000
    params["q_time"] = "[2000-01-01 TO 2001-01-01T00:00:00]"
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert 1 == results['a.matchDocs']

    params["q_time"] = "[* TO 2001-01-01T00:00:00]"
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert 1 == results['a.matchDocs']

    params["q_time"] = "[2000-01-01 TO *]"
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert len(layers_list) - 1 == results['a.matchDocs']

    # Test error when q_time is not given.
    params["a_time_limit"] = 1
    params.pop('q_time', None)
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    es_status, data = results
    assert 400 == es_status
    assert 'error' in data
    assert 'q_time MUST BE initialized' in data['error']['msg']

    # Test error when a_time_gap is not given.
    params["q_time"] = "[* TO *]"
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    es_status, data = results
    assert 400 == es_status
    assert 'error' in data
    assert 'a_time_gap MUST BE initialized' in data['error']['msg']

    # test complete min and max when q time is asterisks.
    params["a_time_gap"] = "P1Y"
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert len(layers_list) - 1 == results['a.matchDocs']
    assert results["a.time"]["start"].upper() == "2000-01-01T00:00:00Z"
    assert results["a.time"]["end"].upper() == "2004-01-01T00:00:00Z"

    # Test histograms generation using time values.
    params["a_time_gap"] = "PT24H"
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert len(layers_list) - 1 == results['a.matchDocs']
    assert results["a.time"]["start"].upper() == "2000-03-01T00:00:00Z"
    assert results["a.time"]["end"].upper() == "2004-03-01T00:00:00Z"

    # Test wrong values for a_time_gap.
    params["a_time_gap"] = "P1ye"
    with pytest.raises(Exception) as excinfo:
        response = client.get(catalog_search_api, params)
    assert 'Does not match' in str(excinfo.value)

    # Test wrong values for a_time_gap.
    params["a_time_gap"] = "PT2h"
    with pytest.raises(Exception) as excinfo:
        response = client.get(catalog_search_api, params)
    assert 'Does not match' in str(excinfo.value)

    # test facets
    params["q_time"] = "[2000 TO 2022]"
    params["a_time_limit"] = 1
    params["a_time_gap"] = "P1Y"
    response = client.get(catalog_search_api, params)
    assert 200 == response.status_code

    results = json.loads(response.content.decode('utf-8'))
    assert len(layers_list) - 1 == results['a.matchDocs']
    assert results["a.time"]["end"].upper() == "2004-01-01T00:00:00Z"
    assert len(results["a.time"]["counts"]) == len(layers_list) - 1


def test_mapproxy(client):
    mapproxy_url = '/layer/f28ad41b-b91f-4d5d-a7c3-4b17dfaa5170.yml'
    response = client.get(mapproxy_url)
    assert 200 == response.status_code
    assert 'text/plain' in response.serialize_headers().decode('utf-8')

    mapproxy_url = '/layer/f28ad41b-b91f-4d5d-a7c3-4b17dfaa5170.xml'
    response = client.get(mapproxy_url)
    assert 200 == response.status_code
    assert 'application/xml' in response.serialize_headers().decode('utf-8')

    mapproxy_url = '/layer/f28ad41b-b91f-4d5d-a7c3-4b17dfaa5170.png'
    response = client.get(mapproxy_url)
    assert 200 == response.status_code
    assert 'image/png' in response.serialize_headers().decode('utf-8')

    # test xml exception response in the case of a source error
    registry.MAPPROXY_ERROR_IMAGES = False
    mapproxy_url = '/layer/f28ad41b-b91f-4d5d-a7c3-4b17dfaa5170.png'
    response = client.get(mapproxy_url)
    assert 500 == response.status_code
    assert 'application/xml' in response.serialize_headers().decode('utf-8')
    registry.MAPPROXY_ERROR_IMAGES = True

    # test the JSON view of the layer
    mapproxy_url = '/layer/f28ad41b-b91f-4d5d-a7c3-4b17dfaa5170.js'
    response = client.get(mapproxy_url)
    assert 200 == response.status_code
    assert 'application/json' in response.serialize_headers().decode('utf-8')

    mapproxy_url = '/layer/f28ad41b-b91f-4d5d-a7c3-4b17dfaa5171.yml'
    response = client.get(mapproxy_url)
    assert 404 == response.status_code

    mapproxy_url = '/layer/f28ad41b-b91f-4d5d-a7c3-4b17dfaa5171.png'
    response = client.get(mapproxy_url)
    assert 404 == response.status_code

    mapproxy_url = '/layer/f28ad41b-b91f-4d5d-a7c3-4b17dfaa5171.js'
    response = client.get(mapproxy_url)
    assert 404 == response.status_code
    assert 'not found' in response.content.decode('utf-8')

    mapproxy_url = '/layer/f28ad41b-b91f-4d5d-a7c3-4b17dfaa5171/'
    response = client.get(mapproxy_url)
    assert 404 == response.status_code

    mapproxy_url = '/layer/f28ad41b-b91f-4d5d-a7c3-4b17dfaa5170/'
    response = client.get(mapproxy_url)
    assert 200 == response.status_code

    mapproxy_url = '/layer/f28ad41b-b91f-4d5d-a7c3-4b17dfaa5170/demo/?srs=EPSG' \
                   '%3A3857&format=image%2Fpng&wms_layer=0'
    response = client.get(mapproxy_url)
    assert 200 == response.status_code


def test_reindex_records(client):
    message, status = registry.delete_index(catalog_slug)
    assert 200 == status
    assert 'removed' in message

    # Test empty list of catalogs.
    response = client.get('/catalog')
    assert 404 == response.status_code
    assert 'Empty' in response.content.decode('utf-8')

    registry.create_index(catalog_slug)
    registry.re_index_layers(catalog_slug)

    # Provisional hack to refresh documents in elasticsearch.
    es_client = rawes.Elastic(registry.REGISTRY_SEARCH_URL)
    es_client.post('/_refresh')

    response = client.get(catalog_search_api, default_params)
    assert 200 == response.status_code
    results = json.loads(response.content.decode('utf-8'))
    assert len(layers_list) - 1 == results['a.matchDocs']


def test_vcaps(client):
    SAMPLE_VCAPS = r"""{
        "searchly": [
            {
            "name": "searchly-1",
            "label": "searchly",
            "tags": [ ],
            "plan": "starter",
            "credentials": {
                "uri": "http://cloudfoundry:f0d15584ef7b5dcd1c5c1794ef3506ec@api.searchbox.io",
                "sslUri": "https://cloudfoundry:f0d15584ef7b5dcd1c5c1794ef3506ec@api.searchbox.io"
            }
            }
        ]
        }
    """
    registry_url = registry.vcaps_search_url(SAMPLE_VCAPS, 'http://localhost:8000/')
    assert registry_url == 'https://cloudfoundry:f0d15584ef7b5dcd1c5c1794ef3506ec@api.searchbox.io'


def test_utilities(client):
    # Hit the docs.
    response = client.get('/')
    assert 200 == response.status_code

    datetime_range = "[2013-03-01 TO 2014-05-02T23:00:00]"
    start, end = registry.parse_datetime_range(datetime_range)
    assert start.get("is_common_era")

    assert start.get("parsed_datetime").year == 2013
    assert start.get("parsed_datetime").month == 3
    assert start.get("parsed_datetime").day == 1
    assert end.get("is_common_era")
    assert end.get("parsed_datetime").year == 2014
    assert end.get("parsed_datetime").month == 5
    assert end.get("parsed_datetime").day == 2
    assert end.get("parsed_datetime").hour == 23
    assert end.get("parsed_datetime").minute == 0
    assert end.get("parsed_datetime").second == 0

    datetime_range = "[-500000000 TO 2014-05-02T23:00:00]"
    start, end = registry.parse_datetime_range(datetime_range)
    assert not start.get("is_common_era")
    assert start.get("parsed_datetime") == "-500000000-01-01T00:00:00Z"

    start, end = registry.parse_datetime_range("[* TO *]")
    assert start.get("is_common_era")
    assert start.get("parsed_datetime") is None
    assert end.get("parsed_datetime") is None

    # test_parse_ISO8601
    quantity, units = registry.parse_ISO8601("P3D")
    assert quantity == 3
    assert units[0] == "DAYS"

    # test_parse_geo_box
    value = registry.parse_geo_box("[-90,-180 TO 90,180]")
    assert value.bounds[0] == -90
    assert value.bounds[1] == -180
    assert value.bounds[2] == 90
    assert value.bounds[3] == 180

    line = 'fb76f1d7-55bc-4c19-9182-0dbeef4208e6 0 0 0 0 1483721501'
    uuid, reliability_dic = registry.parse_values_from_string(line)
    assert '0' == reliability_dic['valid_bbox']
    assert '0' == reliability_dic['valid_image']
    assert '0' == reliability_dic['valid_config']

    wrong_url = 'http://localhost:9500'
    with pytest.raises(requests.exceptions.ConnectionError) as excinfo:
        response = registry.es_connect(wrong_url)
    assert 'Failed to establish a new connection' in str(excinfo.value)

    check_list = [
        {
            'check_color': '1',
            'timestamp': '2017-01-11 14:30:45',
            'valid_bbox': '0',
            'valid_config': '0',
            'valid_image': '0'
        },
        {
            'check_color': '1',
            'timestamp': '2017-01-11 14:30:56',
            'valid_bbox': '0',
            'valid_config': '0',
            'valid_image': '0'
        },
        {
            'check_color': '0',
            'timestamp': '2017-01-11 14:32:26',
            'valid_bbox': '0',
            'valid_config': '0',
            'valid_image': '0'
        }
    ]
    new_dict = {
        'check_color': '0',
        'timestamp': '2017-01-11 14:32:26',
        'valid_bbox': '0',
        'valid_config': '0',
        'valid_image': '0'
    }
    assert 3 == len(check_list)
    new_list = registry.add_dict_to_list(check_list, new_dict)
    assert 4 == len(new_list)
    reliability_rate = registry.compute_reliability(new_list)
    assert 50.0 == reliability_rate

    # Creating whole white and dark images for testing.
    # We will include new pixel values as noise.
    img = Image.new('L', (200, 150))
    img.putpixel((20, 20), 172)
    img.putpixel((30, 70), 240)
    img.putpixel((120, 100), 120)
    check_color = registry.check_image(img)
    assert 1 == check_color

    img = Image.new('L', (200, 150), 255)
    img.putpixel((20, 20), 172)
    img.putpixel((30, 70), 240)
    img.putpixel((120, 100), 120)
    check_color = registry.check_image(img)
    assert 1 == check_color


def test_bad_mapproxy_config(client):
    with pytest.raises(registry.ConfigurationError) as excinfo:
        registry.configure_mapproxy({}, ignore_warnings=False)
    assert 'invalid configuration' in str(excinfo.value)


def test_check_layers():
    layer_uuid = 'f28ad41b-b91f-4d5d-a7c3-4b17dfaa5170'
    layer = registry.layer_from_csw(layer_uuid)
    _, yaml_config = registry.get_mapproxy(layer)
    valid_bbox, valid_config, valid_image, check_color = registry.check_layer(layer_uuid)
    assert 0 == valid_bbox
    assert 0 == valid_config
    assert 0 == valid_image
    assert 1 == check_color

    # Verify that recently created file exist in yml file.
    valid_config = registry.check_config(layer_uuid, yaml_config, 'yml')
    assert 0 == valid_config

    shutil.rmtree('yml')

    layer_uuid_good = '0cbd4894-c9d2-4624-b4fc-ea66d2d1c71c'
    valid_image, check_color = registry.layer_image(layer_uuid_good)
    assert 0 == valid_image
    assert 0 == check_color

    yaml_text = yaml.load(yaml_config)

    # Test url with None.
    yaml_text['sources']['default_source']['req']['url'] = None
    valid_config = registry.check_config(layer_uuid, yaml.dump(yaml_text, default_flow_style=False), 'yml')
    assert 1 == valid_config

    # Remove dictionary keys from yaml file.
    services = yaml_text.pop('services', None)
    valid_bbox = registry.check_bbox(yaml_text)
    assert 1 == valid_bbox
    yaml_text['services'] = services

    # Removing wms value.
    wms = yaml_text['services'].pop('wms', None)
    valid_bbox = registry.check_bbox(yaml_text)
    assert 1 == valid_bbox
    yaml_text['services']['wms'] = wms

    # Removing bounding box value.
    bbox = yaml_text['services']['wms'].pop('bbox', None)
    valid_bbox = registry.check_bbox(yaml_text)
    assert 1 == valid_bbox

    # Incomplete number of coordinates.
    yaml_text['services']['wms']['bbox'] = '-40.0000,-40.0000,-20.0000'
    valid_bbox = registry.check_bbox(yaml_text)
    assert 1 == valid_bbox

    # Upper left less than -180 in x.
    yaml_text['services']['wms']['bbox'] = '-191.0000,-40.0000,-20.0000,-20.0000'
    valid_bbox = registry.check_bbox(yaml_text)
    assert 1 == valid_bbox

    # Upper left less than -90 in y.
    yaml_text['services']['wms']['bbox'] = '-40.0000,-100.0000,-20.0000,-20.0000'
    valid_bbox = registry.check_bbox(yaml_text)
    assert 1 == valid_bbox

    # Lower right higher than 180 in x.
    yaml_text['services']['wms']['bbox'] = '-40.0000,-40.0000,500.0000,-20.0000'
    valid_bbox = registry.check_bbox(yaml_text)
    assert 1 == valid_bbox

    # Lower right higher than 90 in y.
    yaml_text['services']['wms']['bbox'] = '-40.0000,-40.0000,-20.0000,500.0000'
    valid_bbox = registry.check_bbox(yaml_text)
    assert 1 == valid_bbox

    # Create wrong yml configuration file.
    wrong_yml = 'h1 { font-weight:normal; }'
    valid_config = registry.check_config('wrong_uuid', wrong_yml, 'yml')
    assert 1 == valid_config


def test_clear_records(client):
    response = client.delete('/catalog/{0}/csw'.format(catalog_slug))
    assert 200 == response.status_code
    assert 'removed' in response.content.decode('utf-8')

    # Delete records in pycsw database.
    context = config.StaticContext()
    delete_records(context,
                   registry.PYCSW['repository']['database'],
                   registry.PYCSW['repository']['table'])

    # Delete a catalog that has not been created previosuly.
    response = client.delete('/catalog/boom/csw')
    assert 404 == response.status_code
    assert 'does not exist' in response.content.decode('utf-8')


def test_elasticsearch(client):
    test_create_catalog(client)

    # Test when there is no connection in elasticsearch, add records to pycsw.
    payload = construct_payload(records_number=1)
    temp = registry.REGISTRY_SEARCH_URL
    registry.REGISTRY_SEARCH_URL = 'http://localhost:9500'
    response = client.post('/catalog/{0}/csw'.format(catalog_slug), payload, content_type='text/xml')

    repository = registry.RegistryRepository()
    number_records_matched = int(repository.query('')[0])
    assert 1 == number_records_matched
    registry.REGISTRY_SEARCH_URL = temp

    payload = construct_payload(records_number=3)
    response = client.post('/catalog/not_es/csw'.format(catalog_slug), payload, content_type='text/xml')
    assert 200 == response.status_code

    wrong_bbox_record = layers_list[0].copy()
    wrong_bbox_record['upper_corner_1'] = wrong_bbox_record['upper_corner_1'] + 5000
    wrong_bbox_record['upper_corner_2'] = wrong_bbox_record['upper_corner_2'] + 5000
    wrong_bbox_record['lower_corner_1'] = wrong_bbox_record['lower_corner_1'] + 5000
    wrong_bbox_record['lower_corner_2'] = wrong_bbox_record['lower_corner_2'] + 5000

    payload = construct_payload(layers_list=[wrong_bbox_record])
    response = client.post('/catalog/{0}/csw'.format(catalog_slug), payload, content_type='text/xml')
    assert 200 == response.status_code

    test_clear_records(client)


if __name__ == '__main__':
    pytest.main()
