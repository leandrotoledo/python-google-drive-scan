# -*- coding: utf-8 -*-
"""Google Drive Scan.

Example:

"""

import argparse
import asyncio

from typing import AsyncIterator

from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import ServiceAccountCreds

from drive_file import DriveFile

# Google Drive API
DRIVE_API_NAME = "drive"
DRIVE_API_VERSION = "v3"


async def _build():
    creds = ServiceAccountCreds(
        scopes=[
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/bigquery",
        ]
    )

    aiogoogle = Aiogoogle(service_account_creds=creds)
    await aiogoogle.service_account_manager.detect_default_creds_source()

    return aiogoogle


# Google Drive Service client
_client = asyncio.run(_build())


async def create_drive_file(id: str) -> DriveFile:
    async with _client:
        drive = await _client.discover(DRIVE_API_NAME, DRIVE_API_VERSION)
        file = await _client.as_service_account(drive.files.get(fileId=id))

        return DriveFile(**file)


async def get_files(
    drive_file: DriveFile, mime_types: list[str] = None
) -> list[DriveFile]:
    files = list()

    if mime_types:
        mime_types_filter = " or ".join(f"mimeType = '{i}'" for i in mime_types)
        query = f"({mime_types_filter}) and '{drive_file.id}' in parents"
    else:
        query = f"'{drive_file.id}' in parents"

    async with _client:
        drive = await _client.discover(DRIVE_API_NAME, DRIVE_API_VERSION)
        pages = await _client.as_service_account(
            drive.files.list(q=query), full_res=True
        )

        async for page in pages:
            for file in page["files"]:
                path = f"{drive_file.path} > {file['name']}"
                depth = drive_file.depth + 1
                new_drive_file = DriveFile(
                    **file, parent_id=drive_file.id, path=path, depth=depth
                )

                files.append(new_drive_file)

    return files


async def drive_scan(
    drive_file: DriveFile,
    max_depth: int = None,
    filter: list[str] = None,
    current_depth: int = 0,
) -> AsyncIterator[DriveFile]:
    """Recursive function to scan a Google Drive folder.

    Args:
      drive_file: DriveFile object .
      max_depth: Folder recursion max depth.
        e.g. when set to 3: Sub-folder 1 > Sub-folder 2 > Sub-folder 3.
      current_depth: Recursion current depth.
      files: Argument only used by recursive calls passing a list of files.

    Returns:
      A list of folders under the parent_folder_id.
      Each list item has a list of dictionaries with {folder_id: folder_name}.
    """
    current_depth = current_depth + 1
    if max_depth is None or current_depth <= max_depth:
        if drive_file.is_folder:
            for file in await get_files(drive_file, filter):
                async for child in drive_scan(file, max_depth, filter, current_depth):
                    yield child

    yield drive_file


async def main(args) -> None:
    folder = await create_drive_file(args.folder_id)
    files = drive_scan(folder, max_depth=args.max_depth)

    rows_to_insert = dict()
    rows_to_insert["rows"] = list()
    async for file in files:
        rows_to_insert["rows"].append({"json": file.as_dict})
        print(file.path, "||", file.name)

    # bq = await _client.discover("bigquery", "v2", validate=False)
    # res = await _client.as_service_account(
    #     bq.datasets.list(
    #         projectId="mystic-column-320016",
    #     )
    # )

    # res = await _client.as_service_account(
    #     bq.tabledata.insertAll(
    #         projectId="mystic-column-320016",
    #         datasetId="my_google_drive",
    #         tableId="scan",
    #         json=rows_to_insert,
    #     )
    # )

    # print(res)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-f",
        "--folder_id",
        required=True,
        help="The id of the Google Drive folder to scan.",
    )
    parser.add_argument(
        "-d",
        "--max_depth",
        type=int,
        help="Max depth to reach while scanning Google Drive folders.",
        default=3,
    )

    args = parser.parse_args()
    asyncio.run(main(args))
