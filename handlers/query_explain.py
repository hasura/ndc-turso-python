try:
    from models import Configuration, State, QueryRequest, ExplainResponse
except ImportError:
    from ..models import Configuration, State, QueryRequest, ExplainResponse


async def query_explain(configuration: Configuration, state: State, query_request: QueryRequest) -> ExplainResponse:
    pass
