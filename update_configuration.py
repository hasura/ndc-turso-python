import libsql_client
from models import Configuration, ObjectFieldDetails
from constants import BASE_TYPES, BASE_FIELDS
from utilities import introspect_table
from typing import Dict
import json
import asyncio


async def update_configuration(raw_configuration: Configuration) -> Configuration:
    credentials = raw_configuration.credentials.model_dump()
    client = libsql_client.create_client(**credentials)
    tables_result = await client.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND "
        "name <> 'sqlite_sequence' AND name <> 'sqlite_stat1' AND "
        "name <> 'libsql_wasm_func_table'"
    )
    table_names = [row['name'] for row in tables_result.rows]

    if not raw_configuration.config:
        raw_configuration.config = {
            'collection_names': table_names,
            'object_types': {**BASE_TYPES},
            'object_fields': {}
        }

        object_fields: Dict[str, ObjectFieldDetails] = {}

        for table_name in table_names:
            field_dict = await introspect_table(table_name, client)
            raw_configuration.config['object_types'][table_name] = {
                'description': None,
                'fields': {**field_dict.object_types, **BASE_FIELDS},
            }
            object_fields[table_name] = ObjectFieldDetails(**{
                'field_names': field_dict.field_names,
                'field_types': field_dict.field_types,
                'primary_keys': field_dict.primary_keys,
                'unique_keys': field_dict.unique_keys,
                'nullable_keys': field_dict.nullable_keys,
                'foreign_keys': field_dict.foreign_keys,
            })

        raw_configuration.config["object_fields"] = object_fields

    await client.close()
    return raw_configuration


if __name__ == "__main__":
    with open("config.json", "r") as f:
        configuration = json.load(f)

    configuration = Configuration(**configuration)
    configuration = asyncio.run(update_configuration(configuration))

    with open("config.json", "w") as f:
        json.dump(configuration.model_dump(), f)
