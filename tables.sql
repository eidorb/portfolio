-- Fill in balances in AUD for all accounts for every date with an entry.
create table normalised_balance_aud as
-- Every date that has a balance entry.
with date as (
  select
    distinct date
  from
    balance
),
-- First balance entries for each account.
account as (
  select
    account,
    min(date) as first_balance_date
  from
    balance
  group by
    account
  order by
    id
),
-- Fill in balances for all accounts for every date with an entry.
normalised_balance as (
  select
    date.date,
    account.account,
    balance.amount_number,
    balance.amount_currency,
    max(balance.id)
  from
    date -- Accounts should appear only after their first balance entries.
    join account on date.date >= account.first_balance_date
    left join balance on date.date >= balance.date
    and balance.account = account.account
  group by
    date.date,
    account.account
),
-- Convert all prices to AUD.
price_aud as (
  select
    price.id,
    price.date,
    price.currency,
    coalesce(
      price.amount_number * price_2.amount_number,
      price.amount_number
    ) as amount_number,
    coalesce(
      price_2.amount_currency,
      price.amount_currency
    ) as amount_currency,
    max(price_2.id)
  from
    price
    left join price as price_2 on price.amount_currency = price_2.currency
    and price.date >= price_2.date
  group by
    price.id
)
select
  normalised_balance.date,
  normalised_balance.account,
  normalised_balance.amount_number,
  normalised_balance.amount_currency,
  coalesce(price_aud.amount_number, 1) as price_aud,
  coalesce(
    normalised_balance.amount_number * price_aud.amount_number,
    normalised_balance.amount_number
  ) as value_number,
  coalesce(
    price_aud.amount_currency,
    normalised_balance.amount_currency
  ) as value_currency,
  case
    when normalised_balance.amount_currency in ('AUD', 'USD') then 'Cash'
    else normalised_balance.amount_currency
  end as asset,
  max(price_aud.date)
from
  normalised_balance
  left join price_aud on normalised_balance.date >= price_aud.date
  and normalised_balance.amount_currency = price_aud.currency
group by
  normalised_balance.date,
  normalised_balance.account;

-- Latest balances of each account.
create table latest_balance as
select
  *,
  max(date)
from
  normalised_balance_aud
group by
  account;


-- Calculate changes required to reach target allocations.
create table change as
-- Group accounts into asset categories.
with asset as (
  select
    date,
    latest_balance.asset,
    price_aud,
    sum(value_number) as value,
    sum(value_number) over() as total
  from
    latest_balance
  where
    -- Don't treat debt as cash.
    account not like 'Liabilities:StateCustodians:%'
  group by
    latest_balance.asset
)
select
  asset.*,
  target,
  target * total as target_value,
  value / total as actual,
  target - value / total as change,
  target * total - value as change_value,
  (target * total - value) / price_aud as change_amount
from
  asset
  join target_allocation on asset.asset = target_allocation.asset;
