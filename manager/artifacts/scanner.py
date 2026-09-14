from __future__ import annotations

import hashlib
import re
from pathlib import Path


class ArtifactScanError(RuntimeError):
    pass


class EAArtifactScanner:
    VERSION_PATTERN = re.compile(r"^\d+(?:\.\d+)*$")

    @staticmethod
    def sha256(path: Path) -> str:
        digest = hashlib.sha256()

        with path.open("rb") as file:
            for chunk in iter(
                lambda: file.read(1024 * 1024),
                b"",
            ):
                digest.update(chunk)

        return digest.hexdigest()

    @staticmethod
    def validate_version(version: str) -> str:
        version = version.strip()

        if not version:
            raise ArtifactScanError("Artifact version cannot be empty.")

        if not EAArtifactScanner.VERSION_PATTERN.match(version):
            raise ArtifactScanError(
                "Invalid version format. " "Use values such as 1.31 or 2.0.0."
            )

        return version

    def inspect(
        self,
        ea_id: str,
        version: str,
        path: str,
    ) -> dict:
        version = self.validate_version(version)

        artifact_path = Path(path).expanduser().resolve()

        if not artifact_path.is_file():
            raise ArtifactScanError(f"Artifact does not exist: {artifact_path}")

        if artifact_path.suffix.lower() != ".ex5":
            raise ArtifactScanError("Artifact must be an .ex5 file.")

        return {
            "ea_id": ea_id,
            "version": version,
            "filename": artifact_path.name,
            "path": str(artifact_path),
            "sha256": self.sha256(artifact_path),
            "file_size": artifact_path.stat().st_size,
        }
