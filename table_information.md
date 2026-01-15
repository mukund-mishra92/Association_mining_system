# Table Information for Association Mining System

## 1. Tables Created Through Code

These tables are created automatically by the application if they do not exist:

| Table Name                | Purpose                                 | Created By Code | Notes                                  |
|---------------------------|-----------------------------------------|:--------------:|----------------------------------------|
| mining_schedules          | Stores mining job schedules             |      Yes       | Scheduler configuration                |
| mining_schedule_stats     | Stores stats for schedules              |      Yes       | Execution stats for each schedule      |
| mining_job_logs           | Stores mining job logs                  |      Yes       | Logs for all mining jobs (API/UI/Sched)|
| sku_recommendations       | Stores mining results (rules)           |      Yes*      | Created if output_table is set         |
| article_proximity_score   | Stores mining results (rules, alt)      |      Yes*      | Created if output_table is set         |

*Created dynamically if specified as output table.

---

## 2. Tables Written To (INSERT/UPDATE)

| Table Name                | Written To By           | Purpose                                 |
|---------------------------|------------------------|-----------------------------------------|
| mining_job_logs           | Logging system         | Logs every mining job (API/UI/Sched)    |
| mining_schedule_stats     | Scheduler              | Updates stats after each scheduled run  |
| sku_recommendations       | Mining service         | Saves generated rules                   |
| article_proximity_score   | Mining service         | Saves generated rules (alternative)     |

---

## 3. Tables Read From (SELECT)

| Table Name                | Read By                | Purpose                                 |
|---------------------------|------------------------|-----------------------------------------|
| mining_schedules          | Scheduler, UI          | Loads schedules                         |
| mining_job_logs           | Logs UI, API           | Displays job logs                       |
| mining_schedule_stats     | Scheduler, UI          | Shows schedule/job stats                |
| sku_recommendations       | Mining/Results UI      | Loads mining results                    |
| article_proximity_score   | Mining/Results UI      | Loads mining results (alternative)      |
| order_table (configurable)| Mining service         | Loads order data for mining             |
| sku_master (configurable) | Mining service         | Loads SKU data for mining               |

---

## 4. Typical Table Map

| Table Name                   | Created By Code | Written To | Read From | Purpose                        |
|------------------------------|:--------------:|:----------:|:---------:|--------------------------------|
| mining_schedules             |      Yes       |    Yes     |   Yes     | Stores mining job schedules    |
| mining_schedule_stats        |      Yes       |    Yes     |   Yes     | Stores stats for schedules     |
| mining_job_logs              |      Yes       |    Yes     |   Yes     | Stores mining job logs         |
| sku_recommendations          |      Yes*      |    Yes     |   Yes     | Stores mining results          |
| article_proximity_score      |      Yes*      |    Yes     |   Yes     | Stores mining results (alt)    |
| order_table (configurable)   |      No        |    No      |   Yes     | Source order data              |
| sku_master (configurable)    |      No        |    No      |   Yes     | Source SKU data                |

---

## 5. Notes

- `order_table` and `sku_master` are set in your `.env` or UI and are **not created** by the app; they must exist in your database.
- Output tables like `sku_recommendations` or `article_proximity_score` are created if they do not exist, based on mining configuration.
- All mining jobs (API, UI, Scheduler) are logged in `mining_job_logs`.
- Schedule stats are updated in `mining_schedule_stats` after each scheduled run.

---

## 6. How to List All Tables in MySQL

```sql
SHOW TABLES;
```

---

## 7. How to Search for Table Usage in Code

```bash
# Find all table creation
rg -i "create table" .

# Find all table usage
rg -i "(from|into|update) [a-zA-Z0-9_]+" .
```

---

*Last updated: 2026-01-15*
