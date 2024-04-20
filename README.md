## Work in progress

This is an implementation of a Turso connector in Python, which upon completion can serve as a
reference connector implementing the Python SDK.

The Python SDK is under development.

python3 main.py serve --configuration config.json --port 8084

python3 main.py configuration serve --port 9101

See the .env file

TODO: GroupBy and GroupByHaving

    if q.group_by:  # Assuming q.group_by is a list of field names (strings) for simplicity
        group_by_fields = [escape_double(field) for field in q.group_by]
        group_by_sql = f'GROUP BY {", ".join(group_by_fields)}'

TODO: Collapse/Collect rows into the wrapping types

TODO: Aggregates Generation

TODO: Replace Query with functions so I can hand-roll it and play with different defaults to see what feels the most
sensible.

TODO: Fix the configuration generation and package this so that it can serve as an example that follows the packaging
spec