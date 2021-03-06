---
layout: single
title: Java - Loading an entire Cassandra table in parallel
date: 2018-08-23 08:02:37.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Java
- Programming
tags: []
meta:
  _edit_last: '14827209'
  geo_public: '0'
  _publicize_job_id: '21381978858'
  timeline_notification: '1535029358'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2018/08/23/java-loading-an-entire-cassandra-table-in-parallel/"
---
Sometimes, it is required to load all rows in the Cassandra table but it is very slow if loading is performed by a single thread.
Let's say we have the following table in Cassandra
```sql
CREATE TABLE users (
  userid text PRIMARY KEY,
  first_name text,
  last_name text,
  emails set<text>,
  top_scores list<int>,
  todo map<timestamp, text>
);
```

If we load the entire table with the following CQL syntax in a single thread, it can take several hours if number of rows is 10 million.
```sql
select * from users;
```

Fortunately, there is a way to load an entire table in parallel. Astyanax has a class called AllRowsReader which is showing how to load entire table in parallel.
The basic idea of this code is to use token() keyword on selecting data. Since Cassandra is using hashing mechanism on distributing data in multiple hosts. If we know the token range, Cassandra is allow to load data in parallel.

For example, the below CQL syntax will load users rows between 0 and 10000 but this token value will be determined by the configured current partitioner in Cassandra.
```sql
select * from users where token(userid) >= 0 and token(userid) <= 10000;
```

