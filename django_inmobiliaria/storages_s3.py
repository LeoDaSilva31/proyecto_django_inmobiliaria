from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

class StaticRootS3Boto3Storage(S3Boto3Storage):
    bucket_name   = getattr(settings, "AWS_STATIC_BUCKET_NAME", None)
    location      = "static"
    file_overwrite = True
    custom_domain = getattr(settings, "AWS_STATIC_CUSTOM_DOMAIN", None)

    def get_object_parameters(self, name):
        return {"CacheControl": "public, max-age=31536000, immutable"}

class MediaRootS3Boto3Storage(S3Boto3Storage):
    bucket_name   = getattr(settings, "AWS_MEDIA_BUCKET_NAME", None)
    location      = "media"
    file_overwrite = False
    custom_domain = getattr(settings, "AWS_MEDIA_CUSTOM_DOMAIN", None)

    def get_object_parameters(self, name):
        return {"CacheControl": "public, max-age=604800"}
