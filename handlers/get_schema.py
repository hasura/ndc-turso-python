from hasura_ndc import *
from models import Configuration
from typing import List
from constants import SCALAR_TYPES


def is_numeric_type(type_name: str) -> bool:
    """
    Determines if the provided type name is a numeric type.

    Args:
    type_name (str): The name of the type to check.

    Returns:
    bool: True if the type is numeric, False otherwise.
    """
    numeric_types = ['Int', 'Float', 'Decimal']  # Add more types as per your schema
    return type_name in numeric_types


def get_field_operators(field_type):
    if field_type == 'Int' or field_type == 'Float':
        return {
            "_eq": field_type,
            "_neq": field_type,
            "_gt": field_type,
            "_lt": field_type,
            "_gte": field_type,
            "_lte": field_type,
            "_is_null": "Boolean"
        }
    elif field_type == 'String':
        return {
            "_eq": field_type,
            "_neq": field_type,
            "_like": field_type,
            "_is_null": "Boolean"
        }


def get_nested_where(cn, new_object_fields, nested=1):
    if nested == 0:
        return ObjectType(
            description=f"Where for {cn}",
            fields={
                **new_object_fields
            }
        )
    return ObjectType(
        description=f"Where for {cn}",
        fields={
            **new_object_fields,
            "_not": ObjectField(
                type=Type(
                    type="nullable",
                    underlying_type=Type(
                        type="named",
                        name=f"list_{cn}_bool_exp{'_nested' * nested}"
                    )
                )
            ),
            "_or": ObjectField(
                type=Type(
                    type="nullable",
                    underlying_type=Type(
                        type="array",
                        element_type=Type(
                            type="named",
                            name=f"list_{cn}_bool_exp{'_nested' * nested}"
                        )
                    )
                )
            ),
            "_and": ObjectField(
                type=Type(
                    type="nullable",
                    underlying_type=Type(
                        type="array",
                        element_type=Type(
                            type="named",
                            name=f"list_{cn}_bool_exp{'_nested' * nested}"
                        )
                    )
                )
            ),
        }
    )


