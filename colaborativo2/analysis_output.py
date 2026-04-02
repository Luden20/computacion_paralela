import json
from pathlib import Path


def serialize_analysis(analysis, repeat: int | None = None) -> dict:
    payload = {
        "type": analysis.type.value,
        "time_seconds": analysis.time,
        "result": dict(sorted(analysis.result.items())),
    }
    if repeat is not None:
        payload["repeat"] = repeat
    return payload


def print_analysis(analysis) -> None:
    print(analysis, flush=True)


def write_combined_analysis(
    analyses: dict[str, dict] | dict[str, list[dict]],
    input_file: str,
    output_dir: str,
    file_suffix: str = "analysis_results",
) -> Path:
    payload = {
        "input_file": str(Path(input_file).resolve()) if input_file else None,
        "analyses": analyses,
    }

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    input_stem = Path(input_file).stem if input_file else "analysis"
    output_path = target_dir / f"{input_stem}_{file_suffix}.json"

    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(payload, output_file, indent=2, sort_keys=True)

    print(json.dumps(payload, indent=2, sort_keys=True), flush=True)
    print(f"JSON dump written to {output_path}", flush=True)
    return output_path
