import json


def validate_subtitle_json(content: bytes) -> None:
    """Raise ValueError if content is not valid word-level subtitle JSON."""
    try:
        data = json.loads(content.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Root must be a JSON object")

    words = data.get("words")
    if not isinstance(words, list) or len(words) == 0:
        raise ValueError("'words' must be a non-empty array")

    for i, w in enumerate(words):
        if not isinstance(w, dict):
            raise ValueError(f"words[{i}] must be an object")
        for field in ("word", "start", "end"):
            if field not in w:
                raise ValueError(f"words[{i}] missing field '{field}'")
        if not isinstance(w["word"], str):
            raise ValueError(f"words[{i}].word must be a string")
        if not isinstance(w["start"], (int, float)):
            raise ValueError(f"words[{i}].start must be a number")
        if not isinstance(w["end"], (int, float)):
            raise ValueError(f"words[{i}].end must be a number")
        if w["end"] <= w["start"]:
            raise ValueError(f"words[{i}].end must be after start")
