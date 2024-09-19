from . import settings, storage

settings = settings.Settings()
file_storage = storage.FileStorage(settings=settings.storage)
