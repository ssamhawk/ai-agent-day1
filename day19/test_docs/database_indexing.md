# Database Indexing and Optimization

## What is a Database Index?

An index is a data structure that improves the speed of data retrieval operations on a database table. Think of it like a book's index - instead of reading every page to find a topic, you look it up in the index.

## How Indexes Work

Most databases use **B-tree** (balanced tree) indexes:

```
       [50]
      /    \
   [25]    [75]
   /  \    /  \
 [10][30][60][90]
```

Finding value 60: Only 3 comparisons instead of scanning all rows!

## Creating Indexes

```sql
-- Single column index
CREATE INDEX idx_users_email ON users(email);

-- Composite index (multiple columns)
CREATE INDEX idx_orders_user_date ON orders(user_id, created_at);

-- Unique index
CREATE UNIQUE INDEX idx_users_username ON users(username);
```

## When to Use Indexes

**Good candidates for indexing:**
- Primary keys (automatically indexed)
- Foreign keys used in JOINs
- Columns in WHERE clauses
- Columns in ORDER BY clauses
- Columns frequently searched

**Bad candidates:**
- Small tables (< 1000 rows)
- Columns with low cardinality (few unique values)
- Columns frequently updated
- Columns never used in queries

## Query Optimization Example

```sql
-- SLOW: No index on email
SELECT * FROM users WHERE email = 'john@example.com';
-- Scans all 1,000,000 rows

-- FAST: With index on email
CREATE INDEX idx_users_email ON users(email);
SELECT * FROM users WHERE email = 'john@example.com';
-- Uses index, finds in ~10 comparisons
```

## Composite Index Order Matters

```sql
-- Index: (user_id, created_at)
-- ✅ Can use index
SELECT * FROM orders WHERE user_id = 123 AND created_at > '2024-01-01';

-- ✅ Can use index (prefix)
SELECT * FROM orders WHERE user_id = 123;

-- ❌ Cannot use index efficiently
SELECT * FROM orders WHERE created_at > '2024-01-01';
```

**Rule:** Composite indexes work left-to-right!

## Covering Indexes

An index that contains all columns needed by a query:

```sql
-- Query needs: user_id, created_at, total
CREATE INDEX idx_orders_covering ON orders(user_id, created_at, total);

-- No table lookup needed!
SELECT user_id, created_at, total
FROM orders
WHERE user_id = 123;
```

## Index Overhead

**Drawbacks of too many indexes:**
- Slower INSERT/UPDATE/DELETE operations
- More storage space required
- Index maintenance overhead

**Best practice:** Index only what you actually query!

## Analyzing Query Performance

```sql
-- PostgreSQL
EXPLAIN ANALYZE
SELECT * FROM users WHERE email = 'john@example.com';

-- MySQL
EXPLAIN
SELECT * FROM orders WHERE user_id = 123;
```

Look for:
- **Seq Scan** (bad) → Full table scan
- **Index Scan** (good) → Using index
- Rows examined vs rows returned

## Full-Text Search Indexes

For searching text content:

```sql
-- PostgreSQL
CREATE INDEX idx_posts_content ON posts USING GIN(to_tsvector('english', content));

SELECT * FROM posts
WHERE to_tsvector('english', content) @@ to_tsquery('docker & kubernetes');
```

## Partial Indexes

Index only rows that match a condition:

```sql
-- Only index active users
CREATE INDEX idx_active_users ON users(email) WHERE status = 'active';
```

Saves space and improves performance for specific queries!

## Index Maintenance

```sql
-- PostgreSQL: Rebuild index
REINDEX INDEX idx_users_email;

-- Analyze table statistics
ANALYZE users;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0;  -- Unused indexes!
```

## Database-Specific Tips

### PostgreSQL
- Supports multiple index types (B-tree, Hash, GIN, GiST)
- Partial indexes
- Expression indexes

### MySQL
- InnoDB uses clustered indexes (data stored in PK order)
- FULLTEXT indexes for text search

### MongoDB
- Supports compound indexes
- Text indexes for search
- Geospatial indexes
