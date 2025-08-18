from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

class StaticStorage(S3Boto3Storage):
    bucket_name = settings.AWS_STATIC_BUCKET
    location = "static"
    default_acl = "public-read"
    file_overwrite = True
    custom_domain = getattr(settings, "AWS_STATIC_CUSTOM_DOMAIN", None)
    def get_object_parameters(self, name):
        return {"CacheControl": "public, max-age=31536000, immutable"}

class MediaStorage(S3Boto3Storage):
    bucket_name = settings.AWS_MEDIA_BUCKET
    location = "media"
    default_acl = "public-read"
    file_overwrite = False
    custom_domain = getattr(settings, "AWS_MEDIA_CUSTOM_DOMAIN", None)
    def get_object_parameters(self, name):
        return {"CacheControl": "public, max-age=604800"}
