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

After generating matrix(X), we can define the output(y) for each sample(row) then we can predict output from input data. Input data should have same number of features in training data.


### Training data
```python
import pandas as pd
simple_train = ['hello', 'hi', 'good morning', 'good afternoon', 'it is raining', 'I am playing baseball', 'watching tv']
greeting_train = ['yes', 'yes', 'yes', 'yes', 'no', 'no', 'no']
greeting_df = pd.DataFrame({
    'text': simple_train,
    'greeting': greeting_train,
});

greeting_df['label_greeting'] = greeting_df.greeting.map({'no':0, 'yes':1})
greeting_df.head()
```

### Splitting data
```python
X = greeting_df.text
y = greeting_df.label_greeting

# split X and y into training and testing sets
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=1)
print(X_train.shape)
print(X_test.shape)
print(y_train.shape)
print(y_test.shape)
```

### Training model
```python
from sklearn.feature_extraction.text import CountVectorizer
vect = CountVectorizer()

X_train_dtm = vect.fit_transform(X_train)
X_train_dtm

# import and instantiate a Multinomial Naive Bayes model
from sklearn.naive_bayes import MultinomialNB
nb = MultinomialNB()

# train the model using X_train_dtm (timing it with an IPython "magic command")
nb.fit(X_train_dtm, y_train)
```

### Model testing
```python
# make class predictions for X_test_dtm
y_pred_class = nb.predict(X_test_dtm)
# calculate accuracy of class predictions
from sklearn import metrics
metrics.accuracy_score(y_test, y_pred_class)
```

### Predict
```python
test = ['sing']
test_xtm = vect.transform(test)
test_pred = nb.predict(test_xtm)
test_pred
```
[Github jupyter notebook](https://github.com/nsclass/jupyter-pyspark-notebook/blob/main/data/sklearn-test.ipynb)

[SK learn - Youtube link](https://www.youtube.com/watch?v=ZiKMIuYidY0)
