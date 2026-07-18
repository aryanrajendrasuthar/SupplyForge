from ariadne import QueryType, make_executable_schema

type_defs = """
    type Query {
        health: String!
    }
"""

query = QueryType()


@query.field("health")
def resolve_health(*_) -> str:
    return "ok"


schema = make_executable_schema(type_defs, query)
