---
layout: single
title: C++ 11 - Exception safe guidline from Jon Kalb
date: 2014-02-13 12:58:55.000000000 -06:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- C++
- Programming
tags:
- C++11
meta:
  _edit_last: '14827209'
  _publicize_pending: '1'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2014/02/13/c-11-exception-safe-guidline-from-jon-kalb/"
---

- Throw by value. Catch by reference
- No dynamic exception specifications. Use noexcept.
- Destructors that throw are evil.
- Use RAII. (Every responsibility is an object. One per.)
- All cleanup code called from a destructor
- Support swapperator (With No-Throw Guarantee)
- Draw “Critical Lines” for the Strong Guarantee
- Know where to catch (Switch/Strategy/Some Success)
- Prefer exceptions to error codes.

Where we should use "try, catch"

• Anywhere that we support the No-Throw Guarantee\
• Destructors & Cleanup\
• Swapperator & Moves\
• C-API\
• OS Callbacks\
• UI Reporting\
• Converting to other exception types\
• Threads

And extra places\
•Switch\
•Strategy\
•Some Success
