---
layout: single
title: C++ custom view for ranges
date: 2025-11-09 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2025/11/09/cpp-custom-view"
---

The following youtube shows a good explanation how we can define the custom view for ranges

[Advanced Ranges - Writing Modular, Clean, and Efficient Code with Custom Views - Steve Sorkin](https://www.youtube.com/watch?v=5iXUCcFP6H4&list=PL_AKIMJc4roW7umwjjd9Td-rtoqkiyqFl&index=28)

# Custom C++23 Range Adaptor Closure Example

This example demonstrates how to implement a **custom C++23 range adaptor** (a pipeable custom view) using `std::ranges::views::adaptor_closure`.

---

## 🎯 Goal

We’ll implement a **`even_filter_view`** — a view that filters out odd numbers — and make it **pipeable** like standard adaptors (`std::views::filter`, `std::views::transform`, etc.).

---

## ✅ Full Example

```cpp
#include <ranges>
#include <iostream>
#include <vector>
#include <concepts>

// 1️⃣ Define the custom view
template <std::ranges::view V>
requires std::integral<std::ranges::range_value_t<V>>
class even_filter_view : public std::ranges::view_interface<even_filter_view<V>> {
private:
    V base_; // underlying view

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

        bool operator==(const iterator&) const = default;
    };

public:
    even_filter_view() = default;
    explicit even_filter_view(V base) : base_(std::move(base)) {}

    auto begin() { return iterator(std::ranges::begin(base_), std::ranges::end(base_)); }
    auto end() { return iterator(std::ranges::end(base_), std::ranges::end(base_)); }

    V base() const { return base_; }
};

// Deduction guide
template <class R>
even_filter_view(R&&) -> even_filter_view<std::views::all_t<R>>;

// 2️⃣ Range adaptor closure definition (C++23 way!)
namespace views {
    inline constexpr auto even_filter = std::ranges::views::adaptor_closure([](auto&& r) {
        return even_filter_view(std::views::all(std::forward<decltype(r)>(r)));
    });
}

// 3️⃣ Example usage
int main() {
    std::vector<int> nums = {1, 2, 3, 4, 5, 6, 7, 8};

    // ✅ Using C++23 pipe syntax directly
    for (int x : nums | views::even_filter)
        std::cout << x << " ";

    std::cout << "\n";

    // ✅ Combine with standard views
    for (int x : nums | views::even_filter | std::views::transform([](int n) { return n * n; }))
        std::cout << x << " ";
    std::cout << "\n";
}
```

---

## 🧠 Output

```
2 4 6 8
4 16 36 64
```

---

## 🔍 What’s new in C++23

C++23 introduces **range adaptor closures** using:

```cpp
std::ranges::views::adaptor_closure
```

This makes custom views behave like standard adaptors — **pipeable**, **composable**, and **constexpr-friendly**.

### Advantages

✅ Natural pipe syntax (`nums | views::even_filter`)  
✅ Composable with standard adaptors  
✅ Less boilerplate, more expressive code  

---

## 🧩 TL;DR

| C++20 way | C++23 way |
|------------|------------|
| Define a struct with `operator()` | Use `std::ranges::views::adaptor_closure` |
| Not automatically pipeable | Fully pipeable |
| More boilerplate | Cleaner and composable |

---

### Example Composition

```cpp
auto result = nums 
    | views::even_filter 
    | std::views::transform([](int n) { return n * 10; })
    | std::views::take(3);
```