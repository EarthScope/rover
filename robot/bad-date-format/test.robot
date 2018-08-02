
*** Settings ***

Library    Process
Library    OperatingSystem


*** Test Cases ***

Bad Date Format Command Line

    Remove Directory    ${CURDIR}${/}run  resursive=True
    Create Directory    ${CURDIR}${/}run

    Run Process    rover  -f  ../rover.config  retrieve  TA_MSTX__BH?  2012-02-01  2012-02-2  cwd=${CURDIR}${/}run  stderr=retrieve-error-1.txt
    Run Process    sed  -i  -e  's/[0-9\\-]\\+T[0-9:]\\+/DATE/g'  retrieve-error-1.txt  cwd=${CURDIR}${/}run  shell=True
    ${run} =    Get File    ${CURDIR}${/}run${/}retrieve-error-1.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}retrieve-error-1.txt
    Should Be Equal    ${run}  ${target}

Bad Date Format File

    Run Process    rover  -f  ../rover.config  retrieve  ../TA_MSTX_BH_Feb2012.req  cwd=${CURDIR}${/}run  stderr=retrieve-error-2.txt
    Run Process    sed  -i  -e  s/[0-9/]\\+ [0-9:]\\+/DATE/g  retrieve-error-2.txt  cwd=${CURDIR}${/}run  shell=True
    ${run} =    Get File    ${CURDIR}${/}run${/}retrieve-error-2.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}retrieve-error-2.txt
    Should Be Equal    ${run}  ${target}
