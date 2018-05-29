
*** Settings ***

Library    Process
Library    OperatingSystem


*** Test Cases ***

Single Day

    Remove Directory    ${CURDIR}${/}run  resursive=True
    Create Directory    ${CURDIR}${/}run

    Run Process    rover  -f  ../roverrc  subscribe  ../request.1  cwd=${CURDIR}${/}run
    Run Process    rover  -f  ../roverrc  subscribe  ../request.2  cwd=${CURDIR}${/}run
    Run Process    rover  -f  ../roverrc  list-subscribe  1:2  cwd=${CURDIR}${/}run  stdout=list-subscribe-12.txt
    ${run} =    Get File    ${CURDIR}${/}run${/}list-subscribe-12.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-subscrive-12.txt
    Should Be Equal    ${run}  ${target}

    Run Process    rover  -f  ../roverrc  subscribe  ../request.3  cwd=${CURDIR}${/}run
    Run Process    rover  -f  ../roverrc  list-subscribe  1:2  cwd=${CURDIR}${/}run  stdout=list-subscribe-12.txt
    ${run} =    Get File    ${CURDIR}${/}run${/}list-subscribe-12.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-subscrive-12.txt
    Should Be Equal    ${run}  ${target}

    Run Process    rover  -f  ../roverrc  start
    Sleep  2 minutes  Wait for daemon to run
    Run Process    rover  -f  ../roverrc  stop

    Run Process    rover  -f  ../roverrc  list-summary  cwd=${CURDIR}${/}run  stdout=list-summary.txt
    ${run} =    Get File    ${CURDIR}${/}run${/}list-summary.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-summary.txt
    Should Be Equal    ${run}  ${target}

