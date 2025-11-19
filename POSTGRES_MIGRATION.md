# Heroku Postgres Migration Guide

This guide will help you migrate from SQLite to Heroku Postgres for production.

## Step 1: Add Heroku Postgres Addon

Run this command in your terminal (or add via Heroku dashboard):

```bash
heroku addons:create heroku-postgresql:mini
```

The `mini` plan is free and suitable for small applications. For larger databases, consider `basic` or higher plans.

## Step 2: Verify DATABASE_URL

After adding Postgres, Heroku automatically sets the `DATABASE_URL` environment variable. You can verify it:

```bash
heroku config:get DATABASE_URL
```

## Step 3: Deploy Code

The code has already been updated to use Postgres when `DATABASE_URL` is set. Just push to GitHub and Heroku will auto-deploy:

```bash
git push origin main
```

## Step 4: Initialize Database Tables

The database tables will be created automatically when the app first runs, but you may need to run setup scripts manually via Heroku console:

```bash
heroku run python setup_awards_table.py
heroku run python setup_schedule_tables.py
heroku run python setup_hole_in_one_tables.py
```

## Step 5: Migrate Existing Data (Optional)

If you have important data in your local SQLite database that you want to migrate:

1. Export data from local database:
```bash
python migrate_database.py
```

2. Import to Heroku Postgres:
```bash
heroku pg:psql < exported_data.sql
```

## How It Works

- **Local Development**: Uses SQLite (`golf_scores.db`) when `DATABASE_URL` is not set
- **Production (Heroku)**: Automatically uses Postgres when `DATABASE_URL` environment variable is present
- **Query Compatibility**: The `db_helper.py` module automatically converts SQLite `?` placeholders to Postgres `%s` placeholders

## Benefits

✅ **Persistent Storage**: Data survives deployments and dyno restarts  
✅ **No Data Loss**: Events and awards won't disappear on deployments  
✅ **Better Performance**: Postgres is optimized for production workloads  
✅ **Scalability**: Easy to upgrade as your app grows  

## Troubleshooting

If you see connection errors:
1. Verify Postgres addon is active: `heroku addons`
2. Check DATABASE_URL is set: `heroku config`
3. View logs: `heroku logs --tail`

