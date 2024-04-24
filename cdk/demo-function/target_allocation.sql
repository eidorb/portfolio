create table target_allocation (
  asset text primary key,
  target real
);
insert into
  target_allocation
values
  -- In order as they should appear on stacked area graph (bottom to top).
  ('VDHG', 0.64),
  ('BTC', 0.2),
  ('Cash', 0.1),
  ('NET', 0.02),
  ('AMZN', 0.02),
  ('AAPL', 0.02);