The below code is summarizing this idea.
```java
public class TokenRange
{
    private final BigInteger beginToken;
    private final BigInteger endToken;
    public TokenRange(BigInteger beginToken, BigInteger endToken)
    {
        this.beginToken = beginToken;
        this.endToken = endToken;
    }
    public BigInteger getBeginToken()
    {
        return beginToken;
    }
    public BigInteger getEndToken()
    {
        return endToken;
    }
}
```
```java
public interface TokenPartitioner
{
    List<TokenRange> splitTokenRange(int count);
}
```
```java
public class MurmurPartitioner implements TokenPartitioner
{
    private static final BigInteger MIN = new BigInteger(Long.toString(Long.MIN_VALUE));
    private static final BigInteger MAX = new BigInteger(Long.toString(Long.MAX_VALUE));
    @Override
    public List<TokenRange> splitTokenRange(int count)
    {
        List<TokenRange> tokens = new ArrayList<>();
        List<BigInteger> splits = splitRange(MIN, MAX, count);
        Iterator<BigInteger> iter = splits.iterator();
        BigInteger current = iter.next();
        while (iter.hasNext())
        {
            BigInteger next = iter.next();
            tokens.add(new TokenRange(current, next));
            current = next;
        }
        return tokens;
    }
    public static List<BigInteger> splitRange(BigInteger first, BigInteger last, int count)
    {
        List<BigInteger> tokens = new ArrayList<>();
        tokens.add(first);
        BigInteger delta = (last.subtract(first).divide(BigInteger.valueOf((long) count)));
        BigInteger current = first;
        for (int i = 0; i < count - 1; i++)
        {
            current = current.add(delta);
            tokens.add(current);
        }
        tokens.add(last);
        return tokens;
    }
}
```
```java
public class AllRowReader<T>
{
    private static final Logger log = LoggerFactory.getLogger(AllRowCqlReader.class);
    private final Cluster cluster;
    private final Session session;
    private final static int DEFAULT_PAGE_SIZE = 100;
    private final String tableName;
    private final List<String> partitionKeyNames;
    private final Class<T> klass;
    private int pageSize;
    private int concurrencyLevel;
    private final Map<String, TokenPartitioner> partitionerMap = ImmutableMap.of(
            "org.apache.cassandra.dht.Murmur3Partitioner", new MurmurPartitioner(),
            "org.apache.cassandra.dht.RandomPartitioner", new RandomPartitioner()
    );
    public static class Builder<T>
    {
        private final Cluster cluster;
        private final Session session;
        private final String tableName;
        private final List<String> partitionKeyNames;
        private final Class<T> klass;
        private int pageSize = DEFAULT_PAGE_SIZE;
        private int concurrencyLevel = 4;
        public Builder(Cluster cluster,
                       Session session,
                       String tableName,
                       List<String> partitionKeyNames,
                       Class<T> klass)
        {
            this.cluster = cluster;
            this.Session = session;
            this.tableName = tableName;
            this.partitionKeyNames = partitionKeyNames;
            this.klass = klass;
        }
        public Builder<T> withPageSize(int pageSize)
        {
            this.pageSize = pageSize;
            return this;
        }
        public Builder<T> withConcurrencyLevel(int level)
        {
            this.concurrencyLevel = level;
            return this;
        }
        public AllRowReader<T> build()
        {
            return new AllRowCqlReader<>(cluster,
                    session,
                    tableName,
                    partitionKeyNames,
                    klass,
                    pageSize,
                    concurrencyLevel);
        }
    }
    private AllRowCqlReader(Cluster cluster,
                            Session session,
                            String tableName,
                            List<String> partitionKeyNames,
                            Class<T> klass,
                            int pageSize,
                            int concurrencyLevel)
    {
        this.cluster = cluster;
        this.session = session;
        this.tableName = tableName;
        this.partitionKeyNames = partitionKeyNames;
        this.klass = klass;
        this.pageSize = pageSize;
        this.concurrencyLevel = concurrencyLevel;
    }
    public void executeWithCallback(Function<List<T>, Boolean> callback)
    {
        TokenPartitioner partitioner = findTokenPartitioner();
        List<TokenRange> tokens = partitioner.splitTokenRange(concurrencyLevel);
        List<Callable<Boolean>> tasks = new ArrayList<>(concurrencyLevel);
        for (TokenRange token : tokens)
        {
            tasks.add(createLoadTaskInRange(ctx, token, callback));
        }
        try
        {
            ExecutorService localExecutor = Executors.newFixedThreadPool(concurrencyLevel,
                    new ThreadFactoryBuilder().setDaemon(true)
                            .setNameFormat("AllRowCqlReaderExecutor-%d")
                            .build());
            try
            {
                List<Future<Boolean>> futures = localExecutor.invokeAll(tasks);
                waitForTasksToFinish(futures);
            }
            finally
            {
                localExecutor.shutdownNow();
            }
        }
        catch (Exception e)
        {
            log.error("failed to load a table {}", tableName, e);
        }
    }
    private void waitForTasksToFinish(List<Future<Boolean>> futures) throws Exception
    {
        for (Future<Boolean> future : futures)
        {
            future.get();
        }
    }
    private TokenPartitioner findTokenPartitioner()
    {
        String partitioner = cluster.getMetadata().getPartitioner();
        TokenPartitioner found = partitionerMap.get(partitioner);
        if (found == null)
        {
            throw new IllegalArgumentException("Not supported partitioner: " + partitioner);
        }
        return found;
    }
    private Callable<Boolean> createLoadTaskInRange(TokenRange token,
                                                    Function<List<T>, Boolean> callback)
    {
        return () ->
        {
            try
            {
                StringBuilder sb = new StringBuilder();
                sb.append("token(");
                sb.append(String.join(",", partitionKeyNames));
                sb.append(")");
                String tokenOfKey = sb.toString();
                BigInteger beginTokenB = token.getBeginToken();
                BigInteger endTokenB = token.getEndToken();
                Statement statement = QueryBuilder.select()
                        .all()
                        .from(tableName)
                        .where(QueryBuilder.gte(tokenOfKey, beginTokenB.longValue()))
                        .and(QueryBuilder.lte(tokenOfKey, endTokenB.longValue()))
                        .setFetchSize(pageSize);
                MappingManager mappingManager = new MappingManager(session);
                ResultSet rs = session.execute(statement);
                Result<T> mappedResultSet = mappingManager.mapper(klass).map(rs);
                List<T> rows = new ArrayList<>(pageSize);
                while (mappedResultSet.iterator().hasNext())
                {
                    rows.add(mappedResultSet.iterator().next());
                    if (rows.size() >= pageSize)
                    {
                        callback.apply(rows);
                        rows = new ArrayList<>(pageSize);
                    }
                }
                if (rows.size() > 0)
                {
                    callback.apply(rows);
                }
                return true;
            }
            catch (Exception e)
            {
                log.error("failed to load rows in range: {} - {}", token.getBeginToken().toString(), token.getEndToken().toString(), e);
            }
            return false;
        };
    }
}
```