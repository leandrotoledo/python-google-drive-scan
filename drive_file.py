class DriveFile:
    # Google Drive Folders MIME Type
    MIME_TYPE_FOLDER: str = "application/vnd.google-apps.folder"

    # Google Drive URLs
    DRIVE_URL_FOLDERS: str = "https://drive.google.com/drive/u/0/folders/"
    DRIVE_URL_FILE: str = "https://drive.google.com/file/d/"

    def __init__(
        self,
        id: str,
        name: str = None,
        path: str = None,
        mime_type: str = None,
        parent_id: str = None,
        depth: int = None,
        **kwargs,
    ) -> None:
        self.id = id
        self.name = name
        self.path = path or name
        self.mime_type = mime_type or kwargs.get("mimeType")
        self.parent_id = parent_id
        self.depth = depth or 0

    @property
    def is_folder(self):
        if self.mime_type == self.MIME_TYPE_FOLDER:
            return True
        return False

    @property
    def url(self):
        if self.is_folder:
            return f"{self.DRIVE_URL_FOLDERS}{self.id}"
        return f"{self.DRIVE_URL_FILE}{self.id}"

    @property
    def as_dict(self):
        drive_file = self.__dict__

        drive_file["is_folder"] = self.is_folder
        drive_file["url"] = self.url

        return drive_file

    def __str__(self) -> str:
        return f"{self.path} ({self.url})"
