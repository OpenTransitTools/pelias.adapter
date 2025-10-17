def assert_builtins(local_data, stage_data, skip: list[str] = []):
    if skip:
        for s in skip:
            if s in local_data:
                del local_data[s]
            if s in stage_data:
                del stage_data[s]

    for k, v in local_data.items():
        if k in stage_data and isinstance(v, str | int | float | bool):
            print(f"Comparing key '{k}': local={v}, stage={stage_data[k]}")
            assert (
                v == stage_data[k]
            ), f"Key {k} differs: local={v}, stage={stage_data[k]}"
