from __future__ import absolute_import

import datetime

from flask import current_app
import cloudstorage as gcs
from werkzeug import secure_filename
from werkzeug.exceptions import BadRequest
from google.appengine.api import app_identity
import logging

bucket = app_identity.get_default_gcs_bucket_name()
write_retry_params = gcs.RetryParams(backoff_factor=1.1)
logger = logging.getLogger('')

def _check_extension(filename, allowed_extensions):
    if ('.' not in filename or
                filename.split('.').pop().lower() not in allowed_extensions):
        raise BadRequest(
            "{0} has an invalid name or extension".format(filename))


def _safe_filename(filename):
    filename = secure_filename(filename)
    date = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H%M%S")
    splitted_filename = filename.rsplit('.', 1)
    if len(splitted_filename) == 1:
         basename = "non_ascii_name_string"
         extension = splitted_filename[0]
    else:
        basename, extension = splitted_filename
    return "{0}-{1}.{2}".format(basename, date, extension)


def upload_file(file_stream, filename, content_type):
    _check_extension(filename, current_app.config['ALLOWED_EXTENSIONS'])
    filename = _safe_filename(filename)
    filename = '/' + bucket + '/' + filename

    gcs_file = gcs.open(filename, 'w',
     content_type=content_type,
     options={'x-goog-acl' : 'public-read'},
     retry_params=write_retry_params)
    gcs_file.write(file_stream)
    gcs_file.close()

    return filename

def list_recent_objects(number):
    objects = gcs.listbucket('/' + bucket)
    recent_objs = sorted(objects, key=lambda o: o.st_ctime, reverse=True)[0:number]
    logger.info('recent objects: %s' % recent_objs)
    return recent_objs


