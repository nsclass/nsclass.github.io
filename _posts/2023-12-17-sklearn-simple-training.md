---
layout: single
title: Scikit-learn simple training example
date: 2023-12-17 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - ai
permalink: "2023/12/17/sk-learn-simple-training"
---

Main point of training data is to generate matrix(X) having features(columns) and samples(rows) from provided data which can be text or any form of data.

After generating matrix(X), we can define the output(y) for each sample(row) then we can predict output from input data. Input data should have a same number of features in training data.


### Training data
```python
simple_train = ['hello', 'hi', 'good morning', 'good afternoon', 'it is raining', 'I am playing baseball', 'watching tv']
```

### Training model
```python
from sklearn.feature_extraction.text import CountVectorizer
vect = CountVectorizer()

vect.fit(simple_train)
```

### Transform to vectorize data
```python
simple_train_dtm = vect.transform(simple_train)
```
#### Note
we can do train and transform in a single function.
```python
simple_train_dtm vect.fit_transform(simple_train)
```

### Model testing by transforming to vector data
```python
simple_test = ["hi there"]
simple_test_dtm = vect.transform(simple_test)
```

[SK learn - You tube link](https://www.youtube.com/watch?v=ZiKMIuYidY0)
