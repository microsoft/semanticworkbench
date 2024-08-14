from . import config, storage

settings = config.Settings()
file_storage = storage.FileStorage(settings=settings.storage)
