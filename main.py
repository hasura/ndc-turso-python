# from hasura_ndc import *
from hasura_ndc.models import *
from hasura_ndc.main import start
from typing import Optional, Dict, Any
import libsql_client
from models import Configuration, State
from handlers.query_explain import query_explain
from handlers.get_schema import get_schema
# from handlers.update_configuration import update_configuration
from handlers.query import query
from handlers.mutation import mutation
from hasura_ndc.connector import Connector
import json


class RootConnector(Connector[Configuration, State]):

    def __init__(self):
        super().__init__(Configuration, State)

    async def parse_configuration(self, configuration_dir: str) -> Configuration:
        with open(configuration_dir, "r") as f:
            configuration = json.load(f)
        config = Configuration(**configuration)
        return config

    async def try_init_state(self, configuration: Configuration, metrics: Any) -> State:
        credentials = configuration.credentials.model_dump()
        client = libsql_client.create_client(**credentials)
        return State(
            client=client
        )

    async def get_capabilities(self, configuration: Configuration) -> CapabilitiesResponse:
        return CapabilitiesResponse(
            version="^0.1.0",
            capabilities=Capabilities(
                query=QueryCapabilities(
                    aggregates=LeafCapability(),
                    variables=LeafCapability(),
                    explain=LeafCapability()
                ),
                mutation=MutationCapabilities(
                    transactional=LeafCapability(),
                    explain=None
                ),
                relationships=RelationshipCapabilities(
                    relation_comparisons=LeafCapability(),
                    order_by_aggregate=LeafCapability()
                )
            )
        )

    async def get_schema(self,
                         configuration: Configuration) -> SchemaResponse:
        return await get_schema(configuration)

    async def query_explain(self,
                            configuration: Configuration,
                            state: State,
                            request: QueryRequest) -> ExplainResponse:
        return await query_explain(configuration, state, request)

    async def mutation_explain(self,
                               configuration: Configuration,
                               state: State,
                               request: MutationRequest) -> ExplainResponse:
        pass

    async def query(self, configuration: Configuration, state: State, request: QueryRequest) -> QueryResponse:
        return await query(configuration, state, request)

    async def mutation(self, configuration: Configuration,
                       state: State,
                       request: MutationRequest) -> MutationResponse:
        return await mutation(configuration, state, request)

    async def fetch_metrics(self,
                            configuration: Configuration,
                            state: State) -> Optional[None]:
        pass

    async def health_check(self,
                           configuration: Configuration,
                           state: State) -> Optional[None]:
        pass


if __name__ == "__main__":
    c = RootConnector()
    start(c)
