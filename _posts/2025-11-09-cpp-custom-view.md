---
layout: single
title: How neural network works
date: 2025-11-09 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - ai
permalink: "2025/11/09/cpp-custom-view"
---

The following youtube shows a good explanation how we can define the custom view for ranges

[Advanced Ranges - Writing Modular, Clean, and Efficient Code with Custom Views - Steve Sorkin](https://www.youtube.com/watch?v=5iXUCcFP6H4&list=PL_AKIMJc4roW7umwjjd9Td-rtoqkiyqFl&index=28)

# Custom Ranges View Example in C++ (C++20)

This example demonstrates how to create a **custom range view** in modern C++ using templates and the `std::ranges` library.

---

## 🎯 Goal

We'll create a **`even_filter_view`** — a simple custom view that wraps another range and yields **only even numbers**.

---

## ✅ Complete Example

```cpp
#include <ranges>
#include <iostream>
#include <vector>
#include <concepts>

// 1️⃣ Define the view type
template <std::ranges::view V>
requires std::integral<std::ranges::range_value_t<V>>
class even_filter_view : public std::ranges::view_interface<even_filter_view<V>> {
private:
    V base_; // underlying range

    // Define an iterator for the view
    class iterator {
        using base_iterator = std::ranges::iterator_t<V>;
        base_iterator current_;
        base_iterator end_;

        void satisfy_predicate() {
            while (current_ != end_ && *current_ % 2 != 0)
                ++current_;
        }

    public:
        using value_type = std::ranges::range_value_t<V>;
        using difference_type = std::ptrdiff_t;
        using iterator_category = std::forward_iterator_tag;

        iterator() = default;
        iterator(base_iterator current, base_iterator end)
            : current_(current), end_(end) {
            satisfy_predicate();
        }

        value_type operator*() const { return *current_; }

        iterator& operator++() {
            ++current_;
            satisfy_predicate();
            return *this;
        }

        bool operator==(const iterator& other) const = default;
    };

public:
    even_filter_view() = default;
    explicit even_filter_view(V base) : base_(std::move(base)) {}

    auto begin() {
        return iterator(std::ranges::begin(base_), std::ranges::end(base_));
    }

    auto end() {
        return iterator(std::ranges::end(base_), std::ranges::end(base_));
    }

    V base() const { return base_; }
};

// 2️⃣ Deduction guide
template <class R>
even_filter_view(R&&) -> even_filter_view<std::views::all_t<R>>;

// 3️⃣ Helper factory function
struct even_filter_fn {
    template <std::ranges::viewable_range R>
    auto operator()(R&& r) const {
        return even_filter_view{std::views::all(std::forward<R>(r))};
    }
};

inline constexpr even_filter_fn even_filter;

// 4️⃣ Example usage
int main() {
    std::vector<int> nums = {1, 2, 3, 4, 5, 6, 7, 8};

    auto view = even_filter(nums); // our custom view
    // You can also combine it with standard views:
    // auto view = even_filter(nums) | std::views::take(2);

    for (int x : view)
        std::cout << x << " ";

    std::cout << "\n";
}
```

---

## 🧩 Explanation

- `std::ranges::view_interface` provides boilerplate for `.begin()`, `.end()`, `.empty()`, `.size()` etc.
- We define a **nested iterator** that skips odd numbers.
- The `even_filter_view` wraps any other range (like a `std::vector` or another view).
- The **helper object** `even_filter` makes it easier to compose with other views.

---

## 🧠 Example Output

```
2 4 6 8
```

---

## 💡 Combine with standard views

```cpp
for (int x : nums | even_filter | std::views::transform([](int n){ return n * n; }))
    std::cout << x << " ";
```

Output:

```
4 16 36 64
```
