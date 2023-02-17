---
layout: single
title: Spring Data - How interface class is working
date: 2023-02-17 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - spring
permalink: "2023/02/17/spring-data-interface-classes"
---

Spring data is using a proxy pattern to implement the interface only class at runtime. The following example will show how it will override `findById` function at runtime.

```java
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.repository.core.support.RepositoryFactorySupport;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;

public class ExampleDynamicProxy {

    public static void main(String[] args) {
        RepositoryFactorySupport factory = new RepositoryFactorySupport() {
            @Override
            public <T> T getRepository(Class<T> repositoryInterface) {
                InvocationHandler handler = new JpaRepositoryInvocationHandler(repositoryInterface);
                return (T) Proxy.newProxyInstance(getClass().getClassLoader(), new Class[]{repositoryInterface}, handler);
            }
        };

        ExampleRepository exampleRepository = factory.getRepository(ExampleRepository.class);
        ExampleEntity entity = new ExampleEntity();
        entity.setId(1L);
        entity.setName("example");
        exampleRepository.save(entity);

        ExampleEntity retrievedEntity = exampleRepository.findById(1L).orElseThrow();
        System.out.println(retrievedEntity.getName());
    }

    private interface ExampleRepository extends JpaRepository<ExampleEntity, Long> {
    }

    private static class ExampleEntity {
        private Long id;
        private String name;

        public Long getId() {
            return id;
        }

        public void setId(Long id) {
            this.id = id;
        }

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }
    }

    private static class JpaRepositoryInvocationHandler implements InvocationHandler {

        private final Class<?> repositoryInterface;

        JpaRepositoryInvocationHandler(Class<?> repositoryInterface) {
            this.repositoryInterface = repositoryInterface;
        }

        @Override
        public Object invoke(Object proxy, Method method, Object[] args) {
            if (method.getName().startsWith("find")) {
                System.out.println("Executing query: " + method.getName());
                // return some dummy data
                return new ExampleEntity();
            } else {
                throw new UnsupportedOperationException("Method " + method.getName() + " not implemented");
            }
        }
    }
}
```