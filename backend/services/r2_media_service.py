"""Private Cloudflare R2 storage adapter for WhatsApp media."""
from dataclasses import dataclass
import os
from urllib.parse import urlparse

import boto3
from botocore.config import Config


REQUIRED_R2_ENV = (
    'R2_ACCESS_KEY_ID',
    'R2_SECRET_ACCESS_KEY',
    'R2_ENDPOINT',
    'R2_BUCKET_NAME',
)


class R2MediaError(RuntimeError):
    pass


class R2MediaConfigurationError(R2MediaError):
    pass


@dataclass(frozen=True)
class R2StoredObject:
    etag: str


@dataclass(frozen=True)
class R2RetrievedObject:
    data: bytes
    content_type: str


def missing_r2_configuration(environ=None):
    source = environ if environ is not None else os.environ
    return [name for name in REQUIRED_R2_ENV if not source.get(name)]


class R2MediaService:
    def __init__(self, *, client=None, environ=None, production=False):
        source = environ if environ is not None else os.environ
        runtime = str(source.get('APP_RUNTIME', 'production')).strip().lower()
        if not production and runtime != 'demo':
            raise R2MediaConfigurationError('Private demo media storage is unavailable.')
        if production and runtime != 'production':
            raise R2MediaConfigurationError('Private production media storage is unavailable.')

        missing = missing_r2_configuration(source)
        if missing:
            raise R2MediaConfigurationError(
                'Private media storage is not fully configured.'
            )

        values = {name: source[name] for name in REQUIRED_R2_ENV}
        if any(value != value.strip() for value in values.values()):
            raise R2MediaConfigurationError('Private media storage configuration is invalid.')

        endpoint = values['R2_ENDPOINT']
        parsed_endpoint = urlparse(endpoint)
        if (
            parsed_endpoint.scheme != 'https'
            or not parsed_endpoint.hostname
            or not parsed_endpoint.hostname.endswith('.r2.cloudflarestorage.com')
            or parsed_endpoint.username
            or parsed_endpoint.password
            or parsed_endpoint.query
            or parsed_endpoint.fragment
            or parsed_endpoint.path not in {'', '/'}
        ):
            raise R2MediaConfigurationError('Private media storage endpoint is invalid.')

        self.bucket_name = values['R2_BUCKET_NAME']
        if ('demo' in self.bucket_name.lower()) == production:
            raise R2MediaConfigurationError('The media bucket does not match this runtime.')

        self.client = client or boto3.client(
            's3',
            endpoint_url=endpoint.rstrip('/'),
            aws_access_key_id=values['R2_ACCESS_KEY_ID'],
            aws_secret_access_key=values['R2_SECRET_ACCESS_KEY'],
            region_name='auto',
            config=Config(
                connect_timeout=5,
                read_timeout=15,
                retries={'max_attempts': 2, 'mode': 'standard'},
                signature_version='s3v4',
            ),
        )

    def put_image(self, object_key, image):
        try:
            response = self.client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=image.data,
                ContentLength=image.byte_size,
                ContentType=image.content_type,
                CacheControl='private, no-store',
                Metadata={'sha256': image.sha256_hex},
            )
        except Exception as exc:
            raise R2MediaError('Private media storage is temporarily unavailable.') from exc
        return R2StoredObject(etag=str(response.get('ETag', '')).strip('"')[:200])

    def get_image(self, object_key, *, max_bytes):
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=object_key,
            )
            body = response['Body']
            try:
                data = body.read(max_bytes + 1)
            finally:
                close = getattr(body, 'close', None)
                if callable(close):
                    close()
        except Exception as exc:
            raise R2MediaError('The stored image could not be retrieved.') from exc

        if len(data) > max_bytes:
            raise R2MediaError('The stored image failed its size validation.')
        return R2RetrievedObject(
            data=data,
            content_type=str(response.get('ContentType', ''))[:100],
        )

    def delete_image(self, object_key):
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=object_key)
        except Exception as exc:
            raise R2MediaError('Stored image cleanup failed.') from exc
