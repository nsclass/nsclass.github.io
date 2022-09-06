---
layout: single
title: Spring boot - Exception handling
date: 2022-09-06 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - stringboot
permalink: "2022/09/06/spring-boot-exception-handling"
---

SpringBoot allow to define the exception handler inside of Controller.

```java
@Controller
@ResponseBody
public class RestController {

  @ExceptionHandler
  @ResponseStatus(HttpStatus.BAD_REQUEST)
  public ResponseEntity<?> exceptionHandler(Exception e) {
    return ResponseEntity.badRequest().build()
  }

  @GetMapping("/hello/{name}")
  public Mono<Item> hello(@PathVariable String name) {
    return Mono.just(new Item(name));
  }

  @GetMapping(value = "/stream/{name}", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
  public Flux<Item> Flux.fromStream(stream.generate(() -> new Item(name)))
                          .take(10)
                          .delayElements(Duration.ofSeconds(1));
}

record Item(String name) {}
```
