from datasette.app import Datasette
from mangum import Mangum

# Serve a minimal Datasette application with Mangum.
handler = Mangum(Datasette().app())
