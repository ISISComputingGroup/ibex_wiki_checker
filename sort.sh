#!/bin/bash
sort words.txt | tr '[:upper:]' '[:lower:]' > sorted.txt
mv sorted.txt words.txt