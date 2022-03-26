# Portfolio

- [x] Create build pipeline that pings Up API.
- [x] Generate Beancount balance directives from Up account balances.
- [ ] Create build configuration that commits new ledger entries to repository.
- [ ] Create a ledger of portfolio account balances and prices. (Prices are used for currency conversion.)
  - The Beancount ledger format seems as good as any - use it.
- [ ] Each day, automatically retrieve balances and prices and write them to the ledger.
  - Because this is just account *balances*, not transactions, this should be simple to automate.
- [ ] Export Beancount ledger to SQLite.
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
