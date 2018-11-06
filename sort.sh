#!/bin/bash
tr '[:upper:]' '[:lower:]' < words.txt > words-lower.txt 
sort words-lower.txt > words-sorted.txt | mv words-sorted.txt words.txt
rm words-lower.txt 