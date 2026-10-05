from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.pipeline import (
    run_photo_pipeline,
    run_video_pipeline,
    run_lidar_pipeline,
)


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Multimodal spatial reconstruction pipeline"
        )
    )

    parser.add_argument(
        "--tier",
        required=True,
        choices=[
            "photo",
            "video",
            "lidar"
        ]
    )

    parser.add_argument(
        "--input",
        required=True
    )

    parser.add_argument(
        "--output",
        default="outputs/result.json"
    )

    args = parser.parse_args()

    print(
        f"[INFO] Running {args.tier} pipeline..."
    )

    if args.tier == "photo":
        result = run_photo_pipeline(
            args.input
        )

    elif args.tier == "video":
        result = run_video_pipeline(
            args.input
        )

    else:
        result = run_lidar_pipeline(
            args.input
        )

    output = Path(args.output)

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output.write_text(
        json.dumps(
            {
                "capture_id": Path(
                    args.input
                ).name,
                "tier": args.tier,
                "result": result,
            },
            indent=2
        ),
        encoding="utf-8"
    )

    print(
        f"[SUCCESS] Output written to {output}"
    )


if __name__ == "__main__":
    main()