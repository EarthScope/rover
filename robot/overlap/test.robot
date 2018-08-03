
*** Settings ***

Library    Process
Library    OperatingSystem


*** Test Cases ***

Overlapping Subscription

    Remove Directory    ${CURDIR}${/}run  resursive=True
    Create Directory    ${CURDIR}${/}run

    Run Process    rover  -f  ../rover.config  subscribe  ../TA_MSTX_BH_Feb2012.req  cwd=${CURDIR}${/}run  stderr=subscribe-error-1.txt
    Run Process    rover  -f  ../rover.config  subscribe  ../TA_MSTX_BH_Feb2012.req  cwd=${CURDIR}${/}run  stderr=subscribe-error-2.txt
    Run Process    sed  -i  -e  's/_[0-9a-f]\\{6\\}_[0-9]\\+/_HASH/g'  subscribe-error-2.txt  cwd=${CURDIR}${/}run  shell=True
    ${run} =    Get File    ${CURDIR}${/}run${/}subscribe-error-1.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}subscribe-error-1.txt
    Should Be Equal    ${run}  ${target}
    ${run} =    Get File    ${CURDIR}${/}run${/}subscribe-error-2.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}subscribe-error-2.txt
    Should Be Equal    ${run}  ${target}

