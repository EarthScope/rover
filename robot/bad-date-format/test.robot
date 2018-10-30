
*** Settings ***

Library    Process
Library    OperatingSystem


*** Test Cases ***

Bad Date Format Command Line

    Remove Directory    ${CURDIR}${/}run  recursive=True
    Create Directory    ${CURDIR}${/}run

    Run Process    rover  -f  ../rover.config  retrieve  TA_MSTX__BH?  2012-02-01  2012-02-2  cwd=${CURDIR}${/}run  stderr=retrieve-error-1.txt
    Run Process    sed  -i.bak  -E  -e  s/task on [-._a-zA-Z0-9]+/task on HOST/g  ${CURDIR}${/}run${/}retrieve-error-1.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/[0-9-]+T[0-9:]+/DATE/g  ${CURDIR}${/}run${/}retrieve-error-1.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/completed in [0-9\.]+ [a-zA-Z]+$/completed in DURATION/g  ${CURDIR}${/}run${/}retrieve-error-1.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/version:? *[0-9.]+[a-z]*/VERSION/g  ${CURDIR}${/}run${/}retrieve-error-1.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  '14,$d'  ${CURDIR}${/}run${/}retrieve-error-1.txt  shell=True
    ${run} =    Get File    ${CURDIR}${/}run${/}retrieve-error-1.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}retrieve-error-1.txt
    Should Be Equal    ${run}  ${target}

Bad Date Format File

    Run Process    rover  -f  ../rover.config  retrieve  ../TA_MSTX_BH_Feb2012.req  cwd=${CURDIR}${/}run  stderr=retrieve-error-2.txt
    Run Process    sed  -i.bak  -E  -e  s/[0-9-]+T[0-9:]+/DATE/g  ${CURDIR}${/}run${/}retrieve-error-2.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/version:? *[0-9.]+[a-z]*/VERSION/g  ${CURDIR}${/}run${/}retrieve-error-2.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  s/completed in [0-9\.]+ [a-zA-Z]+$/completed in DURATION/g  ${CURDIR}${/}run${/}retrieve-error-2.txt  shell=True
    Run Process    sed  -i.bak  -E  -e  '12,$d'  ${CURDIR}${/}run${/}retrieve-error-2.txt  shell=True
    ${run} =    Get File    ${CURDIR}${/}run${/}retrieve-error-2.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}retrieve-error-2.txt
    Should Be Equal    ${run}  ${target}
