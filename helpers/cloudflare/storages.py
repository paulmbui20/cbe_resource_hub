# helpers/cloudflare/storages.py

from storages.backends.s3 import S3Storage
import helpers.storages.mixins as mixins


class CloudflareStorage(S3Storage):
    pass


class StaticFileStorage(mixins.DefaultACLMixin, CloudflareStorage):
    """
    For staticfiles (CSS, JS, TinyMCE) - PUBLIC bucket
    """
    location = "static"
    default_acl = "public-read"
    querystring_auth = False

    def get_object_parameters(self, name):
        params = super().get_object_parameters(name)
        params['CacheControl'] = 'public, max-age=31536000, immutable'
        return params


class MediaFileStorage(mixins.DefaultACLMixin, CloudflareStorage):
    """
    For user uploads - PRIVATE bucket with signed URLs
    """
    location = "media"
    default_acl = "private"
    querystring_auth = True

    def get_object_parameters(self, name):
        """Set moderate caching for media"""
        params = super().get_object_parameters(name)
        params['CacheControl'] = 'private, max-age=2592000'  # 30 days
        return params


class ProtectedMediaStorage(mixins.DefaultACLMixin, CloudflareStorage):
    """
    For sensitive user uploads - PRIVATE bucket with signed URLs
    """
    location = "protected"
    default_acl = "private"
    querystring_auth = True


class PublicFilesStorage(mixins.DefaultACLMixin, CloudflareStorage):
    """
    For files app uploads - PUBLIC bucket with media/files prefix
    No auth required, publicly accessible URLs
    """
    location = "media"  # Files will be stored at media/files/{category}/{filename}
    default_acl = "public-read"
    querystring_auth = False


class DbBackupPrivateStorage(mixins.DefaultACLMixin, CloudflareStorage):
    """
    This is a private protected bucket For storing db backup uploads
    """
    location = "database-backups"
    default_acl = "private"
    querystring_auth = True
