# tasks.py
from iati_synchroniser.models import IatiXmlSource
from django_rq import job
import django_rq
from django.http import HttpResponse
import datetime


###############################
######## WORKER TASKS  ########
###############################

@job
def start_worker(queue_name):
    worker = django_rq.get_worker(queue_name)
    worker.work()

@job
def start_parser_worker():
    worker = django_rq.get_worker('parser') # Returns a worker for "parser" queue
    worker.work()

def advanced_start_worker():
    from rq import Connection, Queue, Worker
    with Connection():
        queue = django_rq.get_queue('parser')
        w = Worker(queue)
        w.work()

###############################
######## PARSING TASKS ########
###############################

@job
def parse_all_existing_sources():
    for e in IatiXmlSource.objects.all():
        django_rq.enqueue(parse_source_by_url, e.source_url)


@job
def get_new_sources_from_iati_api():
    from iati_synchroniser.dataset_syncer import DatasetSyncer
    ds = DatasetSyncer()
    ds.synchronize_with_iati_api(1)


@job
def parse_source_by_url(url):
    if IatiXmlSource.objects.filter(source_url=url).exists():
        xml_source = IatiXmlSource.objects.get(source_url=url)
        xml_source.process()


@job
def parse_all_not_parsed_in_x_days(days):
    for source in IatiXmlSource.objects.all():
        curdate = float(datetime.datetime.now().strftime('%s'))
        last_updated = float(source.date_updated.strftime('%s'))

        update_interval_time = 24 * 60 * 60 * int(days)

        if ((curdate - update_interval_time) > last_updated):
            source.save()

@job
def parse_all_over_parse_interval():
    for source in IatiXmlSource.objects.all():
        curdate = float(datetime.datetime.now().strftime('%s'))
        last_updated = float(source.date_updated.strftime('%s'))
        update_interval = source.update_interval

        if update_interval == "day":
            update_interval_time = 24 * 60 * 60
        if update_interval == "week":
            update_interval_time = 24 * 60 * 60 * 7
        if update_interval == "month":
            update_interval_time = 24 * 60 * 60 * 7 * 4.34
        if update_interval == "year":
            update_interval_time = 24 * 60 * 60 * 365

        if ((curdate - update_interval_time) > last_updated):
            source.save()


###############################
#### IATI MANAGEMENT TASKS ####
###############################

@job
def sync_codelist():
    from iati_synchroniser.codelist_importer import CodeListImporter
    syncer = CodeListImporter()

    syncer.synchronise_with_codelists()


###############################
######## GEODATA TASKS ########
###############################

@job
def update_all_geo_data():
    raise Exception("Not implemented yet")


###############################
######## INDICATOR TASKS ########
###############################

@job
def update_all_indicator_data():
    raise Exception("Not implemented yet")


###############################
######## CACHING TASKS ########
###############################

@job
def update_existing_api_call_caches():
    from cache.validator import Validator
    v = Validator()
    v.update_cache_calls()

@job
def cache_long_api_calls():
    from cache.validator import Validator
    v = Validator()
    v.update_response_times_and_add_to_cache()


def delete_task_from_queue(job_id):
    from rq import cancel_job
    from rq import Connection
    with Connection():
        cancel_job(job_id)

def delete_all_tasks_from_queue(queue_name):
    if queue_name == "failed":
        q = django_rq.get_failed_queue()
    elif queue_name == "parser":
        q = django_rq.get_queue("parser")
    else:
        q = django_rq.get_queue("default")

    while True:
        job = q.dequeue()
        if not job:
            break
        job.delete()