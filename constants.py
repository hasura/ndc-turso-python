from hasura_ndc.models import ScalarType

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
            "_eq": {
              "type": "equal"
            },
            "_gt": {
                "type": "custom",
                "argument_type": {
                    "type": "named",
                    "name": "Int",
                }
            },
            "_lt": {
                "type": "custom",
                "argument_type": {
                    "type": "named",
                    "name": "Int",
                },
            },
            "_gte": {
                "type": "custom",
                "argument_type": {
                    "type": "named",
                    "name": "Int",
                },
            },
            "_lte": {
                "type": "custom",
                "argument_type": {
                    "type": "named",
                    "name": "Int",
                },
            },
            "_neq": {
                "type": "custom",
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
            "_eq": {
                "type": "equal"
            },
            "_gt": {
                "type": "custom",
                "argument_type": {
                    "type": "named",
                    "name": "Float",
                },
            },
            "_lt": {
                "type": "custom",
                "argument_type": {
                    "type": "named",
                    "name": "Float",
                },
            },
            "_gte": {
                "type": "custom",
                "argument_type": {
                    "type": "named",
                    "name": "Float",
                },
            },
            "_lte": {
                "type": "custom",
                "argument_type": {
                    "type": "named",
                    "name": "Float",
                },
            },
            "_neq": {
                "type": "custom",
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
            "_eq": {
                "type": "equal"
            },
            "_like": {
                "type": "custom",
                "argument_type": {
                    "type": "named",
                    "name": "String",
                },
            },
            "_glob": {
                "type": "custom",
                "argument_type": {
                    "type": "named",
                    "name": "String",
                },
            },
            "_gt": {
                "type": "custom",
                "argument_type": {
                    "type": "named",
                    "name": "String",
                },
            },
            "_lt": {
                "type": "custom",
                "argument_type": {
                    "type": "named",
                    "name": "String",
                },
            },
            "_gte": {
                "type": "custom",
                "argument_type": {
                    "type": "named",
                    "name": "String",
                },
            },
            "_lte": {
                "type": "custom",
                "argument_type": {
                    "type": "named",
                    "name": "String",
                },
            },
            "_neq": {
                "type": "custom",
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
