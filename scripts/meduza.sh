#!/bin/bash
export PYTHONPATH="$PYTHONPATH:$(pwd)"
cd wbm_newspapers/waybackmachine
scrapy crawl spider_meduza -a settings_file=../../settings/meduza.yaml