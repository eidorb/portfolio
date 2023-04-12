# Portfolio

## Local development

Create SQLite database from portfolio locally:

    micromamba activate portfolio
    # Convert portfolio Beancount ledger to SQLite.
    bean-sql ../portfolio-ledger/portfolio.beancount portfolio/cdk/function/portfolio.db
    # Create target allocations table.
    sqlite3 portfolio/cdk/function/portfolio.db < ../portfolio-ledger/target_allocations.sql
    # Initialise database with views.
    sqlite3 portfolio/cdk/function/portfolio.db < views.sql

Serve Datasette locally:

    datasette portfolio/cdk/function/portfolio.db --reload --metadata portfolio/cdk/function/metadata.yaml


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
