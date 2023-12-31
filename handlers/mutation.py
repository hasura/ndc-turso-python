from models import *
from libsql_client import Statement, ResultSet
from libsql_client.sqlite3 import LibsqlError
from typing import List, Dict
from handlers.query import plan_queries, perform_query, QueryRequest


class ConnectorError(Exception):
    def __init__(self, status_code: int, message: str, details: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details if details is not None else {}


async def execute_sql_transaction(state: State, statements: List[Statement]) -> List[ResultSet]:
    client = state.client
    try:
        batch_results = await client.batch(statements)
        return batch_results
    except LibsqlError as e:
        raise ConnectorError(
            status_code=400,
            message=str(e),
            details={}
        )


def build_insert_sql(table: str, data: list, returning: bool = False) -> tuple:
    if not data:
        return "", []

    columns = ', '.join([f'"{col}"' for col in data[0].keys()])
    placeholders = '(' + ', '.join(['?'] * len(data[0])) + ')'
    values_tuple = ', '.join([placeholders] * len(data))
    returning_clause = "RETURNING *" if returning else ""
    sql = f"INSERT INTO \"{table}\" ({columns}) VALUES {values_tuple} {returning_clause}"
    values = [val for item in data for val in item.values()]
    return sql, values


def build_update_sql(table: str, pk_columns: dict, set_arguments: dict, inc_arguments: dict,
                     returning: bool = False) -> tuple:
    set_clauses = []
    args = []

    # Handle _set argument
    if set_arguments:
        for column, value in set_arguments.items():
            set_clauses.append(f'"{column}" = ?')
            args.append(value)

    # Handle _inc argument
    if inc_arguments:
        for column, increment_value in inc_arguments.items():
            set_clauses.append(f'"{column}" = "{column}" + ?')
            args.append(increment_value)

    where_clause = ' AND '.join([f'"{column}" = ?' for column in pk_columns.keys()])
    args.extend(pk_columns.values())

    if set_clauses:
        set_clause = ', '.join(set_clauses)
        returning_clause = "RETURNING *" if returning else ""
        sql = f"UPDATE \"{table}\" SET {set_clause} WHERE {where_clause} {returning_clause}"
        return sql, args
    else:
        return "", []


def build_delete_sql(table: str, pk_columns: dict, returning: bool = False) -> tuple:
    where_clause = ' AND '.join([f'"{column}" = ?' for column in pk_columns.keys()])
    args = list(pk_columns.values())
    returning_clause = "RETURNING *" if returning else ""
    sql = f"DELETE FROM \"{table}\" WHERE {where_clause} {returning_clause}"
    return sql, args


def build_binary_expression(field_name: str, operator: str, value: Any) -> Expression:
    return Expression(
        type='binary_comparison_operator',
        column=ComparisonTarget(type='column', name=field_name, path=[]),
        operator=BinaryComparisonOperator(type='other', name=operator),
        value=ComparisonValue(type='scalar', value=value)
    )


def build_field_expressions(field_name: str, conditions: Any) -> List[Expression]:
    # Build expressions for each condition on a specific field
    if isinstance(conditions, dict):
        # Single condition for a field
        return [build_binary_expression(field_name, operator, value) for operator, value in conditions.items()]
    elif isinstance(conditions, list):
        # Multiple conditions for a field
        return [build_expression(cond) for cond in conditions]
    else:
        raise ValueError(f"Invalid condition format for field '{field_name}'")


def build_expression(where: Dict[str, Any]) -> Expression | None:
    if where is None:
        return None

    expressions = []

    for key, value in where.items():
        if key in ['_and', '_or', '_not']:
            # Handle logical operators
            if key == '_not':
                expressions.append(Expression(
                    type='not',
                    expression=build_expression(value)
                ))
            else:
                sub_expressions = [build_expression(cond) for cond in value]
                expressions.append(Expression(
                    type=key[1:],  # Removing the underscore from '_and' or '_or'
                    expressions=sub_expressions
                ))
        else:
            # Handle binary comparison operators for specific fields
            field_expressions = build_field_expressions(key, value)
            expressions.extend(field_expressions)

    if len(expressions) == 1:
        return expressions[0]  # Return the single expression directly
    else:
        return Expression(
            type='and',  # Default to 'and' if there are multiple top-level expressions
            expressions=expressions
        )


def build_query_request(operation: MutationOperation,
                        collection_relationships: Dict[str, Relationship]) -> QueryRequest:
    q = Query(
        aggregates=None,
        fields=operation.fields,
        limit=operation.arguments.get("limit"),
        offset=operation.arguments.get("offset"),
        where=build_expression(operation.arguments.get("where", None))
    )
    qr = QueryRequest(
        arguments={},
        variables=None,
        collection=operation.name[len("list_"):],
        collection_relationships=collection_relationships,
        query=q
    )
    return qr


async def mutation(configuration: Configuration, state: State, mutation_request: MutationRequest) -> MutationResponse:
    statements = []
    results = []
    for op in mutation_request.operations:
        if op.type == 'procedure':
            if op.name.startswith('insert_'):
                prefix_len = len('insert_')
                suffix_len = len('_one') if op.name.endswith('_one') else len('_many')
                table = op.name[prefix_len:-suffix_len]
                data = [op.arguments['object']] if op.name.endswith('_one') else op.arguments['objects']
                returning = not (op.arguments.get("return") is None or int(op.arguments.get("return")) <= 0)
                sql, args = build_insert_sql(table, data, returning=returning)
                if sql:
                    statements.append(Statement(sql=sql, args=args))
                else:
                    print(f"No data to insert for operation {op.name}")
            elif op.name.startswith('update_'):
                if op.name.endswith("_by_pk"):
                    table = op.name[len('update_'):-len('_by_pk')]
                    pk_columns = op.arguments["pk_columns"]
                    assert isinstance(pk_columns, dict)
                    _set = op.arguments.get("_set", {})
                    _inc = op.arguments.get("_inc", {})
                    returning = not (op.arguments.get("return") is None or int(op.arguments.get("return")) <= 0)
                    sql, args = build_update_sql(table, pk_columns, _set, _inc, returning=returning)
                    if sql:
                        statements.append(Statement(sql=sql, args=args))
                    else:
                        print(f"No update set for operation {op.name}")
                else:
                    raise NotImplemented("This is not implemented")
            elif op.name.startswith("delete_"):
                if op.name.endswith("_by_pk"):
                    table = op.name[len('delete_'):-len('_by_pk')]
                    pk_columns = op.arguments["pk_columns"]
                    assert isinstance(pk_columns, dict)
                    # Returning is always none for SQLite, MySQL, but for things like Postgres it might not be.
                    returning = not (op.arguments.get("return") is None or int(op.arguments.get("return")) <= 0)
                    sql, args = build_delete_sql(table, pk_columns, returning=returning)
                    if sql:
                        statements.append(Statement(sql=sql, args=args))
                    else:
                        print(f"No primary key provided for delete operation {op.name}")
                else:
                    raise NotImplemented("This is not implemented")
            elif op.name.startswith("list_"):
                print(mutation_request.model_dump_json(indent=4))
                query_request = build_query_request(op,
                                                    collection_relationships=mutation_request.collection_relationships)
                query_plans = await plan_queries(configuration, query_request)
                query_response = await perform_query(state, query_plans)
                res = MutationResponse(
                    operation_results=[
                        MutationOperationResults(
                            affected_rows=len(query_response),
                            returning=[
                                {"__value": query_response[0].get("rows")}
                            ]
                        )
                    ]
                )
                print(res)
                return res
            else:
                raise NotImplemented("This is not implemented")
    if len(statements) > 0:
        results = await execute_sql_transaction(state, statements)
    returning = []
    for r in results:
        for values in r.rows:
            if len(returning) == 0:
                returning.append({"__value": []})
            returning[0]["__value"].append(dict(zip(r.columns, values)))
    else:
        if len(returning) == 0:
            returning.append({"__value": None})
    response = MutationResponse(
        operation_results=[
            MutationOperationResults(
                affected_rows=len(returning),
                returning=returning
            )
        ]
    )
    return response
