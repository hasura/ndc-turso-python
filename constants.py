from hasura_ndc import ScalarType

MAX_32_INT = 2147483647
SCALAR_TYPES = {
    "Int": ScalarType(**{
        "aggregate_functions": {
            "sum": {
                "result_type": {
                    "type": "named",
                    "name": "Int"
                }
            }
        },
        "comparison_operators": {
            "_gt": {
                "argument_type": {
                    "type": "named",
                    "name": "Int",
                },
            },
            "_lt": {
                "argument_type": {
                    "type": "named",
                    "name": "Int",
                },
            },
            "_gte": {
                "argument_type": {
                    "type": "named",
                    "name": "Int",
                },
            },
            "_lte": {
                "argument_type": {
                    "type": "named",
                    "name": "Int",
                },
            },
            "_neq": {
                "argument_type": {
                    "type": "named",
                    "name": "Int",
                },
            },
        }
    }),
    "Float": ScalarType(**{
        "aggregate_functions": {
            # "sum": {
            #     "result_type": {
            #         "type": "named",
            #         "name": "Float"
            #     }
            # }
        },
        "comparison_operators": {
            "_gt": {
                "argument_type": {
                    "type": "named",
                    "name": "Float",
                },
            },
            "_lt": {
                "argument_type": {
                    "type": "named",
                    "name": "Float",
                },
            },
            "_gte": {
                "argument_type": {
                    "type": "named",
                    "name": "Float",
                },
            },
            "_lte": {
                "argument_type": {
                    "type": "named",
                    "name": "Float",
                },
            },
            "_neq": {
                "argument_type": {
                    "type": "named",
                    "name": "Float",
                },
            },
        }
    }),
    "String": ScalarType(**{
        "aggregate_functions": {},
        "comparison_operators": {
            "_like": {
                "argument_type": {
                    "type": "named",
                    "name": "String",
                },
            },
            "_glob": {
                "argument_type": {
                    "type": "named",
                    "name": "String",
                },
            },
            "_gt": {
                "argument_type": {
                    "type": "named",
                    "name": "String",
                },
            },
            "_lt": {
                "argument_type": {
                    "type": "named",
                    "name": "String",
                },
            },
            "_gte": {
                "argument_type": {
                    "type": "named",
                    "name": "String",
                },
            },
            "_lte": {
                "argument_type": {
                    "type": "named",
                    "name": "String",
                },
            },
            "_neq": {
                "argument_type": {
                    "type": "named",
                    "name": "String",
                },
            },
        }
    })
}
BASE_FIELDS = {}
BASE_TYPES = {}
