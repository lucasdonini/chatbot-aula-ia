import re

from qdrant_client import QdrantClient

from ..settings import settings

url = settings.qdrant_url.get_secret_value()
forbid_http = not re.match(r"http://(localhost|0\.0\.0\.0\.|127\.0\.0\.1).*", url)
qdrant_client = QdrantClient(
    url=url,
    api_key=settings.qdrant_api_key.get_secret_value(),
    https=forbid_http,
)
