
*** Settings ***

Library    Process
Library    OperatingSystem

Test Setup    Set Environment Variable    PYTHONPATH  ../../../../rover

*** Test Cases ***

Single Day

    Remove Directory    ${CURDIR}${/}run  resursive=True
    Create Directory    ${CURDIR}${/}run
    Run Process    python  -m  rover  -f  ../roverrc  retrieve  IU.ANMO.*.*  2016-01-01  2016-01-02  cwd=${CURDIR}${/}run
    Run Process    python  -m  rover  -f  ../roverrc  list-index  net\=*  join-qsr  cwd=${CURDIR}${/}run  stdout=list-index.txt
    ${run} =    Get File    ${CURDIR}${/}run${/}list-index.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-index.txt
    Should Be Equal    ${run}  ${target}
    Run Process    python  -m  rover  -f  ../roverrc  compare  IU.ANMO.*.*  2016-01-01  2016-01-02  cwd=${CURDIR}${/}run  stdout=compare.txt
    ${run} =    Get File    ${CURDIR}${/}run${/}compare.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}compare.txt
    Should Be Equal    ${run}  ${target}
