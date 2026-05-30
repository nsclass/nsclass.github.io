---
layout: single
title: Monad - simple example definition
date: 2017-08-13 12:55:34.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories: []
tags: []
meta:
  _edit_last: '14827209'
  geo_public: '0'
  _publicize_job_id: '8210197506'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2017/08/13/monad-simple-example-definition/"
---

Combines the following concept.

1\. Functor\
- Type constructor.\
- Value lifting.\
- class Functor f where\
fmap :: (a -\> b) -\> (f a -\> f b)\
2. Bind\
- Create a functor then unwrap -\> for example, flatMap in optional in Java8.
