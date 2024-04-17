# Portfolio

## Local development

Create SQLite database from portfolio locally:

    micromamba activate portfolio
    # Convert portfolio Beancount ledger to SQLite.
    bean-sql ../portfolio-ledger/portfolio.beancount cdk/function/portfolio.db
    # Create target allocation table.
    sqlite3 cdk/function/portfolio.db < ../portfolio-ledger/target_allocation.sql
    # Create additional tables.
    sqlite3 cdk/function/portfolio.db < tables.sql

Serve Datasette locally:

    datasette cdk/function/portfolio.db --reload --metadata cdk/function/metadata.yaml


# Auth

The Lambda function URL serving Datasette has its auth type set to `NONE`. That
means anyone with knowledge of the URL can invoke the function.

I want to control who is authorised to access my portfolio data. I use the
[datasette-auth-github](https://datasette.io/plugins/datasette-auth-github) Datasette
plugin to authenticate GitHub users.

I registered a new OAuth application on GitHub. The application client ID and secret
are stored in Parameter Store. The Lambda function reads the values of the parameters
and passes them to Datasette as metadata configuration.

The GitHub OAuth application must have its *Authorization callback URL* setting
set to https://portfolio.brodie.id.au/-/github-auth-callback.

Access to Datasette is restricted to my GitHub user ID. Forbidden requests are
redirected to the GitHub auth page.


# Upgrading dependencies

```bash
micromamba activate portfolio
```


## Upgrade CDK Toolkit

```bash
npm update aws-cdk
```


## Upgrade Python dependencies

```bash
poetry update
```


## Upgrade Lambda function dependencies

```bash
cd cdk/function
poetry update
cd -
```

- Use Beancount
- [x] Create build pipeline that pings Up API.
- [x] Generate Beancount balance directives from Up account balances.
- [x] Create build configuration that commits new ledger entries to repository.
- [x] Convert Beancount ledger to SQLite database.
- [x] Retrieve Bitcoin wallet balance.
- [x] Create Beancount Price directives for commodoties.
- [ ] Seed other account balances manually.
- [x] Retrieve SelfWealth balances.
- [x] Retrieve State Custodians balances.
- [ ] Create a Datasette using the exported SQLite file.
- [ ] Configure some pre-canned SQL queries useful for analysing the portfolio.
- [ ] Include visualisations (maybe portfolio over time) using the datasette-vega plugin.
- [ ] Host the Datasette using Lambda with Mangum (this *should* be quite cheap).
- [ ] Use strong OpenID Connect authentication in front of it.
  - Amazon Cognito may be of use here.


# Getting started

- [Install micromamba](https://mamba.readthedocs.io/en/latest/installation.html).
- Create prefix `portfolio`:

      micromamba create --file environment.yml --yes
- Install Node.js dependencies:

      micromamba run --name portfolio npm ci
- Install Python dependencies:

      micromamba run --name portfolio poetry install


## Github Actions secrets

- `TAILSCALE_AUTHKEY`: Ephemeral Tailscale authkey. Must be rotated every 90 days.


## Embedding a dashboard in the index page

Portfolio information is summarised in dashboard charts using the [datasette-dashboards](https://datasette.io/plugins/datasette-dashboards) plugin.
This information should be visible on the index page, rather than having to navigate to the dashboard page.

datasette-dashboards documentation suggests using `<iframe>` elements to embed dashboards and charts in HTML.
However, it was difficult to achieve a responsive layout without scrollbars using this approach.
Instead, a subset of elements from the dashboard page are included in the index page's HTML.
Datasette's index page is customised using the `description_html` [metadata](https://docs.datasette.io/en/stable/metadata.html) property.

The [Datasette CLI](https://docs.datasette.io/en/stable/cli-reference.html#datasette-get) and `extract-dashboard.py` script is used to extract HTML elements from the dashboard page.

The following command extracts dashboard HTML elements to the clipboard for easy pasting into `metadata.yaml`:

```bash
datasette serve \
  --get https://portfolio.brodie.id.au/-/dashboards/portfolio \
  --metadata cdk/function/metadata.yaml \
  cdk/function/portfolio.db | \
python extract-dashboard.py | \
pbcopy
```

This command does the same for the demo application:

```bash
datasette serve \
  --get https://portfolio-demo.brodie.id.au/-/dashboards/portfolio \
  --metadata cdk/function/metadata.yaml \
  cdk/function/portfolio.db | \
python extract-dashboard.py | \
pbcopy
```
