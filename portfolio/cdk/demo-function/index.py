import json
from pathlib import Path

import yaml
from datasette.app import Datasette
from mangum import Mangum


# Load base metadata from file.
metadata = yaml.safe_load((Path(__file__).parent / "metadata.yaml").open())

# Use Mangum to serve demo Datasette application.
handler = Mangum(
    Datasette(
        # Open database in immutable mode for improved performance.
        immutables=["portfolio.db"],
        # Load precalculated counts from file.
        inspect_data=json.load((Path(__file__).parent / "inspect_data.json").open()),
        metadata=metadata,
    ).app(),
    # Content-Length header is not allowed in Lambda@Edge responses.
    exclude_headers=["Content-Length"],
)
