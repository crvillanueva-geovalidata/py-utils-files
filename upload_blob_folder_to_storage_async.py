import asyncio
import os
from mimetypes import guess_type
from pathlib import Path

from azure.storage.blob import (
    ContentSettings,
)
import colorama
from colorama import Fore

colorama.init(autoreset=True)


async def upload_file_to_blob(
    connection_string: str,
    filename: str,
    filename_az: str,
    container_name: str = "$web",
    overwrite: bool = True,
):
    from azure.storage.blob.aio import BlobServiceClient

    service_client = BlobServiceClient.from_connection_string(connection_string)
    async with service_client:
        container_client = service_client.get_container_client(container_name)

        content_type = guess_type(filename)[0]
        settings = ContentSettings(content_type=content_type)

        with open(filename, "rb") as data:
            print(Fore.YELLOW + f"Uploading '{filename}' ({content_type}).")

            blob_client = container_client.get_blob_client(blob=str(filename_az))
            await blob_client.upload_blob(
                data=data,
                overwrite=overwrite,
                content_settings=settings,
            )

            print(Fore.GREEN + f"'{filename}' uploaded successfully to blob container.")


async def upload_folder_to_blob_container(
    connection_string: str,
    folder_path: str = "build",
    container_name: str = "$web",
    overwrite: bool = True,
):
    futures = []
    for dirpath, _, filenames in os.walk(folder_path):
        if filenames:
            for file in filenames:
                file_path_on_local = Path(dirpath) / file
                # Omit the folder name in the upload file structure
                file_path_on_azure = file_path_on_local.relative_to(folder_path)
                futures.append(
                    upload_file_to_blob(
                        connection_string,
                        str(file_path_on_local),
                        str(file_path_on_azure),
                        container_name,
                        overwrite,
                    )
                )
    await asyncio.gather(*futures)


async def main():
    FILENAME_STR_CONNECTION = "blob-storage-conn-str"
    import sys

    args = sys.argv
    if len(args) > 1:
        print("Credentials given")
        print(args[1])
        connection_string_blob = args[1]
    else:
        print(f"Searching for credentials in {FILENAME_STR_CONNECTION}")
        with open(FILENAME_STR_CONNECTION, "r") as f:
            connection_string_blob = f.read().strip()
    await upload_folder_to_blob_container(connection_string_blob)


if __name__ == "__main__":
    import asyncio
    import time

    start_time = time.perf_counter()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    end_time = time.perf_counter()
    print(f"Blobs uploaded in {end_time - start_time:.2f} seconds")
