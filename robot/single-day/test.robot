
*** Settings ***

Library    Process
Library    OperatingSystem


*** Test Cases ***

Single Day

    Remove Directory    ${CURDIR}${/}run  recursive=True
    Create Directory    ${CURDIR}${/}run

    Run Process    rover  -f  ../rover.config  retrieve  IU_ANMO_*_*  2016-01-01  2016-01-02  cwd=${CURDIR}${/}run
    Run Process    rover  -f  ../rover.config  list-index  *_*_*_*  join-qsr  cwd=${CURDIR}${/}run  stdout=list-index.txt
    ${run} =    Get File    ${CURDIR}${/}run${/}list-index.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-index.txt
    Should Be Equal    ${run}  ${target}

    Run Process    rover  -f  ../rover.config  list-retrieve  net\=IU  sta\=ANMO  2016-01-01  2016-01-02  cwd=${CURDIR}${/}run  stdout=list-retrieve.txt
    ${run} =    Get File    ${CURDIR}${/}run${/}list-retrieve.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-retrieve.txt
    Should Be Equal    ${run}  ${target}
    ${result} =    Run Process    rover  -f  ../rover.config  retrieve  net\=IU  sta\=ANMO  2016-01-01  2016-01-02  cwd=${CURDIR}${/}run
    Should Match Regexp    ${result.stderr}  A total of 0 downloads were made, with 0 errors

    ${nfiles} =    Count Files In Directory    ${CURDIR}${/}run${/}data${/}IU${/}2016${/}001
    Should Be Equal As Integers    ${nfiles}  1
    File Should Exist    ${CURDIR}${/}run${/}data${/}IU${/}2016${/}001${/}ANMO.IU.2016.001
    ${ndirectories} =    Count Directories In Directory    ${CURDIR}${/}run${/}data${/}IU${/}2016
    Should Be Equal As Integers    ${ndirectories}  2
    Directory Should Exist    ${CURDIR}${/}run${/}data${/}IU${/}2016${/}001

*** Comment ***


