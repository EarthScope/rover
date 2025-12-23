
*** Settings ***
Suite Setup      Initialize Run Dir    ${RUN_DIR}

Library    Process
Library    OperatingSystem
Resource    ../common.robot

*** Variables ***
${RUN_DIR}    ${CURDIR}${/}run

*** Test Cases ***

Cross Day

    Run Process    rover  --no-web  retrieve  IU_ANMO_3?_*  2016-01-01T20:00:00  2016-01-02T04:00:00  cwd=${RUN_DIR}
    Run Process    rover  list-index  net\=*  join-qsr  cwd=${RUN_DIR}  stdout=list-index.txt
    ${run} =    Get File    ${CURDIR}${/}run${/}list-index.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-index.txt
    Should Be Equal    ${run}  ${target}

    Run Process    rover  list-retrieve  net\=IU  sta\=ANMO  loc\=3?  2016-01-01T20:00:00  2016-01-02T04:00:00  cwd=${RUN_DIR}  stdout=list-retrieve.txt
    ${run} =    Get File    ${CURDIR}${/}run${/}list-retrieve.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-retrieve.txt
    Should Be Equal    ${run}  ${target}
    ${result} =    Run Process    rover  --no-web  retrieve  net\=IU  sta\=ANMO  loc\=3?  2016-01-01T20:00:00  2016-01-02T04:00:00  cwd=${RUN_DIR}
    Should Match Regexp    ${result.stderr}  A total of 0 downloads were made

    ${nfiles} =    Count Files In Directory    ${CURDIR}${/}run${/}data${/}IU${/}2016${/}001
    Should Be Equal As Integers    ${nfiles}  1
    File Should Exist    ${CURDIR}${/}run${/}data${/}IU${/}2016${/}001${/}ANMO.IU.2016.001
    ${nfiles} =    Count Files In Directory    ${CURDIR}${/}run${/}data${/}IU${/}2016${/}002
    Should Be Equal As Integers   ${nfiles}  1
    File Should Exist    ${CURDIR}${/}run${/}data${/}IU${/}2016${/}002${/}ANMO.IU.2016.002
    ${ndirectories} =    Count Directories In Directory    ${CURDIR}${/}run${/}data${/}IU${/}2016
    Should Be Equal As Integers   ${ndirectories}  2

