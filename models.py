from hasura_ndc import *
from pydantic import BaseModel
from libsql_client import Client
from typing import Optional, List, Dict


class ForeignKeyDetail(BaseModel):
    table: str
    column: str


class ObjectFieldDetails(BaseModel):
    field_names: List[str]
    field_types: Dict[str, str]
    primary_keys: List[str]
    unique_keys: List[str]
    nullable_keys: List[str]
    foreign_keys: Dict[str, ForeignKeyDetail]


class ConfigurationSchema(BaseModel):
    collection_names: List[str]
    object_types: Dict[str, ObjectType]
    object_fields: Dict[str, ObjectFieldDetails]


class CredentialsSchema(BaseModel):
    url: str
    auth_token: Optional[str] = None


class Configuration(BaseModel):
    credentials: CredentialsSchema
    config: Optional[ConfigurationSchema] = None


RawConfiguration = Configuration


class State(BaseModel):
    client: Client

    class Config:
        arbitrary_types_allowed = True
