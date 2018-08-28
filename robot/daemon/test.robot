
*** Settings ***

Library    Process
Library    OperatingSystem


*** Test Cases ***

Daemon

    Remove Directory    ${CURDIR}${/}run  recursive=True
    Create Directory    ${CURDIR}${/}run

    ${result} =  Run Process    rover  -f  ../rover.config  subscribe  ../request.1  cwd=${CURDIR}${/}run
    Log  ${result.stderr}
    Run Process    rover  -f  ../rover.config  subscribe  ../request.2  cwd=${CURDIR}${/}run
    ${result} =  Run Process    rover  -f  ../rover.config  list-subscribe  1:3  --verbosity  5  stdout=list-subscribe-13.txt  cwd=${CURDIR}${/}run
    Log  ${result.stderr}
    ${run} =    Get File    ${CURDIR}${/}run${/}list-subscribe-13.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-subscribe-13.txt
    Should Be Equal    ${run}  ${target}

    ${result} =  Run Process    rover  -f  ../rover.config  subscribe  ../request.3  cwd=${CURDIR}${/}run
    Log  ${result.stderr}
    Run Process    rover  -f  ../rover.config  list-subscribe  1:3  stdout=list-subscribe-13.txt  cwd=${CURDIR}${/}run
    ${run} =    Get File    ${CURDIR}${/}run${/}list-subscribe-13.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-subscribe-13.txt
    Should Be Equal    ${run}  ${target}

    Comment  I can't get start and stop to work inside robot...
    ${result} =  Run Process    rover  -f  ../rover.config  daemon  cwd=${CURDIR}${/}run  timeout=30 seconds
    Log  ${result.stderr}

    Run Process    rover  -f  ../rover.config  list-summary  stdout=list-summary.txt  cwd=${CURDIR}${/}run
    ${run} =    Get File    ${CURDIR}${/}run${/}list-summary.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-summary.txt
    Should Be Equal    ${run}  ${target}

