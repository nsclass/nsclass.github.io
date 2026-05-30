---
layout: single
title: Monoid - Simple definition of Monoid
date: 2017-09-04 07:07:51.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Functional Programming
- Programming
tags: []
meta:
  _edit_last: '14827209'
  geo_public: '0'
  _publicize_job_id: '8922095693'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2017/09/04/monoid-simple-definition-of-monoid/"
---

1\. Closure: Two same type pair operation results a new result with same type.\
2. Associative: Doesn't matter or operation order wit a pair.\
3. Identity: There is an identity can always result the original value.

Integer plus:\
```
1 + 2 = 3
(1 + 2) + 3 = 1 + (2 + 3)
1 + 0 = 1
0 + 1 = 1
```

String concatenation:\
```
"1" + "2" = "12"
"1" + ("2" + "3") = ("1" + "2") + "3"
"" + "1" = "1"
"1" + "" = "1"
```

Importance of Monoids:\
Once it is identified that provided data is Monoid, it can be parallelized very easily.\
For instance, we can calculate the number of total sold items in a day from million items.

Map/Reduce\
```
List.reduce(+)
```

Log file aggregation:\
From a giant log file, we can aggregate useful data such as what is the average request on Monday, Tuesday, ..., Sunday because String is Monoid.\
It is important to know that Metric data should be Monoid.
