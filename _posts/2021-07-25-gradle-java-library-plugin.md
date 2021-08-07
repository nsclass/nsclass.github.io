---
layout: single
title: Gradle - java-library plugin from 7.x version
date: 2021-07-25 07:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - gradle
permalink: "2021/07/25/gradle-java-library-plugin"
---

Gradle 7+ removed `compile` configuration so all existing gradle projects using `compile` configuration should be migrated.
Instead `java-library` plugin was introduced for the fine grained control of dependencies on compile classpath and runtime classpath.

`api` configuration will allow to have compile time classpath but `implementation` configuration will affect the dependency on runtime.
This fine grain control will allow us to prevent transitive dependency problem.

In order to have a clean packaging, project should use a new `maven-publish` plugin to publish a jar.
Prefer the `implementation` configuration over `api` when possible.

Adding `java-library` plugin

```groovy
apply plugin: 'java-library'
```

Github real world example.

[https://github.com/nsclass/ns-svg-converter/blob/master/build.gradle](https://github.com/nsclass/ns-svg-converter/blob/master/build.gradle)
[https://github.com/nsclass/ns-svg-converter/blob/master/ns-main-service/build.gradle](https://github.com/nsclass/ns-svg-converter/blob/master/ns-main-service/build.gradle)
[https://github.com/nsclass/ns-svg-converter/blob/master/ns-cassandra/build.gradle](https://github.com/nsclass/ns-svg-converter/blob/master/ns-cassandra/build.gradle)

The following Gradle(7.x) init project shows how it will generate multiple projects with `api` and `implementation`

[https://docs.gradle.org/current/samples/sample_building_java_applications_multi_project.html](https://docs.gradle.org/current/samples/sample_building_java_applications_multi_project.html)

Gradle documentation

[https://docs.gradle.org/current/userguide/java_library_plugin.html](https://docs.gradle.org/current/userguide/java_library_plugin.html)

The following article explains how `api` and `implementation` will handle compile/runtime classpath for gradle project.

[https://tomgregory.com/how-to-use-gradle-api-vs-implementation-dependencies-with-the-java-library-plugin/](https://tomgregory.com/how-to-use-gradle-api-vs-implementation-dependencies-with-the-java-library-plugin/)
