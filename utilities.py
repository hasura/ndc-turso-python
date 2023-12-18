from typing import Dict, List, Optional
from pydantic import BaseModel
import libsql_client  # Assuming this is your database client module
from models import ForeignKeyDetail


# Define necessary types and classes
class Type(BaseModel):
    type: str
    name: str = None
    underlying_type: 'Type' = None


class ObjectField(BaseModel):
    description: Optional[str] = None
    type: Type


class TableIntrospectResult(BaseModel):
    object_types: Dict[str, ObjectField]
    field_names: List[str]
    primary_keys: List[str]
    unique_keys: List[str]
    nullable_keys: List[str]
    field_types: Dict[str, str]
    foreign_keys: Dict[str, ForeignKeyDetail]


# Function to determine the Type based on SQLite data type
def determine_type(data_type: str) -> Type:
    data_type = data_type.upper()
    if data_type == "DATETIME":
        return Type(type="named", name="String")
    elif data_type == "INTEGER":
        return Type(type="named", name="Int")
    elif data_type == "REAL":
        return Type(type="named", name="Float")
    elif data_type in ["TEXT", "NVARCHAR"]:
        return Type(type="named", name="String")
    elif data_type == "BLOB":
        raise ValueError("BLOB NOT SUPPORTED!")
    else:
        return Type(type="named", name="String")


def wrap_nullable(_type: Type, is_not_null: bool, is_primary_key: bool) -> Type:
    if is_primary_key:
        return _type
    return _type if is_not_null else Type(type="nullable", underlying_type=_type)


async def introspect_table(table_name: str, client: libsql_client.Client) -> TableIntrospectResult:
    response = TableIntrospectResult(
        object_types={}, field_names=[], primary_keys=[],
        unique_keys=[], nullable_keys=[], field_types={}, foreign_keys={}
    )

    # Execute SQL query to get column details
    columns_result = await client.execute(f"PRAGMA table_info({table_name})")
    for column in columns_result.rows:
        if not isinstance(column['name'], str):
            raise ValueError("Column name must be string")

        determined_type = determine_type(column['type'])
        final_type = wrap_nullable(determined_type, column['notnull'] == 1, column['pk'] == 1)

        response.field_names.append(column['name'])
        if column['pk'] > 0:
            response.primary_keys.append(column['name'])
        if column['notnull'] == 0 and column['pk'] == 0:
            response.nullable_keys.append(column['name'])
        if determined_type.type == "named":
            response.field_types[column['name']] = determined_type.name
        response.object_types[column['name']] = ObjectField(description=None, type=final_type)

    # Introspect for foreign keys
    foreign_keys_result = await client.execute(f"PRAGMA foreign_key_list({table_name})")
    for fk in foreign_keys_result.rows:
        response.foreign_keys[fk['from']] = ForeignKeyDetail(
            table=fk['table'],
            column=fk['to']
        )

    # Introspect for unique keys
    index_list_result = await client.execute(f"PRAGMA index_list({table_name})")
    for index in index_list_result.rows:
        if index['unique']:
            index_info_result = await client.execute(f"PRAGMA index_info({index['name']})")
            for col in index_info_result.rows:
                if col['name'] not in response.unique_keys:
                    response.unique_keys.append(col['name'])

    return response
