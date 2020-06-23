---
layout: single
title: Python - Running IO tasks in parallel
date: 2020-06-23 09:30:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - Python
permalink: "2020/06/23/python-run-io-tasks-in-parallel"
---

Python(3.2 later version) has a feature to run IO tasks in parallel by using futures and ThreadPoolExecutor.

The below code will show an example for sending multiple HTTP requests.

```Python
import http.client
import ssl
import json
from concurrent.futures import ThreadPoolExecutor

def connect_https_server(host_name, port_number):
    host_end_point_address = host_name + ":" + str(port_number)
    return http.client.HTTPSConnection(host_end_point_address, timeout=30, context=ssl._create_unverified_context())


def send_http_query(host_name, port_number):
    conn = connect_https_server(host_name, port_number)
    query = f"/version"
    conn.request("GET", query)
    res = conn.getresponse()
    data = res.read()
    conn.close()

    output = data.decode('utf-8')
    return output


def run_queries_in_parallel(tasks):
    with ThreadPoolExecutor() as executor:
        result = []
        running_tasks = [executor.submit(task) for task in tasks]
        for running_task in running_tasks:
            res = running_task.result()
            result.append(result)

        return result


def make_task(host_name, port_number):
    return lambda: send_http_query(host_name, port_number)


def parallel_tasks_demo():
    host_names = ["test1", "test2", "test3"]
    task_list = []
    for host_name in host_names:
        task_list.append(make_task(host_name, 8080))

    run_queries_in_parallel(task_list, output_path)
```
