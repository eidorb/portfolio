"""Datasette metadata"""
metadata = {
    # Restrict access to me.
    "allow": {
        "gh_id": "1782750",
    },
    "plugins": {
        "datasette-auth-github": {
            "client_id": {"$env": "GITHUB_CLIENT_ID"},
            "client_secret": {"$env": "GITHUB_CLIENT_SECRET"},
        },
        "datasette-redirect-forbidden": {
            "redirect_to": "/-/github-auth-start",
        },
        "datasette-dashboards": {
            "dashboard": {
                "title": "Portfolio allocations",
                "charts": {
                    "change": {
                        "title": "Change required to reach target allocations",
                        "db": "portfolio",
                        "query": "select * from changes order by change desc",
                        "library": "vega",
                        "display": {
                            "encoding": {
                                "x": {
                                    "field": "change",
                                    "type": "quantitative",
                                    "stack": None,
                                    "axis": None,
                                },
                                "y": {
                                    "field": "asset_class",
                                    "type": "nominal",
                                    "sort": None,
                                    "axis": None,
                                },
                                "color": {
                                    "value": "red",
                                    "condition": {
                                        "test": "datum.change>0",
                                        "value": "limegreen",
                                    },
                                },
                            },
                            "layer": [
                                {"mark": "bar"},
                                {
                                    "mark": {
                                        "type": "text",
                                        "align": {
                                            "expr": "datum.change>0?'right':'left'"
                                        },
                                        "dx": {"expr": "datum.change>0?-4:4"},
                                    },
                                    "encoding": {
                                        "text": {"field": "asset_class"},
                                        "color": {"value": "black"},
                                        "x": {"datum": 0},
                                    },
                                },
                                {
                                    "mark": {
                                        "type": "text",
                                        "align": {
                                            "expr": "datum.change>0?'left':'right'"
                                        },
                                        "dx": {"expr": "datum.change>0?4:-4"},
                                    },
                                    "encoding": {
                                        "text": {"field": "change", "format": ".1%"},
                                        "color": {"value": "black"},
                                    },
                                },
                            ],
                        },
                    }
                },
            }
        },
    },
}
