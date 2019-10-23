import os
from celery import Celery
from celery.schedules import crontab, schedule
from datetime import timedelta


class MySchedule(schedule):
    def __init__(self, run_every=None, offset=None):
        self._run_every = run_every
        self._offset = offset if offset is not None else timedelta(seconds=0)
        self._do_offset = True if self._offset else False
        super(MySchedule, self).__init__(run_every=self._run_every + self._offset)

    def is_due(self, last_run_at):
        ret = super(MySchedule, self).is_due(last_run_at)
        if self._do_offset and ret.is_due:
            self._do_offset = False
            self.run_every = self._run_every
            ret = super(MySchedule, self).is_due(last_run_at)
        return ret

    def __reduce__(self):
        return self.__class__, (self._run_every, self._offset)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quiz_project.settings")

app = Celery("quiz_project")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "matchmaking": {
        "task": "quiz.tasks.matchmaking",
        "schedule": MySchedule(
            run_every=timedelta(seconds=2), offset=timedelta(seconds=0.7)
        ),
    },
    "lottery": {
        "task": "quiz.tasks.lottery",
        "schedule": MySchedule(run_every=timedelta(seconds=10)),
    },
    "update_matches": {
        "task": "quiz.tasks.update_matches",
        "schedule": MySchedule(run_every=timedelta(seconds=2)),
    },
    "update_matches2": {
        "task": "quiz.tasks.update_matches2",
        "schedule": MySchedule(
            run_every=timedelta(seconds=2), offset=timedelta(seconds=1)
        ),
    },
    "bot_invite_reply": {
        "task": "quiz.tasks.bot_invite_reply",
        "schedule": MySchedule(run_every=timedelta(seconds=5)),
    },
    "cycle": {
        "task": "quiz.tasks.cycle",
        "schedule": MySchedule(
            run_every=timedelta(seconds=5), offset=timedelta(seconds=1)
        ),
    },
}
