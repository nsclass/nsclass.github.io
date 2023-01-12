---
layout: single
title: Java - Gradle detecting JDK version
date: 2023-01-12 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - web
permalink: "2023/01/12/java-gradle-detect-jdk"
---

We can control gradle auto detecting JDK and auto download options as shown in below.

```
org.gradle.java.installations.auto-detect=false
org.gradle.java.installations.auto-download=false
org.gradle.java.installations.fromEnv=ENV_VALUE
```

```gradle
java {
  toolChain {
    languageVersion = JavaLanguageVersion.of(19)
  }
}

dependencies {
  testImplementation libs.junit.platform
}

tasks.withType(Test).configureEach {
  useJUnitPlatform()
  jvmArgs['--enable-preview']
}

tasks.withType(JavaCompile).configureEach {
  useJUnitPlatform()
  options.compileArgs.add('--enable--preview')
}

```
