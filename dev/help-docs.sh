#!/bin/bash

source env3/bin/activate

#python -c 'from rover.args import Arguments; Arguments().print_docs_text()'
python -c 'from rover.args import Arguments; Arguments().print_docs_table()'
