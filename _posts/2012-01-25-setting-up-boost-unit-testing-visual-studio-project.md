---
layout: single
title: Setting up boost unit testing visual studio project
date: 2012-01-25 10:08:31.000000000 -06:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- C++
- Programming
tags: []
meta:
  _edit_last: '14827209'
  tagazine-media: a:7:{s:7:"primary";s:0:"";s:6:"images";a:0:{}s:6:"videos";a:0:{}s:11:"image_count";s:1:"0";s:6:"author";s:8:"14827209";s:7:"blog_id";s:8:"14365184";s:9:"mod_stamp";s:19:"2012-01-24
    23:19:30";}
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2012/01/25/setting-up-boost-unit-testing-visual-studio-project/"
---

1\. Header\
```
#define BOOST_TEST_MODULE TestExample
#include
using namespace boost::unit_test;
``` 2. Linked library\
```
libboost_unit_test_framework-vc100-mt-sgd-1_46_1.lib
```

3\. Global fixture\
```
struct TestGlobalInitFixture
{
	TestGlobalInitFixture()
	{
		BOOST_TEST_MESSAGE("### Global initialization for testing ###");
	}
	~TestGlobalInitFixture()
	{
		BOOST_TEST_MESSAGE("### Global deinitialization for testing ###");
	}
};
BOOST_GLOBAL_FIXTURE(TestGlobalInitFixture);
```

4\. Fixture\
```
struct BuisnessLogicTestSuiteFixture
{
	BuisnessLogicTestSuiteFixture()
	{
	}
	~BuisnessLogicTestSuiteFixture()
	{
	}
};
BOOST_FIXTURE_TEST_SUITE(TestSuite_BusinessLogic, BuisnessLogicTestSuiteFixture)
```

5\. Test case example\
```
BOOST_AUTO_TEST_CASE(test_should_check_xxx)
{
}
``` 6. run a specific test case example

```
--run_test=*/test_should_check_xxx
```

7\. change log level\
```
--result_code=no --report_level=no
```
