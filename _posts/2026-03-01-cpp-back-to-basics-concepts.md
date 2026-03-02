---
layout: single
title: "C++ - Back to Basics: C++ Concepts"
date: 2026-03-01 10:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - concepts
permalink: "2026/03/01/cpp-back-to-basics-concepts"
---
[Jeff Garland - Back to Basics: C++ Concepts - CppCon 2025](https://www.youtube.com/watch?v=NpuNUGifL1M)

In this session from CppCon 2025, Jeff Garland presents a practitioner's guide to **C++20 Concepts**. The talk covers what concepts are, how to use them in code, reading and writing requires expressions and clauses, and designing with concepts.

## Concept Basics

### Why Do We Want Concepts?

- Write good generic libraries that are fast
- Get reasonable error messages
- Create code that programmers can understand and maintain
- Build better interfaces that are more descriptive with better dependency management

### What is a C++ Concept?

Concepts are **boolean predicate compositions** that:
- Support complex compile-time logic composition (conjunction and disjunction)
- Classify types into sets that share syntax/semantics
- Only check syntax (though semantics is the desired goal)

### Types vs Concepts

| Type | Concept |
|------|---------|
| Describes operations that can be performed | Describes how a type can be used |
| Relationships with other types (base class, dependent type) | Operations it can perform |
| Describes a memory layout | Relationships with other types |

### Simple One Parameter Concept: `printable`

```cpp
namespace io {
// Type T has print( std::ostream& ) const member function
template<class T>
concept printable = requires(std::ostream& os, T v)
{
    v.print( os ); // An expression that if compiles yields true
};
}
```

### Notable Concept Properties

- Evaluated completely at compile time (no runtime footprint)
- Compatible with high performance code
- Can be scoped in namespaces
- Bridge between 'pure auto' and a specific type
- Core use case is constraining templates

## Using Concepts in Code

### What Concepts Can Do

- Constrain an overload set
- Initialize a variable with `<concept_name> auto`
- Conditional compilation with `constexpr if`
- Use a pointer or `unique_ptr` of concept
- Partially specialize a template with concept
- Make template code into 'regular code'

### What Concepts Cannot Do

- Cannot inherit from concept
- Cannot constrain a concrete type using requires
- Cannot 'allocate' via new
- Cannot apply requires to virtual function

### Where Can We Write `<concept_name> auto`?

Where a type name might otherwise appear:
- Variable declaration
- Function parameter
- Function return type
- Class template member (if template argument)

But **not**:
- Class member
- Base class
- Template parameter and aliases (no auto)

### Concept Usage: Basic Examples

```cpp
template<class T>
concept printable = requires(std::ostream& os, T v)
{
    v.print( os ); // An expression that if compiles yields true
};

void f(printable auto s) { /* ... */ }

int main() {
    printable auto s = init_something();  // Must be initialized!
}
```

> **Note:** `printable auto s;` without initialization is a compile error.

### Concept Usage: Function Parameter or Return Value

```cpp
template<printable T>
printable auto
print( const T& s )
{
    //...
    return s;
}

printable auto
print2( const printable auto& s )
{
    //...
    return s;
}
```
[godbolt](https://godbolt.org/z/r3dY3dsvd)

### Unconstrained Auto for Function Parameter

```cpp
// auto parameter -- this is a template function!
// template<typename T>
// void print_ln( T p )
void print_ln( auto p )
{
    std::cout << p << "\n";
}

class my_type {};

int main()
{
    print_ln( "foo" );
    print_ln( 100 );
    my_type m;
    print_ln( m );  // Compile error - no operator<< for my_type
}
```
[godbolt](https://godbolt.org/z/GKq8ns)

### Concrete Overload for `my_type`

```cpp
void print_ln( auto p )
{
    std::cout << p << "\n";
}

// Selected ahead of print_ln(auto) because better match
void print_ln( my_type p )
{
    p.print( std::cout );
    std::cout << "\n";
}

int main()
{
    print_ln( "foo" );
    print_ln( 100 );
    my_type m;
    print_ln( m );  // Now works!
}
```
[godbolt](https://godbolt.org/z/85cEdqMEc)

### Concepts `printable` and `output_streamable`

```cpp
// Type T has print( std::ostream& ) member function
template<typename T>
concept printable = requires(std::ostream& os, T v)
{
    v.print( os );
};

template<typename T>
concept output_streamable = requires(std::ostream& os, T v)
{
    os << v;
};
```
[godbolt](https://godbolt.org/z/dYdhW7)

### A Type Satisfying `printable`

```cpp
class my_type
{
    int i = 1;
    std::string s = "foo\n";
public:  // Concept not satisfied if print isn't public!
    void print( std::ostream& os ) const
    {
        os << "i: " << i << " s: " << s;
    }
};

static_assert( printable<my_type> );
```
[godbolt](https://godbolt.org/z/dYdhW7)

### Constrained Overload for `print_ln`

```cpp
void print_ln( auto p )
{
    std::cout << p << "\n";
}

// Constrained resolution
void print_ln( printable auto p )
{
    p.print( std::cout );
    std::cout << "\n";
}
```
[godbolt](https://godbolt.org/z/36cdsGzzo)

### Overloaded Functions with Concepts

```cpp
// Example of overload resolution
void print_ln( output_streamable auto p )
{
    std::cout << p << "\n";
}

void print_ln( printable auto p )
{
    p.print( std::cout );
    std::cout << "\n";
}

int main()
{
    print_ln( "foo" );   // Uses output_streamable version
    my_type m;
    print_ln( m );       // Uses printable version
}
```
[godbolt](https://godbolt.org/z/dYdhW7)

### Pointers and Concepts

Useful for factory functions:

```cpp
int main()
{
    const printable auto* m = new my_type();
    m->print(std::cout);

    const std::unique_ptr<printable auto> upm = std::make_unique<my_type>();
    upm->print(std::cout);
}
// Output:
// s: foo
// s: foo
```
[godbolt](https://godbolt.org/z/d7bGhn)

### Pointer to Concept - Compile Error

```cpp
class whatever {};  // No print method

int main()
{
    printable auto* m = new whatever();  // Compile error!
}

// Error: deduced initializer does not satisfy placeholder constraints
// Note: constraints not satisfied
// Note: the required expression 'v.print(os)' is invalid
```

### Using `if constexpr` with Concepts

```cpp
template<class T>
std::ostream&
print_ln( std::ostream& os, const T& v )
{
    if constexpr ( printable<T> )
    {
        v.print(os);
    }
    else {
        os << v;
    }
    os << "\n";
    return os;
}

int main()
{
    my_type m;
    print_ln( std::cout, m );  // Uses print()
    int i = 100;
    print_ln( std::cout, i );  // Uses operator<<
}
```
[godbolt](https://godbolt.org/z/nsojqK5e1)

### `if constexpr` with Inline Requires Expression

```cpp
template<class T>
std::ostream&
print_ln( std::ostream& os, const T& v )
{
    if constexpr ( requires{ v.print( os ); } )
    {
        v.print(os);
    }
    else {
        os << v;
    }
    os << "\n";
    return os;
}
```
[godbolt](https://godbolt.org/z/nsojqK5e1)

### Non-Template Member Function of Template Class

```cpp
template<typename T>
class wrapper {
    T val_;
public:
    wrapper(T val) : val_(val) {}

    T operator*() requires std::is_pointer_v<T>  // Type trait constraint
    {
        return val_;
    }
};

int main()
{
    int i = 1;
    wrapper<int*> wi{&i};
    std::cout << *wi << std::endl;  // OK

    // wrapper<int> wi2{i};
    // std::cout << *wi2 << std::endl;  // Error: no match for operator*
}
```

### Template Alias with Concept Shorthand

```cpp
// Template alias using concepts
// All elements must satisfy concept printable
template<printable T>
using vec_of_printable = std::vector<T>;

int main()
{
    vec_of_printable<my_type> vp{ {}, {} };
    for ( const auto& e : vp )
    {
        e.print(std::cout);
    }
}
```

### Template Alias Error Message

```cpp
vec_of_printable<int> vp;  // Compile error!

// Error: template constraint failure for
//   'template<class T> requires printable<T> using vec_of_printable = std::vector<T>'
// Note: constraints not satisfied
// Note: the required expression 'v.print(os)' is invalid
```

## Standard Library Concepts

Standard concepts are found in headers `<concepts>`, `<type_traits>`, `<iterator>`, and `<ranges>`.

### Numeric Concepts

| Concept | Description |
|---------|-------------|
| `floating_point<T>` | float, double, long double |
| `integral<T>` | char, int, unsigned int, bool |
| `signed_integral<T>` | char, int |
| `unsigned_integral<T>` | char, unsigned |

### Comparison Concepts

| Concept | Description |
|---------|-------------|
| `equality_comparable<T>` | operator== is an equivalence |
| `equality_comparable_with<T,U>` | cross-type equality |
| `totally_ordered<T>` | ==, !=, <, >, <=, >= are a total ordering |
| `totally_ordered_with<T,U>` | cross-type total ordering |

### Object Relation Concepts

| Concept | Description |
|---------|-------------|
| `same_as<T,U>` | types are same |
| `derived_from<T,U>` | T is subclass of U |
| `convertible_to<T,U>` | T converts to U |
| `assignable_from<T,U>` | T can assign from U |

### Object Construction Concepts

| Concept | Description |
|---------|-------------|
| `default_initializable<T>` | default construction provided |
| `constructible_from<T,...>` | T can construct from variable pack |
| `move_constructible<T>` | support move |
| `copy_constructible<T>` | support move and copy |

### Regular and Semi-Regular Concepts

| Concept | Description |
|---------|-------------|
| `semiregular<T>` | copy, move, destruct, default construct |
| `regular<T>` | semiregular and equality comparable |

> See Sean Parent talks on why `regular` is so useful. TL;DR - type corresponds to usual expectations (like `int`).

### Enforcing Regularity

```cpp
#include <string>
#include <concepts>

class my_type
{
    std::string s = "foo\n";
public:
    void print( std::ostream& os ) const
    {
        os << "s: " << s;
    }
};

static_assert( std::regular<my_type> );  // Fails!
```

### Enforcing Regular Error

```text
error: static assertion failed
note: constraints not satisfied
note: required for the satisfaction of 'equality_comparable<_Tp>' [with _Tp = my_type]
```

### Enforcing Regular Fix

```cpp
class my_type
{
    std::string s = "foo\n";
public:
    void print( std::ostream& os ) const
    {
        os << "s: " << s;
    }
    // Added this line
    bool operator==( const my_type& ) const = default;
};

static_assert( std::regular<my_type> );  // Now passes!
```

### Using Range Concepts

```cpp
void print_ints( const std::ranges::range auto& R )
{
    for ( auto i : R )
    {
        std::cout << i << std::endl;
    }
}

// This function works on all the types below
int main()
{
    std::vector<int> vi = { 1, 2, 3, 4, 5 };
    print_ints( vi );

    std::array<int, 5> ai = { 1, 2, 3, 4, 5 };
    print_ints( ai );

    std::span<int> si2( ai );
    print_ints( si2 );

    int cai[] = { 1, 2, 3, 4, 5 };
    std::span<int> si3( cai );
    print_ints( si3 );

    std::ranges::iota_view iv{1, 6};
    print_ints( iv );
}
```
[godbolt](https://godbolt.org/z/53qzE35M5)

## Reading & Writing Concepts

### Requires Expression vs Requires Clause

- **Clause**: A boolean expression used after template and method declarations. Clauses can contain expressions.
- **Expression**: Syntax for describing type constraints.

### Requires Expression Basics

```cpp
requires { requirement-sequence }
requires ( ..parameters.. ) { requirement-sequence }

// Simplest possible boolean example - no parameters
template<typename T>
concept always = true;
```

### Requires Expression: Realistic Example

```cpp
// Type T has print( std::ostream& ) member function
template<typename T>
concept printable = requires(std::ostream& os, T v)
{
    // This is a conjunction (AND) --> all must be true
    v.print( os );           // Member function
    format( v );             // Free function
    std::movable<T>;         // Another concept
    typename T::format;      // Nested type requirement
};

template<class T>
concept output_streamable = requires(std::ostream& os, T v)
{
    // Compound requirement: constraint on return type
    { os << v } -> std::same_as<std::ostream&>;
};
```

### Constraint Composition

```cpp
// Disjunction (OR)
template<typename T>
concept printable_or_streamable =
    printable<T> || output_streamable<T>;

// Same as above using 'or' keyword
template<typename T>
concept printable_or_streamable2 =
    printable<T> or output_streamable<T>;

// Conjunction (AND)
template<typename T>
concept fully_outputable =
    printable<T> and output_streamable<T>;
```

### More Constraint Composition

```cpp
template<typename T>
concept printable = requires(std::ostream& os, T v)
{
    v.print( os );
    std::movable<T>;
    typename T::format;
};

// Equivalent formulation
template<typename T>
concept printable2 =
    std::movable<T> and
    requires(std::ostream& os, T v)
    {
        v.print( os );
        typename T::format;
    };
```

### Standard Library Example: `derived_from`

```cpp
template<class Derived, class Base>
concept derived_from =
    std::is_base_of_v<Base, Derived> and
    std::is_convertible_v<const volatile Derived*, const volatile Base*>;
```

### Example Concept: `number`

```cpp
#include <concepts>

template<typename T, typename U>
concept not_same_as = not std::is_same_v<T, U>;

static_assert( not_same_as<int, double> );

template<typename T>
concept number =
    not_same_as<bool, T> and
    not_same_as<char, T> and
    std::is_arithmetic_v<T>;

static_assert( number<int> );
static_assert( number<double> );
static_assert( !number<bool> );
```

> Note: `is_arithmetic` is a trait that includes char and bool, which we often don't want in a "number" concept.

### Ranges and Concepts

```cpp
std::vector<int> vi{ 0, 1, 2, 3, 4, 5, 6 };
auto is_even = [](int i) { return 0 == i % 2; };

for (int i : std::ranges::filter_view( vi, is_even ))
{
    std::cout << i << " ";  // Output: 0 2 4 6
}
```

### `std::ranges::filter_view` Declaration

```cpp
template<std::ranges::input_range V,
         std::indirect_unary_predicate<std::ranges::iterator_t<V>> Pred>
    requires std::ranges::view<V> && std::is_object_v<Pred>
class filter_view : public view_interface<filter_view<V, Pred>> { /* ... */ };
```

### `std::ranges::view_interface`

```cpp
template<class D>
    requires std::is_class_v<D> && std::same_as<D, std::remove_cv_t<D>>
class view_interface
{
    constexpr const D& derived() const noexcept
    {
        return static_cast<const D&>(*this);
    }

    // Concept-based specialization of operator[]
    // Only applies if subclass is random_access_range
    template<std::ranges::random_access_range R = const D>
    constexpr decltype(auto) operator[](std::ranges::range_difference_t<R> n) const
    {
        return std::ranges::begin(derived())[n];
    }
};
```

## Designing with Concepts

### Concepts and Dependencies

- Move dependency from a concrete type to an abstraction
- Simple to test that a type models a concept
- Trade-offs:
  - Type may evolve to no longer model concept (working code fails)
  - Concept may evolve so type no longer models it (working code fails)

### Code Readability and Evolution

```cpp
auto result = some_function();            // Return type unknown, flexible
int result = some_function();             // Return type obvious, brittle
time_duration auto result = some_function();  // Flexible + clear
```

### Type, auto, or `<concept_name> auto`

| Approach | Characteristics |
|----------|-----------------|
| Concrete type | Only one type can be returned; inflexible if return type evolves |
| `auto` | We don't care/know the type; still need recompile on change |
| `<concept_name> auto` | A set of types; good sweet spot; allows bounded evolution |

### Breaking the Grip of Type Dependency

```cpp
// This function works on all the types below
void print_ints( const std::ranges::range auto& R )
{
    for ( auto i : R )
    {
        std::cout << i << std::endl;
    }
}

int main()
{
    std::vector<int> vi = { 1, 2, 3, 4, 5 };
    print_ints( vi );

    std::array<int, 5> ai = { 1, 2, 3, 4, 5 };
    print_ints( ai );

    std::span<int> si2( ai );
    print_ints( si2 );

    int cai[] = { 1, 2, 3, 4, 5 };
    std::span<int> si3( cai );
    print_ints( si3 );

    std::ranges::iota_view iv{1, 6};
    print_ints( iv );
}
```
[godbolt](https://godbolt.org/z/53qzE35M5)

## Final Thoughts

- Concepts are a powerful tool in C++20
- Practical and easy to use
- Alter designs in important ways
- Integrated into many aspects of the standard library

### Additional Resources

- [C++Now 2021 - Part 1](https://www.youtube.com/watch?v=Ffu9C1BZ4-c)
- [C++Now 2021 - Part 2](https://www.youtube.com/watch?v=IXbf5lxGtr0)