async def get_schema(configuration: Configuration) -> SchemaResponse:
    if not configuration.config:
        raise ValueError('Configuration is missing')

    config = configuration.config
    object_fields = config.object_fields
    object_types = config.object_types
    collection_names = config.collection_names
    collection_infos: List[CollectionInfo] = []
    new_object_types = {}
    procedures = [ProcedureInfo(
        arguments={},
        name="sync",
        description="Sync the Local Database file with the Remote Primary Database",
        result_type={
            'type': "named",
            'name': "Int"
        }
    )]

    # Functions do not mutate things
    functions = []

    # Procedures mutate things and are Mutations

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

            new_object_fields = {}
            for field_name in field_details.field_names:
                field_type = field_details.field_types[field_name]
                operators = get_field_operators(field_type)  # Function returning appropriate operators

                field_input_type_name = f"{field_type}_comparison_exp"

                if new_object_types.get(field_input_type_name) is None:
                    # Define the ObjectType for field input
                    field_input_type = ObjectType(
                        description=f"Input type for filtering on field '{field_name}'",
                        fields={op: ObjectField(
                            type=Type(type="nullable",
                                      underlying_type=Type(
                                          type="named",
                                          name=operator_type)
                                      )
                        ) for op, operator_type in operators.items()}
                    )
                    # Add the ObjectType to new_object_types with its unique name
                    new_object_types[field_input_type_name] = field_input_type
                # Use the unique name in the 'name' field of the Type object
                new_object_fields[field_name] = {
                    "type": Type(
                        type="nullable",
                        underlying_type=Type(
                            type="named",
                            name=field_input_type_name
                        )
                    )
                }

            # HAHA! Problem Solved. Don't need recursive types, GroupBy here we come.
            # If we generate 3 levels deep, we can satisfy any possible filter. We don't NEED recursion.
            # The LSP does not currently correctly support recursive types
            # Due to this, recursive types will not work in the WHERE clause
            # HOWEVER
            # As per Boolean Algebra, every boolean expression can be converted into either conjunctive normal form
            # or disjunctive normal form.
            # Therefore :: It is always possible to express ANY boolean expression with just 3 levels of nesting
            # Con: No easy infinite recursion
            # Pro: Forces things to be written in CNF/DNF
            new_object_types[f"list_{cn}_bool_exp_nested_nested_nested"] = get_nested_where(cn, new_object_fields, 0)
            new_object_types[f"list_{cn}_bool_exp_nested_nested"] = get_nested_where(cn, new_object_fields, 3)
            new_object_types[f"list_{cn}_bool_exp_nested"] = get_nested_where(cn, new_object_fields, 2)
            new_object_types[f"list_{cn}_bool_exp"] = get_nested_where(cn, new_object_fields, 1)

            # functions.append(
            #     FunctionInfo(
            procedures.append(
                ProcedureInfo(
                    arguments={
                        "limit": {
                            "type": {
                                "type": "nullable",
                                "underlying_type": {
                                    "type": "named",
                                    "name": "Int"
                                }
                            }
                        },
                        "offset": {
                            "type": {
                                "type": "nullable",
                                "underlying_type": {
                                    "type": "named",
                                    "name": "Int"
                                }
                            }
                        },
                        "where": {
                            "type": {
                                "type": "nullable",
                                "underlying_type": {
                                    "type": "named",
                                    "name": f"list_{cn}_bool_exp"
                                }
                            }
                        }
                    },
                    name=f"list_{cn}",
                    description="List the collection",
                    result_type=Type(
                        type="nullable",
                        underlying_type=Type(
                            type="array",
                            element_type=Type(
                                type="named",
                                name=cn
                            )
                        )
                    )
                )
            )

            new_object_fields = {}
            for field_name in field_details.field_names:
                if field_name in field_details.nullable_keys:
                    new_object_fields[field_name] = {
                        "type": Type(
                            type="nullable",
                            underlying_type=Type(
                                type="named",
                                name=field_details.field_types[field_name]
                            )
                        )
                    }
                else:
                    new_object_fields[field_name] = {
                        "type": Type(
                            type="named",
                            name=field_details.field_types[field_name]
                        )
                    }
            new_object_types[f"{cn}_InsertType"] = ObjectType(
                description=f"Insert type for {cn}",
                fields=new_object_fields
            )
            insert_one_procedure = ProcedureInfo(
                name=f"insert_{cn}_one",
                description=f"Insert a single record into the {cn} collection.",
                arguments={
                    "object": {
                        "description": f"The record to insert into the {cn}",
                        "type": {
                            "type": "named",
                            "name": f"{cn}_InsertType"
                        }
                    },
                    "return": {
                        "type": {
                            "type": "nullable",
                            "underlying_type": {
                                "type": "named",
                                "name": "Int"
                            }
                        }
                    }
                },
                result_type={
                    'type': "named",
                    'name': "Int"
                }
            )
            procedures.append(insert_one_procedure)
            insert_many_procedure = ProcedureInfo(
                name=f"insert_{cn}_many",
                description=f"Insert multiple records into the {cn} collection.",
                arguments={
                    "objects": {
                        "description": f"The records to insert into the {cn}",
                        "type": {
                            "type": "array",
                            "element_type": {
                                "type": "named",
                                "name": f"{cn}_InsertType"
                            }
                        }
                    },
                    "return": {
                        "type": {
                            "type": "nullable",
                            "underlying_type": {
                                "type": "named",
                                "name": "Int"
                            }
                        }
                    }
                },
                result_type={
                    'type': "named",
                    'name': "Int"  # Or any other appropriate return type
                }
            )
            procedures.append(insert_many_procedure)

            if len(field_details.primary_keys) > 0:
                # Define named object types for pk_columns, _set, and _inc
                pk_columns_type = ObjectType(
                    description=f"Primary key columns for {cn}",
                    fields={pk: ObjectField(
                        type=Type(type="named", name=field_details.field_types[pk])
                    ) for pk in field_details.primary_keys}
                )
                set_type = ObjectType(
                    description=f"Fields to set for {cn}",
                    fields={field_name: ObjectField(
                        type=Type(
                            type="nullable",
                            underlying_type=Type(type="named", name=field_details.field_types[field_name])
                        )
                    ) for field_name in field_details.field_names}
                )
                inc_type = ObjectType(
                    description=f"Numeric fields to increment for {cn}",
                    fields={field_name: ObjectField(
                        type=Type(
                            type="nullable",
                            underlying_type=Type(type="named", name=field_details.field_types[field_name])
                        )
                    ) for field_name in field_details.field_names if
                        is_numeric_type(field_details.field_types[field_name])}
                )

                # Add these new object types to new_object_types
                new_object_types[f"{cn}_PKColumnsType"] = pk_columns_type
                new_object_types[f"{cn}_SetType"] = set_type
                new_object_types[f"{cn}_IncType"] = inc_type

                # Define the update_by_pk procedure using named types
                update_by_pk_procedure = ProcedureInfo(
                    name=f"update_{cn}_by_pk",
                    description=f"Update a single record in the {cn} collection by primary key.",
                    arguments={
                        "pk_columns": {
                            "description": f"The primary key columns of the record to update in the {cn}",
                            "type": {"type": "named", "name": f"{cn}_PKColumnsType"}
                        },
                        "_set": {
                            "description": f"The fields to set for the {cn}",
                            "type": {"type": "nullable", "underlying_type": {"type": "named", "name": f"{cn}_SetType"}}
                        },
                        "_inc": {
                            "description": f"The numeric fields to increment for the {cn}",
                            "type": {"type": "nullable", "underlying_type": {"type": "named", "name": f"{cn}_IncType"}}
                        },
                        "return": {
                            "type": {
                                "type": "nullable",
                                "underlying_type": {
                                    "type": "named",
                                    "name": "Int"
                                }
                            }
                        }
                    },
                    result_type={
                        'type': "named",
                        'name': "Int"
                    }
                )
                procedures.append(update_by_pk_procedure)

                # Assuming 'cn' is your collection name in the loop
                delete_by_pk_procedure = ProcedureInfo(
                    name=f"delete_{cn}_by_pk",
                    description=f"Delete a single record from the {cn} collection by primary key.",
                    arguments={
                        "pk_columns": {
                            "description": f"The primary key columns of the record to delete in the {cn}",
                            "type": {"type": "named", "name": f"{cn}_PKColumnsType"}
                        }
                    },
                    result_type={
                        'type': "named",
                        'name': "Int"  # Assuming the return type is an integer indicating the number of records deleted
                    }
                )
                procedures.append(delete_by_pk_procedure)

    schema_response = SchemaResponse(
        scalar_types=SCALAR_TYPES,
        functions=functions,
        procedures=procedures,
        object_types={**config.object_types, **new_object_types},
        collections=collection_infos
    )

    return schema_response
