#!/bin/sh
for f in `find . -name 'export.sh'`; do
    (cd `dirname $f` && ./`basename $f`)
done


