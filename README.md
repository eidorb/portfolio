# Portfolio

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
- Install Python dependencies:

      micromamba run --name portfolio poetry install
