---
layout: single
title: "C++ - Structured Concurrency with Facebook's Folly Library"
date: 2026-03-08 10:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - concurrency
permalink: "2026/03/08/cpp-folly-structured-concurrency"
---

This post demonstrates how [Facebook's Folly library](https://github.com/facebook/folly) supports **structured concurrency** through its coroutine-based `AsyncScope` primitive. The example implements a real-world financial news scraping pipeline with three stages, where each stage's lifetime is strictly bounded by the scope it was spawned in.

## What is Structured Concurrency?

Structured concurrency ensures that concurrent tasks follow a clear ownership hierarchy — no child task can outlive the scope that spawned it. This eliminates common concurrency bugs like dangling tasks, leaked resources, and race conditions on shutdown.

Folly provides this guarantee through `folly::coro::AsyncScope` and its `joinAsync()` method, which acts as a hard barrier: execution only continues after **every** task in the scope has completed.

## Pipeline Architecture

The example builds a three-stage financial news scraper:

```
  ┌─────────────────────────────────────────────────────────────────┐
  │  STAGE 1 – Scrape (IO thread pool, N concurrent HTTP tasks)     │
  │     site1 ──┐                                                   │
  │     site2 ──┼──► UnboundedQueue<RawArticle>  (lock-free MPSC)  │
  │     siteN ──┘                                                   │
  └──────────────────────────┬──────────────────────────────────────┘
                             │  articles flow in as they arrive
  ┌──────────────────────────▼──────────────────────────────────────┐
  │  STAGE 2 – Process (CPU thread pool, M worker coroutines)       │
  │     worker0 ──┐                                                 │
  │     worker1 ──┼──► ResultStore (lock-free push)                │
  │     workerM ──┘                                                 │
  └──────────────────────────┬──────────────────────────────────────┘
                             │  all records collected
  ┌──────────────────────────▼──────────────────────────────────────┐
  │  STAGE 3 – Persist  (single structured transaction, PostgreSQL)  │
  └─────────────────────────────────────────────────────────────────┘
```

**Structured-concurrency guarantees (via AsyncScope + joinAsync):**
- No scraper task outlives Stage 1's scope
- No worker task outlives Stage 2's scope
- DB write only starts after BOTH scopes have fully joined
- Sentinel value (`nullopt`) signals workers that producers are done

## Key Structured Concurrency Patterns in the Code

### 1. AsyncScope as a Task Nursery

Each stage uses its own `AsyncScope`, which acts like a "nursery" (a term from Python's Trio). Tasks are spawned into the scope via `add()`, and the scope guarantees all tasks complete before execution continues past `joinAsync()`:

```cpp
// STAGE 1 — Scrape all URLs concurrently on the IO thread pool
{
    folly::coro::AsyncScope scrape_scope;

    for (const auto& url : cfg.news_urls) {
        scrape_scope.add(
            scrape_one(url, cfg.http_timeout_secs, channel)
                .scheduleOn(io_exec)
        );
    }

    // Structured wait: all scrapers finish before we send sentinels
    co_await scrape_scope.joinAsync();
}
// ← Every scraper coroutine has completed here.
```

### 2. Executor Separation: IO vs CPU

Folly lets you pin tasks to specific executors — `IOThreadPoolExecutor` for network-bound work and `CPUThreadPoolExecutor` for CPU-intensive analysis:

```cpp
auto io_exec  = std::make_shared<folly::IOThreadPoolExecutor>(cfg.io_threads);
auto cpu_exec = std::make_shared<folly::CPUThreadPoolExecutor>(cfg.cpu_workers);
```

Tasks are scheduled on the appropriate executor via `.scheduleOn()`:

```cpp
// Scrapers run on IO threads (mostly blocked on network)
scrape_scope.add(
    scrape_one(url, cfg.http_timeout_secs, channel)
        .scheduleOn(io_exec)
);

// Analysis workers run on CPU threads (regex + sentiment analysis)
worker_scope.add(
    analysis_worker(w, channel, store, cfg.ticker, articles_processed)
        .scheduleOn(cpu_exec)
);
```

### 3. Back-Pressure via Bounded Queue

The `MPMCQueue` provides natural back-pressure. When all CPU workers are busy and the queue fills up, scraper tasks block inside `blockingWrite()` rather than accumulating unlimited articles in memory:

```cpp
ArticleChannel channel(cfg.queue_capacity);  // bounded MPMC queue

// In scraper: blocks if queue is full
channel.blockingWrite(std::move(art));

// In worker: blocks until an item arrives
channel.blockingRead(msg);
```

### 4. Clean Shutdown with Sentinels

After all scrapers complete (guaranteed by `joinAsync()`), sentinel values signal workers to exit:

```cpp
co_await scrape_scope.joinAsync();

// Send one sentinel per worker so each one exits cleanly
for (int w = 0; w < num_workers; ++w)
    channel.blockingWrite(std::nullopt);  // sentinel

co_await worker_scope.joinAsync();
// ← Every worker coroutine has completed here.
```

## Full Source Code

```cpp
{% raw %}
/**
 * Folly Structured Concurrency - Financial News Scraper (v2)
 *
 * Dependencies:
 *   folly, libcurl, libpqxx
 *
 * Build:
 *   g++ -std=c++20 -O2 folly_financial_scraper_v2.cpp \
 *       -lfolly -lglog -lgflags -lpthread -lcurl -lpqxx -lpq \
 *       -o financial_scraper
 */

// ── Folly coroutines ──────────────────────────────────────────────────────────
#include <folly/executors/CPUThreadPoolExecutor.h>
#include <folly/executors/IOThreadPoolExecutor.h>
#include <folly/experimental/coro/AsyncScope.h>
#include <folly/experimental/coro/BlockingWait.h>
#include <folly/experimental/coro/Collect.h>
#include <folly/experimental/coro/Task.h>
#include <folly/experimental/coro/BoundedQueue.h>

// ── Folly concurrency primitives ─────────────────────────────────────────────
#include <folly/MPMCQueue.h>
#include <folly/concurrency/UnboundedQueue.h>
#include <folly/AtomicHashMap.h>

// ── Third-party ───────────────────────────────────────────────────────────────
#include <curl/curl.h>
#include <pqxx/pqxx>

// ── Standard library ─────────────────────────────────────────────────────────
#include <algorithm>
#include <atomic>
#include <chrono>
#include <iostream>
#include <memory>
#include <mutex>
#include <optional>
#include <regex>
#include <string>
#include <thread>
#include <vector>

using namespace std::chrono_literals;

// =============================================================================
// Domain types
// =============================================================================

struct RawArticle {
    std::string source_url;
    std::string title;
    std::string body;
    std::string published_at;
};

struct FinancialRecord {
    std::string ticker;
    std::string source_url;
    std::string title;
    std::string snippet;
    std::string sentiment;
    std::string published_at;
};

// Sentinel: nullopt in the queue means "no more articles — workers should exit"
using ArticleMsg = std::optional<RawArticle>;

// =============================================================================
// Configuration
// =============================================================================

struct AppConfig {
    std::string ticker          = "AAPL";
    std::string pg_conn_string  = "host=localhost port=5432 dbname=finance "
                                  "user=postgres password=secret";
    std::vector<std::string> news_urls;

    int http_timeout_secs       = 10;

    // IO pool: larger — curl threads block on network, not CPU
    int io_threads              = 12;
    // CPU pool: number of parallel analysis workers
    int cpu_workers             = static_cast<int>(
                                      std::thread::hardware_concurrency());

    // How many articles may sit in the queue before scrapers apply back-pressure
    size_t queue_capacity       = 256;
};

// =============================================================================
// HTTP helper  (synchronous libcurl, meant to run on an IO thread)
// =============================================================================

namespace http {

struct Response { long status_code = 0; std::string body, error; };

static size_t write_cb(char* p, size_t sz, size_t n, void* ud) {
    static_cast<std::string*>(ud)->append(p, sz * n);
    return sz * n;
}

Response get(const std::string& url, int timeout_secs) {
    Response r;
    CURL* c = curl_easy_init();
    if (!c) { r.error = "init failed"; return r; }
    curl_easy_setopt(c, CURLOPT_URL,           url.c_str());
    curl_easy_setopt(c, CURLOPT_WRITEFUNCTION, write_cb);
    curl_easy_setopt(c, CURLOPT_WRITEDATA,     &r.body);
    curl_easy_setopt(c, CURLOPT_TIMEOUT,       (long)timeout_secs);
    curl_easy_setopt(c, CURLOPT_FOLLOWLOCATION,1L);
    curl_easy_setopt(c, CURLOPT_USERAGENT,     "FollyFinBot/2.0");
    CURLcode rc = curl_easy_perform(c);
    if (rc != CURLE_OK) r.error = curl_easy_strerror(rc);
    else curl_easy_getinfo(c, CURLINFO_RESPONSE_CODE, &r.status_code);
    curl_easy_cleanup(c);
    return r;
}

} // namespace http

// =============================================================================
// HTML → plain text  (demo quality; swap for libxml2/Gumbo in production)
// =============================================================================

namespace html {

std::string to_text(const std::string& src) {
    static const std::regex tag_re  ("<[^>]+>",  std::regex::optimize);
    static const std::regex ws_re   ("\\s+",     std::regex::optimize);
    std::string t = std::regex_replace(src, tag_re, " ");
    auto repl = [](std::string s, std::string_view f, std::string_view r) {
        for (size_t p=0; (p=s.find(f,p))!=std::string::npos; p+=r.size())
            s.replace(p,f.size(),r);
        return s;
    };
    t = repl(t,"&amp;","&"); t = repl(t,"&lt;","<"); t = repl(t,"&gt;",">");
    t = repl(t,"&nbsp;"," "); t = repl(t,"&#39;","'"); t = repl(t,"&quot;","\"");
    return std::regex_replace(t, ws_re, " ");
}

std::string extract_title(const std::string& src) {
    static const std::regex re("<title[^>]*>([^<]*)</title>",
                               std::regex::icase | std::regex::optimize);
    std::smatch m;
    return std::regex_search(src, m, re) ? m[1].str() : "(no title)";
}

} // namespace html

// =============================================================================
// Financial extraction helpers
// =============================================================================

namespace finance {

std::regex make_ticker_pattern(const std::string& t) {
    return std::regex(
        R"((?:^|[\s\(\[\$,:]))" + t + R"((?=$|[\s\)\],\.;:]))",
        std::regex::optimize);
}

std::string classify_sentiment(const std::string& text) {
    static const char* POS[] = {
        "surge","gain","rally","growth","profit","beat","upgrade",
        "bullish","record","strong","outperform","rise","soar",nullptr};
    static const char* NEG[] = {
        "fall","drop","loss","miss","downgrade","bearish","decline",
        "weak","underperform","crash","sell","concern","risk",nullptr};
    std::string lo = text;
    std::transform(lo.begin(),lo.end(),lo.begin(),::tolower);
    int score = 0;
    for (int i=0; POS[i]; ++i) if (lo.find(POS[i])!=std::string::npos) ++score;
    for (int i=0; NEG[i]; ++i) if (lo.find(NEG[i])!=std::string::npos) --score;
    return score>0 ? "positive" : score<0 ? "negative" : "neutral";
}

std::string extract_snippet(const std::string& text, const std::regex& pat,
                             size_t ctx = 200) {
    std::smatch m;
    if (!std::regex_search(text,m,pat)) return {};
    size_t pos = (size_t)m.position();
    size_t lo  = pos > ctx ? pos-ctx : 0;
    size_t hi  = std::min(pos+ctx, text.size());
    return "..." + text.substr(lo, hi-lo) + "...";
}

} // namespace finance

// =============================================================================
// Lock-free result accumulator
// =============================================================================

class ResultStore {
public:
    void push(FinancialRecord r) {
        queue_.enqueue(std::move(r));
        count_.fetch_add(1, std::memory_order_relaxed);
    }

    std::vector<FinancialRecord> drain() {
        std::vector<FinancialRecord> out;
        out.reserve(count_.load(std::memory_order_relaxed));
        FinancialRecord r;
        while (queue_.try_dequeue(r))
            out.push_back(std::move(r));
        return out;
    }

    size_t size() const { return count_.load(std::memory_order_relaxed); }

private:
    folly::UnboundedQueue<FinancialRecord,
        /*SingleProducer=*/false,
        /*SingleConsumer=*/true,
        /*MayBlock=*/false>  queue_;
    std::atomic<size_t> count_{0};
};

// =============================================================================
// Article channel  (bounded MPMC — provides back-pressure)
// =============================================================================

using ArticleChannel = folly::MPMCQueue<ArticleMsg>;

// =============================================================================
// Stage 1 — Scraper coroutine  (one per URL, runs on IO thread pool)
// =============================================================================

folly::coro::Task<void>
scrape_one(std::string url,
           int timeout_secs,
           ArticleChannel& channel) {
    try {
        auto resp = http::get(url, timeout_secs);
        if (!resp.error.empty() || resp.status_code != 200) {
            std::cerr << "[scrape] SKIP " << url
                      << " (status=" << resp.status_code
                      << " err=" << resp.error << ")\n";
            co_return;
        }

        RawArticle art;
        art.source_url   = url;
        art.title        = html::extract_title(resp.body);
        art.body         = html::to_text(resp.body);
        art.published_at = "";

        std::cout << "[scrape] OK  " << url
                  << "  (" << art.body.size() << " chars)\n";

        channel.blockingWrite(std::move(art));

    } catch (const std::exception& e) {
        std::cerr << "[scrape] EXCEPTION " << url << ": " << e.what() << "\n";
    }
    co_return;
}

// =============================================================================
// Stage 2 — Analysis worker coroutine  (M workers on CPU thread pool)
// =============================================================================

folly::coro::Task<void>
analysis_worker(int worker_id,
                ArticleChannel& channel,
                ResultStore& store,
                const std::string& ticker,
                std::atomic<uint64_t>& articles_processed) {

    const auto ticker_pat = finance::make_ticker_pattern(ticker);

    while (true) {
        ArticleMsg msg;
        channel.blockingRead(msg);

        if (!msg.has_value()) {
            std::cout << "[worker " << worker_id << "] received sentinel, exiting\n";
            co_return;
        }

        RawArticle& art = *msg;
        uint64_t seq = articles_processed.fetch_add(1, std::memory_order_relaxed);

        if (seq % 50 == 0)
            std::cout << "[worker " << worker_id
                      << "] processed " << seq << " articles so far\n";

        bool hit_title = std::regex_search(art.title, ticker_pat);
        bool hit_body  = std::regex_search(art.body,  ticker_pat);
        if (!hit_title && !hit_body) continue;

        FinancialRecord rec;
        rec.ticker       = ticker;
        rec.source_url   = art.source_url;
        rec.title        = art.title;
        rec.published_at = art.published_at;
        rec.snippet      = finance::extract_snippet(art.body, ticker_pat);
        rec.sentiment    = finance::classify_sentiment(art.title + " " + rec.snippet);

        std::cout << "[worker " << worker_id << "] HIT  "
                  << art.source_url << "  sentiment=" << rec.sentiment << "\n";

        store.push(std::move(rec));
    }
}

// =============================================================================
// Stage 3 — PostgreSQL persistence
// =============================================================================

namespace db {

void ensure_schema(pqxx::connection& conn) {
    pqxx::work tx(conn);
    tx.exec(R"sql(
        CREATE TABLE IF NOT EXISTS financial_news (
            id           BIGSERIAL    PRIMARY KEY,
            ticker       TEXT         NOT NULL,
            source_url   TEXT         NOT NULL,
            title        TEXT,
            snippet      TEXT,
            sentiment    TEXT,
            published_at TEXT,
            ingested_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            UNIQUE (ticker, source_url, title)
        );
        CREATE INDEX IF NOT EXISTS idx_fn_ticker ON financial_news(ticker);
    )sql");
    tx.commit();
    std::cout << "[db] Schema ready\n";
}

size_t insert_batch(pqxx::connection& conn,
                    const std::vector<FinancialRecord>& recs) {
    if (recs.empty()) return 0;
    pqxx::work tx(conn);
    size_t n = 0;
    for (const auto& r : recs) {
        auto res = tx.exec_params(R"sql(
            INSERT INTO financial_news
                (ticker, source_url, title, snippet, sentiment, published_at)
            VALUES ($1,$2,$3,$4,$5,$6)
            ON CONFLICT (ticker, source_url, title) DO NOTHING
            RETURNING id
        )sql",
        r.ticker, r.source_url, r.title,
        r.snippet, r.sentiment, r.published_at);
        if (!res.empty()) ++n;
    }
    tx.commit();
    return n;
}

} // namespace db

// =============================================================================
// Top-level pipeline coroutine
// =============================================================================

folly::coro::Task<void>
run_pipeline(const AppConfig& cfg,
             folly::Executor* io_exec,
             folly::Executor* cpu_exec) {

    ArticleChannel channel(cfg.queue_capacity);
    ResultStore store;
    std::atomic<uint64_t> articles_processed{0};
    const int num_workers = cfg.cpu_workers;

    // =========================================================================
    // STAGE 2 — Launch worker pool BEFORE scrapers start
    //           Workers block on the queue until articles arrive.
    // =========================================================================
    folly::coro::AsyncScope worker_scope;

    for (int w = 0; w < num_workers; ++w) {
        worker_scope.add(
            analysis_worker(w, channel, store, cfg.ticker, articles_processed)
                .scheduleOn(cpu_exec)
        );
    }

    std::cout << "[pipeline] Launched " << num_workers
              << " analysis workers on CPU pool\n";

    // =========================================================================
    // STAGE 1 — Scrape all URLs concurrently on the IO thread pool
    // =========================================================================
    {
        folly::coro::AsyncScope scrape_scope;

        for (const auto& url : cfg.news_urls) {
            scrape_scope.add(
                scrape_one(url, cfg.http_timeout_secs, channel)
                    .scheduleOn(io_exec)
            );
        }

        std::cout << "[pipeline] Scraping " << cfg.news_urls.size()
                  << " sources concurrently...\n";

        // Structured wait: all scrapers finish before we send sentinels
        co_await scrape_scope.joinAsync();

        std::cout << "[pipeline] All scrapers done. Sending "
                  << num_workers << " sentinels...\n";
    }
    // ← Every scraper coroutine has completed here.

    // Send one sentinel per worker so each one exits cleanly
    for (int w = 0; w < num_workers; ++w)
        channel.blockingWrite(std::nullopt);

    // =========================================================================
    // Wait for all workers to drain the queue and exit
    // =========================================================================
    co_await worker_scope.joinAsync();
    // ← Every worker coroutine has completed here.

    std::cout << "[pipeline] All workers done. Total articles processed: "
              << articles_processed.load() << "\n"
              << "[pipeline] Financial records matched: "
              << store.size() << "\n";

    // =========================================================================
    // STAGE 3 — Persist results to PostgreSQL
    // =========================================================================
    co_await folly::coro::co_invoke(
        [&cfg, &store]() -> folly::coro::Task<void> {
            auto records = store.drain();

            if (records.empty()) {
                std::cout << "[db] No matching records for "
                          << cfg.ticker << ".\n";
                co_return;
            }

            std::cout << "[db] Persisting " << records.size()
                      << " record(s) for " << cfg.ticker << "...\n";
            try {
                pqxx::connection conn(cfg.pg_conn_string);
                db::ensure_schema(conn);
                size_t n = db::insert_batch(conn, records);
                std::cout << "[db] Inserted " << n << " new row(s).\n";
            } catch (const std::exception& e) {
                std::cerr << "[db] ERROR: " << e.what() << "\n";
                throw;
            }
        }()
    ).scheduleOn(cpu_exec);
}

// =============================================================================
// main
// =============================================================================

int main(int argc, char** argv) {
    AppConfig cfg;
    cfg.ticker = (argc > 1) ? argv[1] : "AAPL";
    cfg.cpu_workers = std::max(1, (int)std::thread::hardware_concurrency());

    cfg.news_urls = {
        "https://finance.yahoo.com/news/",
        "https://www.reuters.com/finance/",
        "https://www.bloomberg.com/markets",
        "https://seekingalpha.com/market-news/",
        "https://www.marketwatch.com/latest-news",
        "https://www.cnbc.com/finance/",
        "https://www.ft.com/markets",
        "https://www.wsj.com/markets",
        "https://www.investing.com/news/stock-market-news",
        "https://finance.yahoo.com/quote/" + cfg.ticker + "/news/",
    };

    auto io_exec  = std::make_shared<folly::IOThreadPoolExecutor>(cfg.io_threads);
    auto cpu_exec = std::make_shared<folly::CPUThreadPoolExecutor>(cfg.cpu_workers);

    curl_global_init(CURL_GLOBAL_ALL);

    std::cout << "════════════════════════════════════════\n"
              << " Folly Financial Scraper  v2\n"
              << "════════════════════════════════════════\n"
              << " Ticker      : " << cfg.ticker        << "\n"
              << " Sources     : " << cfg.news_urls.size() << "\n"
              << " IO threads  : " << cfg.io_threads    << "\n"
              << " CPU workers : " << cfg.cpu_workers   << "\n"
              << " Queue cap   : " << cfg.queue_capacity << "\n"
              << "════════════════════════════════════════\n\n";

    try {
        folly::coro::blockingWait(
            run_pipeline(cfg, io_exec.get(), cpu_exec.get())
                .scheduleOn(io_exec.get())
        );
        std::cout << "\n✓ Pipeline complete.\n";
    } catch (const std::exception& e) {
        std::cerr << "✗ Fatal: " << e.what() << "\n";
        curl_global_cleanup();
        return 1;
    }

    curl_global_cleanup();
    return 0;
}
{% endraw %}
```

## Structured Lifetime Guarantees

The core structured concurrency contract in this pipeline:

```
scrape_scope.joinAsync()  → all scrapers done       → sentinels sent
worker_scope.joinAsync()  → all workers done        → store fully populated
db::insert_batch()        → write to PostgreSQL     → pipeline complete
```

No stage can observe a partially-completed earlier stage; every `joinAsync()` is a hard barrier enforced by the Folly `AsyncScope` destructor.

## Thread Utilization Strategy

| Pool | Threads | Work Type |
|------|---------|-----------|
| IO pool | 12 threads | Scraping: mostly blocked on network latency |
| CPU pool | N threads (= `hardware_concurrency`) | Analysis: regex + sentiment — always doing real CPU work |

Workers are launched **before** scrapers and immediately block on the queue. Scrapers are launched after. This means analysis begins the moment the first article lands in the queue — scraping and analysis overlap fully in time rather than running sequentially.

## Scaling Further

- Replace `MPMCQueue` with `folly::coro::BoundedQueue` for async back-pressure (avoids blocking IO threads when the CPU pool is saturated)
- Add a `CancellationSource` to enforce a wall-clock deadline on the whole run
- Partition `news_urls` by domain and run per-domain rate limiters (`folly::TokenBucketSemaphore`) to avoid IP bans
- For very large article corpora, replace in-process analysis with a work-stealing thread pool (`folly::FiberManager`) for finer-grained tasks
