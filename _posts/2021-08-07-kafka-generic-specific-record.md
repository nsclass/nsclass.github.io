---
layout: single
title: Kafka - GenericRecord vs SpecificRecord
date: 2021-08-07 11:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - kafka
permalink: "2021/08/07/kafka-generic-specific-record"
---

Kafka has two types of record on producing and consuming Kafka messages which are called GenericRecord and SpecificRecord.
Main difference between GenericRecord and SpecificRecord is that SpecificRecord type can use the Java type information after generating Java classes from Schema definition.

## Producer

Producer does not have many difference between two types in terms of sending a message.

### GenericRecord

```java
//avro schema
String simpleMessageSchema =
        "{" +
        " \"type\": \"record\"," +
        " \"name\": \"SimpleMessage\"," +
        " \"namespace\": \"com.codingharbour.avro\"," +
        " \"fields\": [" +
        " {\"name\": \"content\", \"type\": \"string\", \"doc\": \"Message content\"}," +
        " {\"name\": \"date_time\", \"type\": \"string\", \"doc\": \"Datetime when the message\"}" +
        " ]" +
        "}";

//parse the schema
Schema.Parser parser = new Schema.Parser();
Schema schema = parser.parse(simpleMessageSchema);

//prepare the avro record
GenericRecord avroRecord = new GenericData.Record(schema);
avroRecord.put("content", "Hello world");
avroRecord.put("date_time", Instant.now().toString());

//prepare the kafka record
ProducerRecord<String, GenericRecord> record = new ProducerRecord<>("avro-topic", null, avroRecord);

producer.send(record);
producer.flush();
producer.close();
```

### SpecificRecord

```java
SimpleMessage simpleMessage = new SimpleMessage();
simpleMessage.setContent("Hello world");
simpleMessage.setDateTime(Instant.now().toString());
ProducerRecord<String, SpecificRecord> record = new ProducerRecord<>("avro-topic", null, simpleMessage);
producer.send(record);
producer.flush();
producer.close();

```

## Consumer

Consumer needs some extra configuration to use SpecificRecord.

### GenericRecord

```java
Properties properties = new Properties();
properties.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
properties.put(ConsumerConfig.GROUP_ID_CONFIG, "generic-record-consumer-group");
properties.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
properties.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, false);

properties.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
properties.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, KafkaAvroDeserializer.class);

properties.put(KafkaAvroDeserializerConfig.SCHEMA_REGISTRY_URL_CONFIG, "http://localhost:8081");

KafkaConsumer<String, GenericRecord> consumer = new KafkaConsumer<>(properties);


consumer.subscribe(Collections.singleton("avro-topic"));

//poll the record from the topic
while (true) {
    ConsumerRecords<String, GenericRecord> records = consumer.poll(Duration.ofMillis(100));

    for (ConsumerRecord<String, GenericRecord> record : records) {
        System.out.println("Message content: " + record.value().get("content"));
        System.out.println("Message time: " + record.value().get("date_time"));
    }
    consumer.commitAsync();
}

```

### SpecificRecord

Consumer needs to make sure that `KafkaAvroDeserializerConfig.SPECIFIC_AVRO_READER_CONFIG` is true.

```java
Properties properties = new Properties();
properties.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
properties.put(ConsumerConfig.GROUP_ID_CONFIG, "specific-record-consumer-group");
properties.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
properties.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, false);

properties.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
properties.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, KafkaAvroDeserializer.class);

properties.put(KafkaAvroDeserializerConfig.SCHEMA_REGISTRY_URL_CONFIG, "http://localhost:8081");
properties.put(KafkaAvroDeserializerConfig.SPECIFIC_AVRO_READER_CONFIG, true); //ensures records are properly converted

KafkaConsumer<String, SimpleMessage> consumer = new KafkaConsumer<>(properties);
consumer.subscribe(Collections.singleton("avro-topic"));

//poll the record from the topic
while (true) {
    ConsumerRecords<String, SimpleMessage> records = consumer.poll(Duration.ofMillis(100));

    for (ConsumerRecord<String, SimpleMessage> record : records) {
        System.out.println("Message content: " + record.value().getContent()); //1
        System.out.println("Message time: " + record.value().getDateTime()); //2
    }
    consumer.commitAsync();
}

```

Kafka resources
[https://codingharbour.com/blog/](https://codingharbour.com/blog/)
