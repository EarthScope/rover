
*** Settings ***
Suite Setup      Initialize Run Dir    ${RUN_DIR}

Library    Process
Library    OperatingSystem
Resource    ../common.robot

*** Variables ***
${RUN_DIR}    ${CURDIR}${/}run

*** Test Cases ***

Single Day

    Run Process    rover  --no-web  retrieve  IU_ANMO_*_*  2016-01-01  2016-01-01T23:59:59.999999  cwd=${RUN_DIR}
    Run Process    rover  --no-web  list-index  *_*_*_*  join-qsr  cwd=${RUN_DIR}  stdout=list-index.txt
    ${run} =    Get File    ${RUN_DIR}${/}list-index.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-index.txt
    Should Be Equal    ${run}  ${target}

    Run Process    rover  list-retrieve  net\=IU  sta\=ANMO  2016-01-01  2016-01-01T23:59:59.999999  cwd=${RUN_DIR}  stdout=list-retrieve.txt
    ${run} =    Get File    ${RUN_DIR}${/}list-retrieve.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-retrieve.txt
    Should Be Equal    ${run}  ${target}
    ${result} =    Run Process    rover  --no-web  retrieve  net\=IU  sta\=ANMO  2016-01-01  2016-01-01T23:59:59.999999  cwd=${RUN_DIR}
    Should Match Regexp    ${result.stderr}  A total of 0 downloads were made, with 0 errors

    ${nfiles} =    Count Files In Directory    ${RUN_DIR}${/}data${/}IU${/}2016${/}001
    Should Be Equal As Integers    ${nfiles}  1
    File Should Exist    ${RUN_DIR}${/}data${/}IU${/}2016${/}001${/}ANMO.IU.2016.001
    ${ndirectories} =    Count Directories In Directory    ${RUN_DIR}${/}data${/}IU${/}2016
    Should Be Equal As Integers    ${ndirectories}  1
    Directory Should Exist    ${RUN_DIR}${/}data${/}IU${/}2016${/}001
