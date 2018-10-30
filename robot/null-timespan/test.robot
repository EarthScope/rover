
*** Settings ***

Library    Process
Library    OperatingSystem


*** Test Cases ***

Null Timespan

    Remove Directory    ${CURDIR}${/}run  recursive=True
    Create Directory    ${CURDIR}${/}run

    Run Process    rover  -f  ../rover.config  --dev  retrieve  ../retrieve  cwd=${CURDIR}${/}run  stderr=retrieve-1.txt

    Run Process    sed  -i.bak  -E  -e  s/task on [-._a-zA-Z0-9]+/task on HOST/g  ${CURDIR}${/}run${/}retrieve-1.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/[0-9-]+T[0-9:]+/DATE/g  ${CURDIR}${/}run${/}retrieve-1.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/completed in [0-9\.]+ [a-zA-Z]+$/completed in DURATION/g  ${CURDIR}${/}run${/}retrieve-1.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/version:? *[0-9.]+[a-z]*/VERSION/g  ${CURDIR}${/}run${/}retrieve-1.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  '14,$d'  ${CURDIR}${/}run${/}retrieve-1.txt  shell=True

    ${run} =    Get File    ${CURDIR}${/}run${/}retrieve-1.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}retrieve-1.txt
    Should Be Equal    ${run}  ${target}

    Run Process    rover  -f  ../rover.config  list-index  *_*_*_*  join-qsr  cwd=${CURDIR}${/}run  stdout=list-index.txt
    ${run} =    Get File    ${CURDIR}${/}run${/}list-index.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-index.txt
    Should Be Equal    ${run}  ${target}

    Run Process    rover  -f  ../rover.config  --dev  retrieve  ../retrieve  cwd=${CURDIR}${/}run  stderr=retrieve-2.txt

    Run Process    sed  -i.bak  -E  -e  s/task on [-._a-zA-Z0-9]+/task on HOST/g  ${CURDIR}${/}run${/}retrieve-2.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/[0-9-]+T[0-9:]+/DATE/g  ${CURDIR}${/}run${/}retrieve-2.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/completed in [0-9\.]+ [a-zA-Z]+$/completed in DURATION/g  ${CURDIR}${/}run${/}retrieve-2.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/version:? *[0-9.]+[a-z]*/VERSION/g  ${CURDIR}${/}run${/}retrieve-2.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  '14,$d'  ${CURDIR}${/}run${/}retrieve-2.txt  shell=True

    ${run} =    Get File    ${CURDIR}${/}run${/}retrieve-2.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}retrieve-2.txt
    Should Be Equal    ${run}  ${target}

    Run Process    rover  -f  ../rover.config  list-index  *_*_*_*  join-qsr  cwd=${CURDIR}${/}run  stdout=list-index.txt
    ${run} =    Get File    ${CURDIR}${/}run${/}list-index.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-index.txt
    Should Be Equal    ${run}  ${target}
