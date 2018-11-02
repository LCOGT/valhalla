from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    location = settings.MEDIAFILES_DIR


class StaticStorage(S3Boto3Storage):
    default_acl = 'public-read'
    location = settings.STATICFILES_DIR