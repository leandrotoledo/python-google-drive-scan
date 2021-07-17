"""Google Drive Scan."""

import argparse

from googleapiclient.discovery import build

from drive_file import DriveFile

# Google Drive API
DRIVE_API_NAME = "drive"
DRIVE_API_VERSION = "v3"

# Google Drive Service client
_client = build(DRIVE_API_NAME, DRIVE_API_VERSION)


def create_drive_file(id: str) -> DriveFile:
    file = _client.files().get(fileId=id).execute()

    return DriveFile(**file)


def get_files(drive_file: DriveFile, mime_types: list[str] = None) -> list[DriveFile]:
    files = list()

    page_token = None
    while True:
        if mime_types:
            mime_types_filter = " or ".join(f"mimeType = '{i}'" for i in mime_types)
            query = f"({mime_types_filter}) and '{drive_file.id}' in parents"
        else:
            query = f"'{drive_file.id}' in parents"

        request = (
            _client.files()
            .list(
                q=query,
                spaces="drive",
                fields="nextPageToken, files(id, name)",
                pageSize=1000,
                pageToken=page_token,
            )
            .execute()
        )

        for file in request.get("files", []):
            new_drive_file = create_drive_file(file["id"])

            new_drive_file.parent_id = drive_file.id
            new_drive_file.path = f"{drive_file.path} > {file['name']}"
            new_drive_file.depth = drive_file.depth + 1

            files.append(new_drive_file)

        page_token = request.get("nextPageToken", None)
        print(page_token)
        if page_token is None:
            break

    return files


def drive_scan(
    drive_file: DriveFile,
    max_depth: int = None,
    filter: list[str] = None,
    current_depth: int = 0,
):
    current_depth = current_depth + 1
    if max_depth is None or current_depth <= max_depth:
        if drive_file.is_folder:
            for file in get_files(drive_file, filter):
                for child in drive_scan(file, max_depth, filter, current_depth):
                    yield child

    yield drive_file


def main(args):
    folder = create_drive_file(args.folder_id)
    files = drive_scan(folder, max_depth=args.max_depth)

    for file in files:
        print(file.__dict__)


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
    main(args)
