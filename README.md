# Purestorage Prometheus exporter

## Description

This utility collects various metrics from different Purestorage arrays specified in a certain syntax inside an inventory.yaml file
Metrics include:
- open events
- array temperature
- array power
- hw component availability
- array performance stats
- array space consumption
- volumes performance stats
- volumes space consumption

## How to use

The package includes a "purestoragefa_exporter.service" example file for systemd and an example "pure-inventory.yaml" file.

purexporter -u pureuser -p 8085 -f pure-inventory.yaml

It has been tested collecting from 10 arrays each with aprox 5-6 volumes, probably something with multiprocessing can be done to speed up the collection of metrics.
The actual exporter will not execute if it is already running so even with short interval you should allow enough time to exporter to complete.
