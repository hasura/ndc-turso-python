from hasura_ndc import *
from models import Configuration
from typing import List
from constants import SCALAR_TYPES


async def get_schema(configuration: Configuration) -> SchemaResponse:
    if not configuration.config:
        raise ValueError('Configuration is missing')

    config = configuration.config
    object_fields = config.object_fields
    object_types = config.object_types
    collection_names = config.collection_names
    collection_infos: List[CollectionInfo] = []

    for cn in object_types.keys():
        if cn in collection_names:
            field_details = object_fields[cn]
            foreign_keys = {}
            for key, fk_info in field_details.foreign_keys.items():
                foreign_keys[key] = {
                    'column_mapping': {key: fk_info.column},
                    'foreign_collection': fk_info.table
                }
            collection_infos.append(CollectionInfo(
                name=cn,
                description=None,
                arguments={},
                type=cn,
                uniqueness_constraints={
                    f'{cn[0].upper()}{cn[1:]}ByID': {
                        'unique_columns': field_details.primary_keys
                    }
                },
                foreign_keys=foreign_keys
            ))

    procedures = [ProcedureInfo(
        arguments={},
        name="sync",
        description="Sync the Local Database file with the Remote Primary Database",
        result_type={
            'type': "named",
            'name': "Int"
        }
    )]

    functions = []

    schema_response = SchemaResponse(
        scalar_types=SCALAR_TYPES,
        functions=functions,
        procedures=procedures,
        object_types=config.object_types,
        collections=collection_infos
    )

    return schema_response
