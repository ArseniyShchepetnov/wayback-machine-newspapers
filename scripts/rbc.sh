#!/bin/bash
export PYTHONPATH="$PYTHONPATH:$(pwd)"
cd wbm_newspapers/waybackmachine
scrapy crawl spider_rbc -a settings_file=../../settings/rbc.yaml