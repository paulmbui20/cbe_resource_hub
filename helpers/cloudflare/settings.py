# helpers/cloudflare/settings.py

import logging
import os

logger = logging.getLogger(__name__)

# ============ PRIVATE BUCKET (for media/user uploads) ============
private_bucket = os.getenv("CLOUDFLARE_R2_BUCKET")
private_endpoint = os.getenv("CLOUDFLARE_R2_BUCKET_ENDPOINT")
private_access_key = os.getenv("CLOUDFLARE_R2_ACCESS_KEY")
private_secret_key = os.getenv("CLOUDFLARE_R2_SECRET_KEY")

# ============ BACKUP PRIVATE BUCKET (for DB Backup uploads) ============
private_backup_bucket = os.getenv("BACKUP_R2_BUCKET_NAME")
private_backup_endpoint = os.getenv("BACKUP_R2_ENDPOINT")
private_backup_access_key = os.getenv("BACKUP_R2_ACCESS_KEY_ID")
private_backup_secret_key = os.getenv("BACKUP_R2_SECRET_ACCESS_KEY")
private_backup_region_name = os.getenv("BACKUP_R2_REGION", "auto")

# ============ PUBLIC BUCKET (for static files/TinyMCE) ============
public_bucket = os.getenv("CLOUDFLARE_R2_PUBLIC_BUCKET")
public_endpoint = os.getenv("CLOUDFLARE_R2_PUBLIC_BUCKET_ENDPOINT")
public_access_key = os.getenv("CLOUDFLARE_R2_PUBLIC_ACCESS_KEY")
public_secret_key = os.getenv("CLOUDFLARE_R2_PUBLIC_SECRET_KEY")
public_custom_domain = os.getenv("CLOUDFLARE_R2_PUBLIC_CUSTOM_DOMAIN")

# ============ PRIVATE BUCKET CONFIG ============
CLOUDFLARE_R2_CONFIG_OPTIONS = {}

if all([private_bucket, private_endpoint, private_access_key, private_secret_key]):
    CLOUDFLARE_R2_CONFIG_OPTIONS = {
        "bucket_name": private_bucket,
        "signature_version": "s3v4",
        "endpoint_url": private_endpoint,
        "access_key": private_access_key,
        "secret_key": private_secret_key,
        "default_acl": "private",
        "querystring_auth": True,
        "querystring_expire": 3600,
    }
    logger.info("✓ Private R2 bucket configured (media/user uploads)")
else:
    missing = []
    if not private_bucket:
        missing.append("CLOUDFLARE_R2_BUCKET")
    if not private_endpoint:
        missing.append("CLOUDFLARE_R2_BUCKET_ENDPOINT")
    if not private_access_key:
        missing.append("CLOUDFLARE_R2_ACCESS_KEY")
    if not private_secret_key:
        missing.append("CLOUDFLARE_R2_SECRET_KEY")
    logger.warning(f"Private R2 bucket not configured. Missing: {', '.join(missing)}")

# ============ PUBLIC BUCKET CONFIG ============
CLOUDFLARE_R2_PUBLIC_CONFIG_OPTIONS = {}

if all([public_bucket, public_endpoint, public_access_key, public_secret_key]):
    config = {
        "bucket_name": public_bucket,
        "signature_version": "s3v4",
        "endpoint_url": public_endpoint,
        "access_key": public_access_key,
        "secret_key": public_secret_key,
        "default_acl": "public-read",
        "querystring_auth": False,  # No signed URLs needed
    }

    # ← CRITICAL: Use custom_domain to override URL generation
    if public_custom_domain:
        config["custom_domain"] = public_custom_domain
        logger.info(f"✓ Public R2 bucket configured with custom domain: {public_custom_domain}")

    CLOUDFLARE_R2_PUBLIC_CONFIG_OPTIONS = config
else:
    missing = []
    if not public_bucket:
        missing.append("CLOUDFLARE_R2_PUBLIC_BUCKET")
    if not public_endpoint:
        missing.append("CLOUDFLARE_R2_PUBLIC_BUCKET_ENDPOINT")
    if not public_access_key:
        missing.append("CLOUDFLARE_R2_PUBLIC_ACCESS_KEY")
    if not public_secret_key:
        missing.append("CLOUDFLARE_R2_PUBLIC_SECRET_KEY")
    logger.warning(f"Public R2 bucket not configured. Missing: {', '.join(missing)}")

# ============ BACKUP BUCKET CONFIG ============

CLOUDFLARE_R2_BACKUP_CONFIG_OPTIONS = {}

if all([private_backup_bucket, private_backup_endpoint, private_backup_access_key, private_backup_secret_key,
        private_backup_region_name]):
    CLOUDFLARE_R2_BACKUP_CONFIG_OPTIONS = {
        "bucket_name": private_backup_bucket,
        "signature_version": "s3v4",
        "endpoint_url": private_backup_endpoint,
        "access_key": private_backup_access_key,
        "secret_key": private_backup_secret_key,
        "default_acl": "private",
        "file_overwrite": False,
        "location": "database-backups",
        "querystring_auth": True,
        "querystring_expire": 3600,
    }
    logger.info("✓ Private DB Backup R2 bucket configured (DB Backup uploads)")
else:
    missing = []
    if not private_backup_bucket:
        missing.append("BACKUP_R2_BUCKET_NAME")
    if not private_backup_endpoint:
        missing.append("BACKUP_R2_ENDPOINT")
    if not private_backup_access_key:
        missing.append("BACKUP_R2_ACCESS_KEY_ID")
    if not private_backup_secret_key:
        missing.append("BACKUP_R2_SECRET_ACCESS_KEY")
    if not private_backup_region_name:
        missing.append("BACKUP_R2_REGION")
    logger.warning(f"Private DB Backup R2 bucket not configured. Missing: {', '.join(missing)}")
