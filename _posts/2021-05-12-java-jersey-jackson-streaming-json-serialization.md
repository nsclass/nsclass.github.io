---
layout: single
title: Java - Jersey and Jackson for JSON serialization in streaming mode
date: 2021-05-12 17:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - java
permalink: "2021/05/12/jersey-jackson-json-streaming-serialization"
---
With Jersey and Jackson combination, we can build the streaming API for serializing very large size of data.

Please find the below pseudo code example.

```java
import javax.ws.rs.core.StreamingOutput;
import com.fasterxml.jackson.databind.ObjectMapper;


public class TestResource {

  private Iterator<Item> unknownLengthIterator;
  private ObjectMapper objectMapper;

  @GET
  @Produce(MediaType.APPLICATION_JSON)
  public Response getAllStream() {
    StreamingOutput streamingOutput = output -> {
      JsonFactory jsonFactory = objectMapper.getFactory();
      try (JsonGenerator jsonGenerator = jsonFactory.createGenerator(output)) {
        jsonGenerator.writeStartArray();
        unknownLengthIterator.forEach(item -> {
          try {
            jsonGenerator.writeObject(item);
          } catch (IOException e) {

          }
        });

        jsonGenerator.writeEndArray();
        jsonGenerator.flush();
      }
    }

    return Response.ok().entity(streamingOutput).build();
  }
}

```
