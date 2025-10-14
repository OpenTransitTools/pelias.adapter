def verify_response(stage_obj: dict, local_obj: dict, top_level: list[str]):
    assert isinstance(stage_obj, dict), f"Expected stage_obj to be dict, got {type(stage_obj)}"
    assert isinstance(local_obj, dict), f"Expected local_obj to be dict, got {type(local_obj)}"

    for key in top_level:
        if key not in ["__type__", "vtype", "timestamp"]:  # Skip __type__ key comparison
            assert key in stage_obj, f"Key '{key}' missing in stage_obj."
            assert key in local_obj, f"Key '{key}' missing in local_obj."

            assert type(stage_obj[key]) == type(local_obj[key]), (
                f"Type mismatch for key '{key}': {type(stage_obj[key])} vs {type(local_obj[key])}"
            )

            if isinstance(stage_obj[key], list):
                assert len(stage_obj[key]) == len(local_obj[key]), (
                    f"Length mismatch for list key '{key}': {len(stage_obj[key])} vs {len(local_obj[key])}"
                )

                for i, (stage_item, local_item) in enumerate(zip(stage_obj[key], local_obj[key])):
                    if isinstance(stage_item, dict) and isinstance(local_item, dict):
                        verify_response(stage_item, local_item, top_level=list(stage_item.keys()))
                    else:
                        assert stage_item == local_item, (
                            f"Mismatch in list '{key}' at index {i}: {stage_item} vs {local_item}"
                        )

            elif isinstance(stage_obj[key], dict):
                if key not in ["__type__", "vtype", "timestamp"]:  # Skip __type__ key comparison
                    verify_response(stage_obj[key], local_obj[key], top_level=stage_obj[key].keys())

            else:
                assert stage_obj[key] == local_obj[key], (
                    f"Value mismatch for key '{key}': {stage_obj[key]} vs {local_obj[key]}"
                )


def assert_builtins(local_data, stage_data, skip:list[str] = []):
    if skip:
        for s in skip:
            if s in local_data:
                del local_data[s]
            if s in stage_data:
                del stage_data[s]

    for k, v in local_data.items():
        if k in stage_data and isinstance(v, str | int | float | bool):
            print (f"Comparing key '{k}': local={v}, stage={stage_data[k]}")
            assert v == stage_data[k], f"Key {k} differs: local={v}, stage={stage_data[k]}"
