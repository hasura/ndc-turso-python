from models import Configuration, State, QueryRequest, QueryResponse, Query, Expression, MutationResponse, MutationOperationResults
from typing import List, Any, Dict, Optional
import json
from libsql_client import Statement
from constants import MAX_32_INT


def escape_single(s: Any) -> str:
    return f"'{s}'"


def escape_double(s: Any) -> str:
    return f'"{s}"'


def wrap_data(s: str) -> str:
    return f"""
SELECT
(
  {s}
) as data
"""


def wrap_rows(s: str) -> str:
    return f"""
SELECT
  JSON_OBJECT('rows', JSON_GROUP_ARRAY(JSON(r)))
FROM
  (
    {s}
  )
"""


def build_where(expression: Expression, args: List, variables: Dict[str, Any]) -> str:
    if expression.type == 'unary_comparison_operator':
        if expression.operator == 'is_null':
            sql = f"{expression.column.name} IS NULL"
        else:
            raise ValueError("Unknown Unary Comparison Operator")
    elif expression.type == 'binary_comparison_operator':
        value_type = expression.value.type
        if value_type == 'scalar':
            args.append(expression.value.value)
        elif value_type == 'variable':
            if variables:
                args.append(variables[expression.value.name])
        elif value_type == 'column':
            raise ValueError("Column type in binary comparison not implemented")
        else:
            raise ValueError("Unknown Binary Comparison Value Type")
        operator_type = expression.operator.type
        if operator_type == 'equal':
            sql = f"{expression.column.name} = ?"
        elif operator_type == 'other':
            operator_name = expression.operator.name
            if operator_name == '_like':
                sql = f"{expression.column.name} LIKE ?"
            elif operator_name == '_glob':
                sql = f"{expression.column.name} GLOB ?"
            elif operator_name == '_neq':
                sql = f"{expression.column.name} != ?"
            elif operator_name == '_gt':
                sql = f"{expression.column.name} > ?"
            elif operator_name == '_lt':
                sql = f"{expression.column.name} < ?"
            elif operator_name == '_gte':
                sql = f"{expression.column.name} >= ?"
            elif operator_name == '_lte':
                sql = f"{expression.column.name} <= ?"
            else:
                raise ValueError("Invalid Expression Operator Name")
        else:
            raise ValueError("Binary Comparison Custom Operator not implemented")
    elif expression.type == 'and':
        if not expression.expressions:
            sql = "1"
        else:
            clauses = [build_where(expr, args, variables) for expr in expression.expressions]
            sql = f"({' AND '.join(clauses)})"
    elif expression.type == 'or':
        if not expression.expressions:
            sql = "1"
        else:
            clauses = [build_where(expr, args, variables) for expr in expression.expressions]
            sql = f"({' OR '.join(clauses)})"
    elif expression.type == 'not':
        not_result = build_where(expression.expression, args, variables)
        sql = f"NOT ({not_result})"
    elif expression.type == 'binary_array_comparison_operator':
        raise ValueError("Binary Array Comparison Operator not implemented")
    elif expression.type == 'exists':
        raise ValueError("Exists not implemented")
    else:
        raise ValueError("Unknown Expression Type")
    return sql


def build_query(config: Configuration,
                query_request: QueryRequest, collection: str,
                q: Query,
                path: List[str],
                variables: Dict[str, Any],
                args: List[Any],
                relationship_key: Optional[str]) -> Dict[str, Any]:
    path.append(collection)
    collection_alias = "_".join(path)

    limit_sql = ""
    offset_sql = ""
    order_by_sql = ""
    collect_rows = []
    where_conditions = ["WHERE 1"]

    # Handle fields and relationships
    if q.fields:
        for field_name, field_value in q.fields.items():
            collect_rows.append(escape_single(field_name))
            if field_value.type == 'column':
                collect_rows.append(escape_double(field_value.column))
            elif field_value.type == 'relationship':
                rel_query = build_query(config,
                                        query_request,
                                        field_name,
                                        field_value.query,
                                        path.copy(),
                                        variables,
                                        args,
                                        field_value.relationship)
                collect_rows.append(f"({rel_query['sql']})")

    # Default to selecting all columns if no specific fields are provided
    if not collect_rows:
        collect_rows.append('*')

    # Build FROM clause
    from_sql = f'{escape_double(collection)} as {escape_double(collection_alias)}'
    if len(path) > 1 and relationship_key is not None:
        relationship = query_request.collection_relationships[relationship_key]
        parent_alias = "_".join(path[:-1])
        from_sql = f'{escape_double(relationship.target_collection)} as {escape_double(collection_alias)}'
        for from_col, to_col in relationship.column_mapping.items():
            where_conditions.append(
                f'{escape_double(parent_alias)}.{escape_double(from_col)} = '
                f'{escape_double(collection_alias)}.{escape_double(to_col)}')

    # Build WHERE clause
    if q.where:
        where_conditions.append(f'({build_where(q.where, args, variables)})')

    # Build ORDER BY clause
    if q.order_by:
        order_elems = [f'{escape_double(elem.target.name)} {elem.order_direction}' for elem in
                       q.order_by.elements if elem.target.type == 'column']
        if order_elems:
            order_by_sql = f'ORDER BY {", ".join(order_elems)}'

    # Handle LIMIT and OFFSET
    if q.limit:
        limit_sql = f'LIMIT {escape_single(q.limit)}'
    if q.offset:
        if not q.limit:
            limit_sql = f'LIMIT {MAX_32_INT}'
        offset_sql = f'OFFSET {escape_single(q.offset)}'

    # Construct the final SQL
    sql = wrap_rows(f"""
SELECT
JSON_OBJECT({", ".join(collect_rows)}) as r
FROM {from_sql}
{" AND ".join(where_conditions)}
{order_by_sql}
{limit_sql}
{offset_sql}
""")

    # Wrap in data select for top-level queries
    if len(path) == 1:
        sql = wrap_data(sql)

    return {'sql': sql, 'args': args}


async def plan_queries(configuration: Configuration, q: QueryRequest) -> List[Statement]:
    if not configuration.config:
        raise ValueError("Connector is not properly configured")

    query_plan = []
    if q.variables:
        for var_set in q.variables.values():
            qp = build_query(configuration,
                             q,
                             q.collection,
                             q.query,
                             [],
                             var_set,
                             [],
                             None)
            st = Statement(sql=qp["sql"], args=qp["args"])
            query_plan.append(st)
    else:
        qp = build_query(configuration,
                         q,
                         q.collection,
                         q.query,
                         [],
                         {},
                         [],
                         None)
        st = Statement(sql=qp["sql"], args=qp["args"])
        query_plan.append(st)
    return query_plan


async def perform_query(state: State, query_plans: List[Statement]) -> QueryResponse:
    client = state.client
    results = await client.batch(query_plans)
    res = [json.loads(r.rows[0]["data"]) for r in results]
    return res


async def query(configuration: Configuration, state: State, query_request: QueryRequest) -> QueryResponse:
    print(query_request.model_dump_json(indent=4))
    if query_request.collection.startswith("list_"):
        # This won't work. :/ Blocked again.
        # Functional Queries just can't return Anything? I'm so confused.
        query_request.collection = query_request.collection[len("list_"):]
        if query_request.arguments.get("limit") is not None:
            limit = query_request.arguments.get("limit", None)
            if limit is not None and limit.value is not None:
                limit = limit.value
            offset = None
            where = None
            query_request.query.limit = limit
            query_request.query.offset = offset
            query_request.query.where = where
    query_plans = await plan_queries(configuration, query_request)
    query_response = await perform_query(state, query_plans)
    return query_response
