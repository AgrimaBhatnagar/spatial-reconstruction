from __future__ import annotations

from pathlib import Path

import cv2

from .geometry import estimate_room_geometry


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".JPG",
    ".JPEG",
    ".PNG",
}


def discover_images(input_dir):
    root = Path(input_dir)

    if not root.exists():
        raise FileNotFoundError(
            f"Input directory does not exist: {input_dir}"
        )

    return sorted(
        str(path)
        for path in root.rglob("*")
        if path.suffix in IMAGE_EXTENSIONS
    )


def extract_video_frames(
    video_path,
    output_dir,
    every_n_frames=10
):
    output_dir = Path(output_dir)
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    capture = cv2.VideoCapture(
        str(video_path)
    )

    if not capture.isOpened():
        raise RuntimeError(
            f"Unable to open video: {video_path}"
        )

    frame_id = 0
    saved_frames = []

    while True:
        success, frame = capture.read()

        if not success:
            break

        if frame_id % every_n_frames == 0:

            output_path = (
                output_dir /
                f"frame_{frame_id:06d}.jpg"
            )

            cv2.imwrite(
                str(output_path),
                frame
            )

            saved_frames.append(
                str(output_path)
            )

        frame_id += 1

    capture.release()

    return saved_frames


def run_photo_pipeline(input_dir):

    images = discover_images(input_dir)

    if not images:
        raise RuntimeError(
            f"No images found in {input_dir}"
        )

    observations = estimate_room_geometry(
        images
    )

    return {
        "input_count": len(images),
        "observations": [
            observation.__dict__
            for observation in observations
        ]
    }


def run_video_pipeline(video_path):

    frames = extract_video_frames(
        video_path,
        "outputs/video_frames"
    )

    observations = estimate_room_geometry(
        frames
    )

    return {
        "frame_count": len(frames),
        "observations": [
            observation.__dict__
            for observation in observations
        ]
    }


def run_lidar_pipeline(input_dir):

    path = Path(input_dir)

    if not path.exists():
        raise FileNotFoundError(
            f"LiDAR input does not exist: {input_dir}"
        )

    files = [
        str(p)
        for p in path.rglob("*")
        if p.is_file()
    ]

    return {
        "input_files": files,
        "status": "loader_ready_for_dataset_adapter"
    }