"""
find issues in images
"""

import os
import inspect
from typing import Iterable, List, Optional
from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import redirect_stderr, redirect_stdout

import numpy as np
import cleanvision

from renumics.spotlight.dtypes import Image

from renumics.spotlight.dtypes.conversion import ConversionError, NoConverterAvailable

from renumics.spotlight.data_store import DataStore

from ..decorator import data_analyzer
from ..typing import DataIssue


_issue_types = {
    "is_light_issue": (
        "Bright images",
        "medium",
        """
        Some images in your dataset are unusually bright.
    """,
    ),
    "is_dark_issue": (
        "Dark images",
        "medium",
        """
        Some images in your dataset are unusually dark.
    """,
    ),
    "is_blurry_issue": (
        "Blurry images",
        "medium",
        """
        Some images in your dataset are blurry.
    """,
    ),
    "is_exact_duplicates_issue": (
        "Exact duplicates",
        "high",
        """
        Some images in your dataset are exact duplicates.
    """,
    ),
    "is_near_duplicates_issue": (
        "Near duplicates",
        "medium",
        """
        Some images in your dataset are near duplicates.
    """,
    ),
    "is_odd_aspect_ratio_issue": (
        "Odd aspect ratio",
        "medium",
        """
        Some images in your dataset have an odd aspect ratio.
    """,
    ),
    "is_low_information_issue": (
        "Low information",
        "medium",
        """
        Some images in your dataset have low information content.
    """,
    ),
    "is_grayscale_issue": (
        "Grayscale images",
        "medium",
        """
        Some images in your dataset are grayscale.
    """,
    ),
}


def _make_issue(cleanvision_key: str, column: str, rows: List[int]) -> DataIssue:
    title, severity, description = _issue_types[cleanvision_key]
    return DataIssue(
        severity=severity,
        title=title,
        rows=rows,
        columns=[column],
        description=inspect.cleandoc(description),
    )


def _get_cell_data_safe(
    data_store: DataStore, column_name: str, row: int
) -> Optional[bytes]:
    try:
        return data_store.get_converted_value(column_name, row, simple=False)  # type: ignore
    except (ConversionError, NoConverterAvailable):
        return None


@data_analyzer
def analyze_with_cleanvision(
    data_store: DataStore, columns: List[str]
) -> Iterable[DataIssue]:
    """
    find image issues using cleanvision
    """

    image_columns = [col for col in columns if data_store.dtypes.get(col) == Image]

    for column_name in image_columns:
        # load image data from data source
        images = (
            _get_cell_data_safe(data_store, column_name, row)
            for row in range(len(data_store))
        )

        # Write images to temporary directory for cleanvision.
        # They alsow support huggingface's image format.
        # Maybe use that in the future where applicable.
        indices_list = []
        image_paths = []
        with TemporaryDirectory() as tmp:
            for i, image_data in enumerate(images):
                if not image_data:
                    continue
                path = Path(tmp) / f"{i}.png"
                path.write_bytes(image_data)
                image_paths.append(str(path))
                indices_list.append(i)

            if len(image_paths) == 0:
                continue

            with open(os.devnull, "w", encoding="utf-8") as devnull:
                with redirect_stdout(devnull), redirect_stderr(devnull):
                    lab = cleanvision.Imagelab(filepaths=image_paths)
                    lab.find_issues()
            analysis = lab.issues

        indices = np.array(indices_list)

        # Iterate over all the different issue types
        # and convert them to our internal DataIssue format.
        for cleanvision_key in _issue_types:
            rows = indices[analysis[cleanvision_key]].tolist()
            if rows:
                yield _make_issue(cleanvision_key, column_name, rows)
