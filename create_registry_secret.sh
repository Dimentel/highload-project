#!/bin/bash

kubectl create secret docker-registry registrysecret \
  --docker-server=registry.gitlab.akhcheck.ru \
  --docker-username=dmitrii.boldyrev \
  --docker-password=your_token \
  --docker-email=daboldyrev@edu.hse.ru \
  -n hl-project
