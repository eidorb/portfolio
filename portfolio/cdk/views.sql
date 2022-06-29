-- This pattern finds the latest thing in each category. In this case we want to
-- find the latest price of each currency. Perform a self left join on the category
-- (currency) and a left.id < right.id comparison. Rows with the latest prices for
-- each category have null values in right's columns. The only reason they appear
-- are because of the left join. The null values mean "there are no rows with an
-- id greater than the maximum id".
-- We can use IDs instead of dates because entries in our source files are in
-- chronological order.
create view latest_prices as
select
  left.id,
  left.date,
  left.currency,
  left.amount_number,
  left.amount_currency
from
  price as left
  left join price as right on (
    left.currency = right.currency
    -- Whenever you see this think IDs are as good as dates, because later entries
    -- occur later in the file.
    and left.id < right.id
  )
where
  right.id is null;

create view latest_balances as
select
  left.id,
  left.date,
  left.account,
  left.amount_number,
  left.amount_currency,
  left.diff_number,
  left.diff_currency
from
  balance as left
  left join balance as right on (
    left.account = right.account
    and left.id < right.id
  )
where
  right.id is null;

-- Not all prices are in AUD (amount_currency). A left self join on
-- left.amount_currency = right.currency gives conversion information in right's
-- columns (pricing our prices). Perform conversions if required using coalesce.
create view latest_prices_aud as
select
  left.id,
  left.date,
  left.currency,
  coalesce(
    left.amount_number * right.amount_number,
    left.amount_number
  ) as amount_number,
  coalesce(
    right.amount_currency,
    left.amount_currency
  ) as amount_currency
from
  latest_prices as left
  left join latest_prices as right on left.amount_currency = right.currency;

-- Perform a similar conversion of balance amounts to AUD.
create view latest_balances_aud as
select
  latest_balances.*,
  coalesce(
    latest_balances.amount_number * latest_prices_aud.amount_number,
    latest_balances.amount_number
  ) as amount_aud
from
  latest_balances
  left join latest_prices_aud on latest_balances.amount_currency = latest_prices_aud.currency;

-- Categorise assets (group cash accounts).
create view asset_classes as
-- Filter out the accounts we aren't interested in.
with assets as (
  select
    *
  from
    latest_balances_aud
  where
    account like 'Assets:%'
    or account like 'Liabilities:Bankwest:%'
)
select
  id,
  date,
  account,
  amount_number,
  amount_currency,
  diff_number,
  diff_currency,
  amount_aud,
  case
    when amount_currency in ('AUD', 'USD') then 'Cash'
    else amount_currency
  end as asset_class
from
  assets;
