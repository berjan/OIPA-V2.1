# Django specific
from django.conf.urls import *

urlpatterns = patterns('',

    # Task queue management
    (r'^start_worker_with_supervisor/', 'task_queue.views.start_worker_with_supervisor'),
    (r'^get_workers/', 'task_queue.views.get_workers'),
    (r'^delete_task_from_queue/', 'task_queue.views.delete_task_from_queue'),
    (r'^delete_all_tasks_from_queue/', 'task_queue.views.delete_all_tasks_from_queue'),
    (r'^get_current_job/', 'task_queue.views.get_current_job'),
    (r'^get_queue/', 'task_queue.views.get_queue'),

    (r'^test/', 'task_queue.views.test'),

    # Callable tasks
    (r'^add_task/', 'task_queue.views.add_task'),

    # Schedule management
    (r'^start_scheduler/', 'task_queue.views.start_scheduler'),
    (r'^add_scheduled_task/', 'task_queue.views.add_scheduled_task'),
    (r'^cancel_scheduled_task/', 'task_queue.views.cancel_scheduled_task'),
    (r'^get_scheduled_tasks/', 'task_queue.views.get_scheduled_tasks'),

    #Failed task management
    (r'^get_failed_tasks/', 'task_queue.views.get_failed_tasks'),
    (r'^reschedule_all_failed/', 'task_queue.views.reschedule_all_failed'),

    # task queue pages
    (r'', include('django_rq.urls')),
)


