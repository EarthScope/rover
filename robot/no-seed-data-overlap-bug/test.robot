
*** Settings ***

Library    Process
Library    OperatingSystem


*** Test Cases ***

No SEED Data Detected / Overlapped Data

    Remove Directory    ${CURDIR}${/}run  recursive=True
    Create Directory    ${CURDIR}${/}run
    Remove Directory    ${CURDIR}${/}logs  recursive=True

    Run Process    rover  -f  ../rover.config  retrieve  TA_MSTX_--_BH?  2012-02-02T23:00:00  2012-02-03T00:00:00  cwd=${CURDIR}${/}run  stderr=retrieve-log-1.txt

    Run Process    sed  -i.bak  -E  -e  s/task on [-._a-zA-Z0-9]+/task on HOST/g  ${CURDIR}${/}run${/}retrieve-log-1.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/[0-9-]+T[0-9:]+/DATE/g  ${CURDIR}${/}run${/}retrieve-log-1.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/completed in [0-9\.]+ [a-zA-Z]+$/completed in DURATION/g  ${CURDIR}${/}run${/}retrieve-log-1.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/version:? *[0-9.]+[a-z]*/VERSION/g  ${CURDIR}${/}run${/}retrieve-log-1.txt  shell=True
    ${run} =    Get File    ${CURDIR}${/}run${/}retrieve-log-1.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}retrieve-log-1.txt
    Should Be Equal    ${run}  ${target}

    Run Process    rover  -f  ../rover.config  list-index  net\=*  join-qsr  cwd=${CURDIR}${/}run  stdout=list-index-1.txt
    ${run} =    Get File    ${CURDIR}${/}run${/}list-index-1.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-index-1.txt
    Should Be Equal    ${run}  ${target}

    Run Process    msi  -tg  data/TA/2012/03*/*  cwd=${CURDIR}${/}run  stdout=msi-1.txt  shell=True
    ${run} =    Get File    ${CURDIR}${/}run${/}msi-1.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}msi-1.txt
    Should Be Equal    ${run}  ${target}

    Run Process    rover  -f  ../rover.config  retrieve  TA_MSTX_--_BH?  2012-02-02T23:00:00  2012-02-04T00:00:00  cwd=${CURDIR}${/}run  stderr=retrieve-log-2.txt

    Run Process    sed  -i.bak  -E  -e  s/task on [-._a-zA-Z0-9]+/task on HOST/g  ${CURDIR}${/}run${/}retrieve-log-2.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/[0-9-]+T[0-9:]+/DATE/g  ${CURDIR}${/}run${/}retrieve-log-2.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/completed in [0-9\.]+ [a-zA-Z]+$/completed in DURATION/g  ${CURDIR}${/}run${/}retrieve-log-2.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/version:? *[0-9.]+[a-z]*/VERSION/g  ${CURDIR}${/}run${/}retrieve-log-2.txt  shell=True
    ${run} =    Get File    ${CURDIR}${/}run${/}retrieve-log-2.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}retrieve-log-2.txt
    Should Be Equal    ${run}  ${target}

    Run Process    rover  -f  ../rover.config  list-index  net\=*  join-qsr  cwd=${CURDIR}${/}run  stdout=list-index-2.txt
    ${run} =    Get File    ${CURDIR}${/}run${/}list-index-2.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-index-2.txt
    Should Be Equal    ${run}  ${target}

    Run Process    msi  -tg  data/TA/2012/03*/*  cwd=${CURDIR}${/}run  stdout=msi-2.txt  shell=True
    ${run} =    Get File    ${CURDIR}${/}run${/}msi-2.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}msi-2.txt
    Should Be Equal    ${run}  ${target}

