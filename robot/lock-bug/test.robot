
*** Settings ***
Suite Setup      Initialize Run Dir    ${RUN_DIR}

Library    Process
Library    OperatingSystem
Resource    ../common.robot

*** Variables ***
${RUN_DIR}    ${CURDIR}${/}run

*** Test Cases ***

Lock File Bug

    Run Process    rover  --no-web  retrieve  I?_T*_00_BH1  2018-01-01T00:00:00  2018-01-01T01:00:00  cwd=${RUN_DIR}  stderr=retrieve-error-1.txt

    Normalize Error File    ${RUN_DIR}${/}retrieve-error-1.txt    100

    ${run} =    Get File    ${RUN_DIR}${/}retrieve-error-1.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}retrieve-error-1.txt
    Should Be Equal    ${run}  ${target}

    Run Process    rover  --no-web  list-index  net\=*  join-qsr  cwd=${RUN_DIR}  stdout=list-index-1.txt
    ${run} =    Get File    ${RUN_DIR}${/}list-index-1.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-index-1.txt
    Should Be Equal    ${run}  ${target}


    Run Process    rover  --no-web  retrieve  IU_T*_00_BH1  2018-01-01T00:00:00  2018-01-01T01:00:00  cwd=${RUN_DIR}  stderr=retrieve-error-2.txt

    Normalize Error File    ${RUN_DIR}${/}retrieve-error-2.txt    100

    ${run} =    Get File    ${RUN_DIR}${/}retrieve-error-2.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}retrieve-error-2.txt
    Should Be Equal    ${run}  ${target}

    Run Process    rover  --no-web  list-index  net\=*  join-qsr  cwd=${RUN_DIR}  stdout=list-index-2.txt
    ${run} =    Get File    ${RUN_DIR}${/}list-index-2.txt
    ${target} =    Get File    ${CURDIR}${/}target${/}list-index-2.txt
    Should Be Equal    ${run}  ${target}

